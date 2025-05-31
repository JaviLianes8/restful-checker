from restful_checker.engine.analyzer import analyze_api
from urllib.parse import urlparse
import os
import sys
import requests
import tempfile
import json
import yaml

def is_valid_file(path):
    return os.path.isfile(path) and path.endswith(('.json', '.yaml', '.yml'))

def is_valid_openapi(path):
    """ Verifica si el archivo contiene un esquema OpenAPI válido. """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.json'):
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

            if 'openapi' in data or 'swagger' in data:
                return True
            return False
    except Exception as e:
        print(f"❌ Error al analizar el archivo: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: restful-checker <path_to_openapi.[json|yaml|yml]> or URL")
        sys.exit(1)

    path = sys.argv[1]
    parsed = urlparse(path)

    if parsed.scheme in ("http", "https"):
        try:
            response = requests.get(path, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Failed to fetch URL: {e}")
            sys.exit(1)

        suffix = '.yaml' if path.endswith(('.yaml', '.yml')) else '.json'
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix=suffix, encoding='utf-8') as tmp:
            tmp.write(response.text)
            tmp.flush()
            path = tmp.name

    elif not is_valid_file(path):
        print(f"❌ Invalid file: '{path}'")
        print("👉 Must be a local file ending in .json, .yaml, or .yml")
        sys.exit(1)

    if not is_valid_openapi(path):
        print(f"❌ The file '{path}' is not a valid OpenAPI document.")
        sys.exit(1)

    try:
        output = analyze_api(path)
        print(f"✅ Report generated: {output}")
    except Exception as e:
        print(f"❌ Error analyzing API: {e}")
        sys.exit(1)