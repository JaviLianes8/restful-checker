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
  `additionalOperations` are read. An operation key written in capitals (`GET`) counts
  once, next to `get`. A path with no operation at all no longer shows up in the report.
- Item paths such as `/v1/users/{userId}` and paths with a trailing slash are checked for
  status codes, content types, examples and error format. Before, these checks looked the
  route up by its grouped name and always passed.
- Path-level parameters apply to every operation, and in OpenAPI 3 documents local `$ref`s
  to path items, parameters, request bodies, responses, media types and schemas are
  followed. Malformed `responses` or `content` (a list, a string) no longer crash a check.
- Naming no longer flags nouns that start like a verb (`posts`, `documents`, `addresses`,
  `updates`) and no longer warns about the `v1` version segment. Verb compounds such as
  `getUsers` or `createorder` are still errors.
- Method checks look at the words of a route, so `presets` or `restarts` are no longer
  side-effect routes, while `deleteUser`, `resetpassword` or `HTTPReset` still are.
- Pagination and query filters are no longer asked of single resources such as
  `/v1/users/{id}` or `/v1/users/{id}/`.
- `application/json` with parameters and `+json` media types such as
  `application/problem+json` count as JSON.
- The JSON report's `httpMethods` no longer carries the first letter of the next heading,
  and section titles holding parentheses are read back whole.
- Route names from the spec are escaped in the HTML report.
- Remote specs are saved with the suffix that matches their content (URLs with a query
  string or without an extension). UTF-8 bodies are kept as sent and a declared other
  charset is converted, instead of guessing ISO-8859-1. The temporary file is removed after
  the run, and an invalid remote document is reported by its URL. A UTF-8 byte order mark
  and upper-case extensions are accepted.
- When one group holds several routes (`/v1/users` and `/v1/users/`), a success line is
  shown once per section instead of once per route.
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
- Single resources show "Skipped pagination check (single resource)" under Pagination.
- The command line helpers live in `restful_checker.cli_io`; `restful_checker.main` still
  exposes them under the same names.

## [3.1.1]

Last release before this changelog.
