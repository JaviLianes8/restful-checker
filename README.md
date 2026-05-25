<a id="readme-top"></a>

# RESTful API Checker

[![PyPI version](https://img.shields.io/pypi/v/restful-checker?color=blue&label=PyPI)](https://pypi.org/project/restful-checker/)
[![Python](https://img.shields.io/pypi/pyversions/restful-checker?color=green)](https://pypi.org/project/restful-checker/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/restful-checker?color=orange)](https://pypi.org/project/restful-checker/)

Validate RESTful best practices on your OpenAPI/Swagger specs. Generates HTML reports with actionable feedback.

> This project is stable. Bug fixes will be released as issues are reported.

## Installation

```bash
pip install restful-checker
```

Requires Python 3.8+

## Usage

```bash
# Local file
restful-checker path/to/openapi.json

# Remote URL
restful-checker https://api.example.com/openapi.yaml --open

# Generate HTML + JSON
restful-checker openapi.json --output-format both --output-folder reports
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-format` | `html`, `json`, or `both` | `html` |
| `--output-folder` | Destination folder | `./html` |
| `--open` | Open HTML in browser | `false` |
| `-q, --quiet` | Suppress output | `false` |
| `--version` | Show version | - |

## What It Checks

### URL Design
| Check | Description |
|-------|-------------|
| Versioning | Ensures `/v1/`, `/v2/` appears early in paths |
| Resource Naming | Detects verbs in URIs, suggests pluralization |
| Resource Nesting | Validates patterns like `/users/{id}/orders` |
| Path Parameters | Verifies consistent `{param}` usage |

### HTTP Standards
| Check | Description |
|-------|-------------|
| HTTP Methods | Validates GET, POST, PUT, DELETE usage |
| Status Codes | Checks proper use of 200, 201, 400, 404, 409, etc. |
| Content Types | Verifies `application/json` usage |
| HTTPS Enforcement | Ensures all servers use HTTPS |

### Response Quality
| Check | Description |
|-------|-------------|
| Response Examples | Encourages `example` in responses |
| Error Format | Suggests structured `code` and `message` fields |
| Response Wrapping | Warns about unnecessary envelopes |

### Performance
| Check | Description |
|-------|-------------|
| Pagination | Suggests `?page=` and `?limit=` for collections |
| Query Filters | Recommends filters like `?status=` |
| GZIP Support | Checks `Accept-Encoding` |

## Programmatic Usage

```python
from restful_checker.engine.analyzer import analyze_api

result = analyze_api("path/to/openapi.json", output_dir="output")

print(f"HTML: {result['html_path']}")
print(f"JSON: {result['json_path']}")
print(f"Score: {result['json_report']['score']}")
```

## Project Structure

```
restful_checker/
├── checks/         # Validation modules
├── engine/         # OpenAPI loader
├── report/         # HTML rendering
├── tools/          # CLI utilities
└── main.py         # Entrypoint
```

## Contributing

Found a bug? Open an [issue](https://github.com/JaviLianes8/restful-checker/issues).

## License

MIT

---

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jlianesglrs)
