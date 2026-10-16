"""Fetch a remote OpenAPI document for the command line: bounded in time and size."""

from __future__ import annotations

import json
import re
import threading
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

MAX_BYTES = 50 * 2**20  # decoded bytes: a compressed body cannot expand past this
DEADLINE = 60.0  # seconds for the whole download, however slowly the bytes arrive


class FetchError(Exception):
    """A remote document that could not be fetched within the limits."""


def safe_url(url: str) -> str:
    """The URL without user, password, query or fragment, fit for a message.

    >>> safe_url("https://alice:secret@api.example.com:8443/spec.yaml?api_key=k#x")
    'https://api.example.com:8443/spec.yaml'
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if parts.port is not None:
            host = f"{host}:{parts.port}"
    except ValueError:  # a malformed port or bracket
        return "<the given URL>"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def _download(url: str, box: dict[str, Any]) -> None:
    try:
        box["response"] = response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise FetchError(f"the document is larger than {MAX_BYTES // 2**20} MB")
            chunks.append(chunk)
        box["body"] = utf8_body(b"".join(chunks), response.headers)
    except BaseException as error:  # handed to the caller's thread
        box["error"] = error


def fetch(url: str) -> bytes:
    """Download a document as UTF-8 bytes; raise FetchError or requests' errors.

    The whole download runs in a daemon worker thread so that a server sending one byte at a
    time cannot hold the command past the deadline.
    """
    box: dict[str, Any] = {}
    worker = threading.Thread(target=_download, args=(url, box), daemon=True)
    worker.start()
    worker.join(DEADLINE)
    if worker.is_alive():
        # Closing would wait for the worker's blocked read; the daemon thread is left to
        # end with the command, which exits on this error.
        raise FetchError(f"the download took longer than {DEADLINE:.0f} s")
    if box.get("response") is not None:
        box["response"].close()
    if "error" in box:
        raise box["error"]
    body: bytes = box["body"]
    return body


def utf8_body(body: bytes, headers: Any) -> bytes:
    """Keep UTF-8 bytes as sent; re-encode only a declared other charset.

    ``response.text`` would decode text/* without a charset as ISO-8859-1, which garbles
    UTF-8 descriptions. A charset that is unknown or cannot decode leaves the bytes as sent.
    """
    content_type = headers.get("content-type", "") if headers else ""
    match = re.search(r"charset\s*=\s*\"?([\w.:-]+)", content_type, re.IGNORECASE)
    charset = match.group(1).lower() if match else "utf-8"
    if charset.replace("_", "-") in ("utf-8", "utf8"):
        return body
    try:
        return body.decode(charset, "replace").encode("utf-8")
    except (LookupError, UnicodeError):  # unknown name, or a codec without "replace"
        return body


def remote_suffix(url_path: str, body: bytes) -> str:
    """The suffix the loader needs: from the URL path, else from the content."""
    if url_path.lower().endswith((".yaml", ".yml")):
        return ".yaml"
    if url_path.lower().endswith(".json"):
        return ".json"
    try:
        json.loads(body.decode("utf-8-sig"))
    except RecursionError:
        return ".json"  # JSON nested too deeply: the loader reports it cleanly
    except ValueError:
        return ".yaml"
    return ".json"


def describe(error: Exception) -> str:
    """A short reason for a failed download that never repeats the URL."""
    if isinstance(error, requests.HTTPError) and error.response is not None:
        return f"HTTP {error.response.status_code} {error.response.reason or ''}".strip()
    if isinstance(error, FetchError):
        return str(error)
    return type(error).__name__
