from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile as tempfile  # these four were importable from here in 3.1
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse as urlparse

import requests as requests
import yaml as yaml

from restful_checker import __version__ as __version__
from restful_checker.cli_io import _print
from restful_checker.cli_io import is_remote as is_remote
from restful_checker.cli_io import is_valid_file as is_valid_file
from restful_checker.cli_io import is_valid_openapi as is_valid_openapi
from restful_checker.cli_io import print_error as print_error
from restful_checker.cli_io import resolve_openapi_path as resolve_openapi_path
from restful_checker.engine.analyzer import analyze_api

try:
    from restful_checker.tools.help_restful_checker import show_help
except ModuleNotFoundError:
    print("❌ Error: Missing help module at 'restful_checker/tools/help_restful_checker.py'")
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
        print_error(f"The file '{args.path}' is not a valid OpenAPI document.")
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
