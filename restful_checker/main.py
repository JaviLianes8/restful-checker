import argparse
import json
import os
import sys
import tempfile
import requests
import yaml

from urllib.parse import urlparse
from restful_checker.engine.analyzer import analyze_api

try:
    from restful_checker.tools.help_restful_checker import show_help
except ModuleNotFoundError:
    print("❌ Error: Missing help module at 'restful_checker/tools/help_restful_checker.py'")
    sys.exit(1)


def print_error(msg):
    """
    Print a formatted error message to the console.
    """
    print(f"❌ {msg}")


def is_valid_file(path):
    """
    Check if a path points to a valid OpenAPI file with .json, .yaml, or .yml extension.
    
    Args:
        path (str): Path to check.
    
    Returns:
        bool: True if the path is a valid file with a correct extension.
    """
    return os.path.isfile(path) and path.endswith(('.json', '.yaml', '.yml'))


def is_valid_openapi(path):
    """
    Validate if the file at the given path is a valid OpenAPI or Swagger document.
    
    Args:
        path (str): Path to the OpenAPI file.
    
    Returns:
        bool: True if the file contains a valid OpenAPI or Swagger root key.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f) if path.endswith('.json') else yaml.safe_load(f)
            return 'openapi' in data or 'swagger' in data
    except Exception as e:
        print_error(f"Error parsing OpenAPI file: {e}")
        return False


def resolve_openapi_path(path):
    """
    Resolve a given path to a valid local file.
    If the path is a URL, downloads the content to a temporary file.
    
    Args:
        path (str): URL or local path to the OpenAPI definition.
    
    Returns:
        str: Path to the resolved local file (original or temporary).
    """
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        try:
            response = requests.get(path, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print_error(f"Failed to fetch URL: {e}")
            sys.exit(1)

        suffix = '.yaml' if path.endswith(('.yaml', '.yml')) else '.json'
        tmp = tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix=suffix, encoding='utf-8')
        tmp.write(response.text)
        tmp.flush()
        return tmp.name
    elif is_valid_file(path):
        return path
    else:
        print_error(f"Invalid file: '{path}'\n👉 Must be a local .json/.yaml/.yml file or a valid URL")
        sys.exit(1)


def parse_arguments():
    """
    Parse command-line arguments using argparse.
    
    Returns:
        argparse.Namespace: Parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Check RESTful API compliance from OpenAPI definitions and generate reports."
    )
    parser.add_argument("path", nargs="?", help="Path or URL to OpenAPI file (.json, .yaml, .yml)")
    parser.add_argument("--output-format", choices=["html", "json", "both"], default="html",
                        help="Output format: html, json, or both (default: html)")
    parser.add_argument("--output-folder", default="html",
                        help="Destination folder for output reports (default: ./html)")
    return parser.parse_args()


def run_checker(args):
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

    if not is_valid_openapi(path):
        print_error(f"The file '{path}' is not a valid OpenAPI document.")
        return 1

    try:
        result = analyze_api(path, output_dir=args.output_folder)

        if args.output_format in ["html", "both"]:
            print(f"✅ HTML report generated: {os.path.abspath(result['html_path'])}")

        if args.output_format in ["json", "both"]:
            json_path = os.path.join(args.output_folder, "rest_report.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result["json_report"], f, indent=2, ensure_ascii=False)
            print(f"✅ JSON report generated: {os.path.abspath(json_path)}")

        return 0
    except Exception as e:
        print_error(f"Error analyzing API: {e}")
        return 1


def main():
    """
    CLI entry point. Parses arguments and executes the checker.
    """
    args = parse_arguments()
    sys.exit(run_checker(args))


if __name__ == "__main__":
    main()