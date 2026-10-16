"""Input and output helpers of the command line: reading local and remote specs, printing."""

from __future__ import annotations

import os
import sys
import tempfile
from urllib.parse import urlparse

import requests

from restful_checker.cli_remote import FetchError, describe, fetch, remote_suffix, safe_url
from restful_checker.engine.openapi_loader import load_openapi


def _print(text: str) -> None:
    # A console or pipe with a legacy code page cannot encode the status emoji; print what
    # it can instead of failing the whole run.
    try:
        try:
            print(text)
        except UnicodeEncodeError:
            encoding = getattr(sys.stdout, "encoding", None) or "ascii"
            print(text.encode(encoding, "replace").decode(encoding))
    except (OSError, AttributeError):  # stdout closed, broken or missing: nothing to tell
        pass


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
        data = load_openapi(path)
        return isinstance(data, dict) and ("openapi" in data or "swagger" in data)
    except Exception as e:
        print_error(f"Error parsing OpenAPI file: {e}")
        return False


def is_remote(path: str) -> bool:
    """Tell whether the path given on the command line is an http or https URL."""
    return urlparse(path).scheme in ("http", "https")


def resolve_openapi_path(path: str) -> str:
    """
    Resolve a given path to a valid local file.
    If the path is a URL, downloads the content to a temporary file (at most 50 MB within
    60 seconds; messages name the URL without credentials or query).

    Args:
        path (str): URL or local path to the OpenAPI definition.

    Returns:
        str: Path to the resolved local file (original or temporary).
    """
    parsed = urlparse(path)
    if is_remote(path):
        try:
            body = fetch(path)
        except (requests.RequestException, FetchError) as e:
            print_error(f"Failed to fetch {safe_url(path)}: {describe(e)}")
            sys.exit(1)

        suffix = remote_suffix(parsed.path, body)
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
