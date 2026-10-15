"""Input and output helpers of the command line: reading local and remote specs, printing."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from urllib.parse import urlparse

import requests
import yaml


def _print(text: str) -> None:
    # A console or pipe with a legacy code page cannot encode the status emoji; print what
    # it can instead of failing the whole run.
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(encoding, "replace").decode(encoding))


def print_error(msg: str) -> None:
    """
    Print a formatted error message to the console.
    """
    _print(f"❌ {msg}")


def is_valid_file(path: str) -> bool:
    """
    Check if a path points to a valid OpenAPI file with .json, .yaml, or .yml extension.

    Args:
        path (str): Path to check.

    Returns:
        bool: True if the path is a valid file with a correct extension.
    """
    return os.path.isfile(path) and path.lower().endswith((".json", ".yaml", ".yml"))


def is_valid_openapi(path: str) -> bool:
    """
    Validate if the file at the given path is a valid OpenAPI or Swagger document.

    Args:
        path (str): Path to the OpenAPI file.

    Returns:
        bool: True if the file contains a valid OpenAPI or Swagger root key.
    """
    try:
        # utf-8-sig: RFC 8259 lets a parser ignore a byte order mark, and editors write one.
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f) if path.lower().endswith(".json") else yaml.safe_load(f)
            return isinstance(data, dict) and ("openapi" in data or "swagger" in data)
    except Exception as e:
        print_error(f"Error parsing OpenAPI file: {e}")
        return False


def _remote_suffix(url_path: str, body: bytes) -> str:
    # The loader picks its parser by suffix. A URL may carry a query string or no extension
    # at all, so look at the URL path first and at the content when it says nothing.
    if url_path.lower().endswith((".yaml", ".yml")):
        return ".yaml"
    if url_path.lower().endswith(".json"):
        return ".json"
    try:
        json.loads(body.decode("utf-8-sig"))
    except ValueError:
        return ".yaml"
    return ".json"


def _utf8_body(response: requests.Response) -> bytes:
    # Keep UTF-8 bytes as sent: `response.text` decodes text/* without a charset as
    # ISO-8859-1, which garbles UTF-8 descriptions. Re-encode only a declared other charset.
    content_type = response.headers.get("content-type", "") if response.headers else ""
    match = re.search(r"charset\s*=\s*\"?([\w.:-]+)", content_type, re.IGNORECASE)
    charset = match.group(1).lower() if match else "utf-8"
    if charset.replace("_", "-") in ("utf-8", "utf8"):
        return response.content
    try:
        return response.content.decode(charset, "replace").encode("utf-8")
    except LookupError:  # an unknown charset name
        return response.content


def is_remote(path: str) -> bool:
    """Tell whether the path given on the command line is an http or https URL."""
    return urlparse(path).scheme in ("http", "https")


def resolve_openapi_path(path: str) -> str:
    """
    Resolve a given path to a valid local file.
    If the path is a URL, downloads the content to a temporary file.

    Args:
        path (str): URL or local path to the OpenAPI definition.

    Returns:
        str: Path to the resolved local file (original or temporary).
    """
    parsed = urlparse(path)
    if is_remote(path):
        try:
            response = requests.get(path, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print_error(f"Failed to fetch URL: {e}")
            sys.exit(1)

        body = _utf8_body(response)
        suffix = _remote_suffix(parsed.path, body)
        with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix=suffix) as tmp:
            tmp.write(body)
        return tmp.name
    elif is_valid_file(path):
        return path
    else:
        print_error(
            f"Invalid file: '{path}'\n👉 Must be a local .json/.yaml/.yml file or a valid URL"
        )
        sys.exit(1)
