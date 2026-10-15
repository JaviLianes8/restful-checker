from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml

from restful_checker import __version__ as __version__
from restful_checker.engine.analyzer import analyze_api

try:
    from restful_checker.tools.help_restful_checker import show_help
except ModuleNotFoundError:
    print("❌ Error: Missing help module at 'restful_checker/tools/help_restful_checker.py'")
    sys.exit(1)


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

        # Keep the bytes as sent: `response.text` decodes text/* without a charset as
        # ISO-8859-1, which garbles UTF-8 descriptions.
        suffix = _remote_suffix(parsed.path, response.content)
        with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix=suffix) as tmp:
            tmp.write(response.content)
        return tmp.name
    elif is_valid_file(path):
        return path
    else:
        print_error(
            f"Invalid file: '{path}'\n👉 Must be a local .json/.yaml/.yml file or a valid URL"
        )
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments using argparse.

    Returns:
        argparse.Namespace: Parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Check RESTful API compliance from OpenAPI definitions and generate reports."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("path", nargs="?", help="Path or URL to OpenAPI file (.json, .yaml, .yml)")
    parser.add_argument(
        "--output-format",
        choices=["html", "json", "both"],
        default="html",
        help="Output format: html, json, or both (default: html)",
    )
    parser.add_argument(
        "--output-folder",
        default="html",
        help="Destination folder for output reports (default: ./html)",
    )
    parser.add_argument(
        "--open", action="store_true", help="Open the generated HTML report in the default browser"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )
    return parser.parse_args()


def run_checker(args: argparse.Namespace) -> int:
    """
    Main execution function that handles file validation, parsing, and analysis.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    if not args.path:
        show_help()
        return 0

    path = resolve_openapi_path(args.path)
    try:
        return _check(args, path)
    finally:
        if is_remote(args.path) and path != args.path:
            try:
                os.remove(path)
            except OSError:
                pass


def _check(args: Any, path: str) -> int:
    if not is_valid_openapi(path):
        print_error(f"The file '{path}' is not a valid OpenAPI document.")
        return 1

    try:
        result = analyze_api(path, output_dir=args.output_folder)
        html_path = os.path.abspath(result["html_path"])

        if args.output_format in ["html", "both"]:
            if not args.quiet:
                _print(f"✅ HTML report generated: {html_path}")
            if args.open:
                webbrowser.open(Path(html_path).resolve().as_uri())

        if args.output_format in ["json", "both"]:
            json_path = os.path.join(args.output_folder, "rest_report.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result["json_report"], f, indent=2, ensure_ascii=False)
            if not args.quiet:
                _print(f"✅ JSON report generated: {os.path.abspath(json_path)}")

        return 0
    except Exception as e:
        print_error(f"Error analyzing API: {e}")
        return 1


def main() -> None:
    """
    CLI entry point. Parses arguments and executes the checker.
    """
    args = parse_arguments()
    sys.exit(run_checker(args))


if __name__ == "__main__":
    main()
