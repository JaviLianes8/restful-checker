# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- The package imports and runs on Python 3.8 and 3.9 again (annotations are postponed and
  the stylesheet is read with `pkgutil` where `importlib.resources.files` is missing).
- YAML specs with unquoted status codes (`200:`) no longer crash the status code check.
- Only operations count as HTTP methods. Path-level `parameters`, `summary`, `description`,
  `servers` and `x-` extensions are no longer reported as methods or crash a check, and
  `x-` keys of the Paths Object are no longer read as paths. OpenAPI 3.2 `query` and
  `additionalOperations` are read.
- Item paths such as `/v1/users/{userId}` and paths with a trailing slash are checked for
  status codes, content types, examples and error format. Before, these checks looked the
  route up by its grouped name and always passed.
- Path-level parameters apply to every operation, and local `$ref`s to path items,
  parameters, request bodies, responses, media types and schemas are followed.
- Naming no longer flags nouns that start like a verb (`posts`, `documents`, `addresses`)
  and no longer warns about the `v1` version segment.
- Method checks match whole words, so `presets` or `restarts` are no longer side-effect
  routes.
- Pagination is no longer asked of single resources such as `/v1/users/{id}`.
- `application/json` with parameters and `+json` media types such as
  `application/problem+json` count as JSON.
- The JSON report's `httpMethods` no longer carries the first letter of the next heading,
  and section titles holding parentheses are read back whole.
- Route names from the spec are escaped in the HTML report.
- Remote specs are saved with the suffix that matches their content (URLs with a query
  string or without an extension), keep their bytes as sent, and the temporary file is
  removed after the run. A UTF-8 byte order mark and upper-case extensions are accepted.
- A console or pipe with a legacy code page no longer crashes on the status symbols.
- Swagger 2.0 query parameters with a `type` are no longer reported as untyped.

### Added

- `analyze_api` returns `json_path`, as the README example uses.
- `restful_checker.analyze_api` and `restful_checker.__version__` at package level, and a
  `py.typed` marker.
- `is_json_media_type` in `restful_checker.checks.content_type_checker`.
- Tests, type hints checked with `mypy --strict`, and a local gate script.

### Changed

- Messages use a comma where they used a long dash.

## [3.1.1]

Last release before this changelog.
