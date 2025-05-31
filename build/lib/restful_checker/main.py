from restful_checker.analyzer.analyzer import analyze_api
from urllib.parse import urlparse

import sys
import requests
import tempfile

def main():
    if len(sys.argv) != 2:
        print("Usage: restful-checker <path_to_openapi.json or URL> ")
        sys.exit(1)

    path = sys.argv[1]
    parsed = urlparse(path)

    if parsed.scheme in ("http", "https"):
        response = requests.get(path)
        if response.status_code != 200:
            print(f"❌ Failed to download OpenAPI from {path}")
            sys.exit(1)

        suffix = '.yaml' if path.endswith(('.yaml', '.yml')) else '.json'
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix=suffix) as tmp:
            tmp.write(response.text)
            tmp.flush()
            path = tmp.name

    output = analyze_api(path)
    print(f"✅ Report generated: {output}")
