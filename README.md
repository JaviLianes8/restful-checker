<a id="readme-top"></a>

# RESTful API Checker

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

[![PyPI version](https://img.shields.io/pypi/v/restful-checker?color=blue&label=PyPI)](https://pypi.org/project/restful-checker/)
[![Python](https://img.shields.io/pypi/pyversions/restful-checker?color=green)](https://pypi.org/project/restful-checker/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/JaviLianes8/restful-checker/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/restful-checker?color=orange)](https://pypi.org/project/restful-checker/)

Validate RESTful best practices on your OpenAPI/Swagger specs. Generates HTML and JSON
reports with actionable feedback.

## Why

OpenAPI linters such as [Spectral](https://github.com/stoplightio/spectral) and
[Redocly CLI](https://github.com/Redocly/redocly-cli) (TypeScript) or
[vacuum](https://github.com/daveshanley/vacuum) (Go) are rule engines you configure with a
ruleset. restful-checker is a small Python package with a fixed set of REST design checks
and a scored report: `pip install` it, point it at a document or URL, and open the HTML.
It reads Swagger 2.0 and OpenAPI 3.0, 3.1 and 3.2 documents in JSON or YAML.

## Installation

```bash
pip install restful-checker
```

Requires Python 3.8+. Depends on PyYAML (YAML documents) and requests (remote documents).

## Usage

```bash
# Local file
restful-checker path/to/openapi.json

# Remote URL
restful-checker https://api.example.com/openapi.yaml --open

# Generate HTML + JSON
restful-checker openapi.json --output-format both --output-folder reports
```

Remote documents are fetched within 60 seconds and up to 50 MB. Messages show a URL
without its user, password or query string.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-format` | `html`, `json`, or `both` | `html` |
| `--output-folder` | Destination folder | `./html` |
| `--open` | Open HTML in browser | `false` |
| `-q, --quiet` | Suppress output | `false` |
| `--version` | Show version | - |

`rest_report.html` and `rest_report.json` are both written to the output folder; the
format picks which ones are announced (and `json` and `both` write the JSON with non-ASCII
text as is).

## What It Checks

### URL Design
| Check | Description |
|-------|-------------|
| Versioning | A version segment (`v1`, `v2.1`, `v1beta1`, `v2alpha`) early in the path, followed by a resource |
| Resource Naming | Verbs in URIs (`getUsers`, `get-users`, `addtocart`), plural collections, casing, generic names |
| Resource Nesting | Patterns like `/users/{id}/orders` |
| Path Parameters | Consistent `{param}` naming across the document |

### HTTP Standards
| Check | Description |
|-------|-------------|
| HTTP Methods | GET, POST, PUT, PATCH, DELETE semantics; HEAD, OPTIONS, TRACE and QUERY are accepted |
| Status Codes | Expected codes per method (200, 201, 204, 400, 404, 409); ranges such as `2XX` count for every code of their class |
| Content Types | JSON bodies (`application/json`, `+json` types, JSON Lines and JSON sequences); binary and multipart bodies are accepted (see `is_binary_media_type`) |
| HTTPS Enforcement | OpenAPI 3 servers of the document, its paths and operations, with variables and relative URLs; Swagger 2.0 `schemes`, also per operation |

### Response Quality
| Check | Description |
|-------|-------------|
| Response Examples | `example` or `examples` on the media type or its schema (also through `allOf`) |
| Error Format | `code` and `message` fields, or RFC 9457 problem details (`application/problem+json` or `+xml`, or two of `type`, `title`, `status`, `detail`, `instance`), also through `allOf` |

### Performance
| Check | Description |
|-------|-------------|
| Pagination | `page`, `limit`, `offset`, `cursor`, `per_page`, `page_size`, `page_token` (or camel case) or JSON:API `page[...]` on collection GETs |
| Query Filters | Filters like `?status=` or JSON:API `filter[...]` on collection GETs, with a declared type |

### Limitations and choices

- The expected status codes are this tool's conventions and stricter than RFC 9110: PUT and
  PATCH are asked for 200 and 204, and a DELETE returning 200 without 204 is an error,
  where the RFC allows 200 or 204 for an update and 200, 202 or 204 for a deletion.
- An OpenAPI 3 document without top-level `servers` gets a warning, although the
  specification then defaults to `/`: declaring the server is the advice.
- Version segments with a minor or patch number (`v1.2`) are accepted, although some style
  guides (Google AIP-185) expose only the major version.

- Only local references (`#/components/...`) are followed. References to other files or
  URLs (`common.yaml#/Error`) are left unresolved, so whatever they hold is not checked.
- The Content Types, Response Examples and Error Format checks read OpenAPI 3 `content`;
  Swagger 2.0 bodies (`consumes`, `produces`, `in: body`) are not read.

## Programmatic Usage

```python
from restful_checker import analyze_api

result = analyze_api("path/to/openapi.json", output_dir="output")

print(f"HTML: {result['html_path']}")
print(f"JSON: {result['json_path']}")
print(f"Score: {result['json_report']['score']}")
```

`analyze_api(path, output_dir="html", output_format="html")` writes both reports and
returns `html_path`, `json_path` and `json_report` (the JSON report as a dictionary). It
raises `OSError` when the file cannot be read or the report written, and `ValueError` when
the file is not valid JSON or YAML, does not hold a mapping, has another extension, or is
nested too deeply to read.

Each check is also a function of its own, returning `(messages, score)`: plain-text
messages starting with ✅, ⚠️ or ❌, and a score from 0.0 to 1.0.

| Function | Module (`restful_checker.checks.`) |
|----------|------------------------------------|
| `check_versioning` | `version_checker` |
| `check_naming` | `naming_checker` |
| `check_http_methods` | `http_method_checker` |
| `check_status_codes`, `covers` | `status_code_checker` |
| `check_content_type`, `is_json_media_type`, `is_binary_media_type` | `content_type_checker` |
| `check_response_examples` | `response_example_checker` |
| `check_error_format`, `is_structured_error` | `check_error_format` |
| `check_query_filters` | `query_filter_checker` |
| `check_pagination`, `is_pagination_parameter` | `pagination_checker` |
| `check_resource_nesting` | `resource_nesting_checker` |
| `check_param_consistency` | `param_consistency_checker` |
| `check_https_usage`, `server_kind` | `https_checker` |

These, `analyze_api`, the command and the report layouts are the stable API; other names
in the submodules stay importable for existing code but may change.

```python
from restful_checker.checks.naming_checker import check_naming

print(check_naming("/v1/get-users"))
# (['❌ Contains verb-like segment: `get-users`'], 0.0)
```

## Guide and changes

The [GUIDE](https://github.com/JaviLianes8/restful-checker/blob/main/GUIDE.md) explains how
documents are read, every rule of every check, the scores and the report layout.

See the [CHANGELOG](https://github.com/JaviLianes8/restful-checker/blob/main/CHANGELOG.md);
3.2.0 lists every verdict that changed since 3.1.1.

## Contributing

Found a bug? Open an [issue](https://github.com/JaviLianes8/restful-checker/issues).

## License

MIT

---

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jlianesglrs)
