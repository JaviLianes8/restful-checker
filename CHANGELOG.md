# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [3.2.0] - 2026-10-15

Stable surface: the `restful-checker` command and its options, `analyze_api(path,
output_dir="html", output_format="html")` with its three return keys, the twelve check
functions with their `(messages, score)` result, the six helpers named in the README
(`covers`, `is_json_media_type`, `is_binary_media_type`, `is_structured_error`,
`is_pagination_parameter`, `server_kind`), and the HTML and JSON report layouts.
Everything below that changes a verdict, a message or a score compared with 3.1.1 is
listed.

### Changed (verdicts that move on purpose)

- HEAD, OPTIONS, TRACE and QUERY are usual methods (RFC 9110, OpenAPI 3.2); only other
  methods get "Unusual HTTP method used".
- Status code ranges (`1XX` to `5XX`, as OpenAPI 3 allows; lower case is tolerated) count
  for every code of their class: a GET with `2XX` and `404` no longer misses 200, a POST
  with `200` and `2XX` no longer "returns 200, should return 201", and so on. A `5XX` range
  is still "defined manually".
- Error responses accept RFC 9457 problem details: a body served as
  `application/problem+json`, or a schema with at least two of `type`, `title`, `status`,
  `detail` and `instance`. Properties given through `allOf` count, and local `$ref`s inside
  `allOf` are followed. The success line reads "All error responses use 'code' and
  'message' or problem details"; the warning adds "or RFC 9457 problem details members".
- Binary and multipart bodies are accepted by Content Types: `application/octet-stream`,
  `application/pdf`, `application/zip`, `application/gzip`, any `image`, `audio`, `video`,
  `font` or `multipart` type, any `+zip` type, and any media type whose schema is
  `type: string, format: binary` (OpenAPI 3.0) or has a `contentMediaType` without a
  `contentEncoding` (OpenAPI 3.1). When one of them was accepted the success line reads "All request and
  response bodies use application/json, binary or multipart types".
  `application/x-www-form-urlencoded`, `text/*` and XML bodies are still errors.
- JSON Lines (`application/jsonl`, `application/x-ndjson`) and JSON text sequences
  (`application/json-seq`, `+json-seq`) count as JSON; the `itemSchema` of OpenAPI 3.2
  sequential media types is read for examples.
- `application/problem+xml` (RFC 9457) is a structured error body.
- Query filters accept the JSON:API `filter[...]` family as useful filters.
- Pagination accepts `offset`, `cursor`, `per_page`, `page_size`, `page_token`, their camel
  case forms and JSON:API `page[...]` next to `page` and `limit`, compared ignoring case.
- Swagger 2.0 documents are judged by `schemes` instead of always getting "No servers
  defined": all `https`/`wss` passes, any `http`/`ws` is "Not all servers use HTTPS", no
  schemes passes with "No schemes listed: the API uses the scheme of the document".
- OpenAPI 3 server URLs: relative URLs (`/api`, `//host/api`) pass ("All servers use HTTPS or
  a URL relative to the document"); server variables are replaced by every `enum` value (or
  the `default`), so `{scheme}://host` with `default: https` passes and with
  `enum: [https, http]` is "Not all servers use HTTPS"; a variable without a value in the
  scheme part warns "A server URL uses a variable without a default or enum". The scheme
  is compared ignoring case and `wss://` counts as secure. Servers given on a Path Item or
  an Operation (and Swagger 2.0 `schemes` given on an Operation) are judged too, so plain
  HTTP there is "Not all servers use HTTPS" even when the document's own servers are
  HTTPS.
- Response examples count an `example` or `examples` on the schema (also through `allOf`).
- Query filters no longer call a parameter untyped when its schema says what it holds
  through `enum`, `const`, `oneOf`/`anyOf` members that all have a type, or an `allOf`
  member, or when an OpenAPI 3 parameter gives its schema under `content`. Local `$ref`s in
  `oneOf` and `anyOf` are followed like those in `allOf`.
- Version segments include `v1.2`, `v1.0.3`, `v1beta`, `v1beta1` and `v2alpha5`, both for
  Versioning and for the mixed alphanumeric naming warning. Versioning no longer warns
  "Version segment exists but no dynamic resource parameter is found" on every static
  collection (`check_resource_static_only` is kept but no longer called).
- Naming catches kebab-case verbs (`get-users`, `create-order`, `add-item`; not `add-ons` or
  `post-` compounds such as `post-processing`). Lower-case `do` and `add` compounds
  (`addtocart`, `dologin`) stay errors as in 3.1.1, while nouns such as `documents`,
  `domains`, `downloads`, `addresses`, `additions` and `addons` are no longer flagged.
- Check messages are plain text. 3.1.1 returned them HTML-escaped with a "More info" link
  (`&#x27;code&#x27;`); the HTML report now escapes them and adds the link itself. Report
  blocks hold plain `Routes: ...` and `HTTP methods: ...` lines, and `generate_html`
  escapes every item it is given.
- The JSON report (`json_report` and `rest_report.json`) is built from the same data as the
  HTML instead of being parsed back from it. Its layout is unchanged; a message keeps any
  symbol or "More info" text that is part of the route it quotes.
- `analyze_api` raises `ValueError` for malformed YAML (with the parser's error as its
  cause; 3.1.1 raised `yaml.YAMLError`) and for a valid JSON or YAML document that is not a
  mapping (3.1.1 raised `AttributeError`). Malformed JSON keeps raising
  `json.JSONDecodeError`, a `ValueError`.
- Python 3.8 or newer is required (3.1.1 declared 3.7 but could not run there). Metadata
  lives in `pyproject.toml`; `setup.py`, `MANIFEST.in` and `requirements.txt` are gone.
- Messages use a comma where they used a long dash; single resources show "Skipped
  pagination check (single resource)" under Pagination.
- `beautifulsoup4` is no longer a dependency. `extract_json_from_html` (for HTML reports
  without their JSON) uses the standard library parser and refuses, with `ValueError`, a
  page nested more than 64 elements deep.

### Fixed

- A document nested too deeply for the JSON or YAML parser raises `ValueError` ("... is
  nested too deeply to read") instead of `RecursionError`; the command reports it and
  exits 1.
- Very long route names (thousands of capitals, letters or `{` characters) no longer take
  quadratic time in the naming, method, grouping and parameter checks.
- The package imports and runs on Python 3.8 and 3.9 again.
- YAML specs with unquoted status codes (`200:`) no longer crash the status code check.
- Only operations count as HTTP methods. Path-level `parameters`, `summary`, `description`,
  `servers` and `x-` extensions are no longer reported as methods or crash a check, and
  `x-` keys of the Paths Object are no longer read as paths. OpenAPI 3.2 `query` and
  `additionalOperations` are read. An operation key written in capitals (`GET`) counts
  once, next to `get`. A path with no operation at all no longer shows up in the report.
- Item paths such as `/v1/users/{userId}` and paths with a trailing slash are checked for
  status codes, content types, examples and error format. Before, these checks looked the
  route up by its grouped name and always passed.
- In OpenAPI 3.1 and 3.2 documents, keywords next to a schema `$ref` (`examples`,
  `properties`) apply, as JSON Schema 2020-12 says; 2.0 and 3.0 still ignore them.
- Local references are read as RFC 6901 says: the fragment is percent-decoded before it is
  split (`#/a%2Fb` is `a` then `b`), and array indexes are plain ASCII digits without a
  leading zero.
- Path-level parameters apply to every operation, and local `$ref`s to path items,
  parameters (and their schemas), request bodies, responses, media types and schemas are
  followed. Malformed
  `responses` or `content` (a list, a string) no longer crash a check.
- Naming no longer flags nouns that start like a verb (`posts`, `documents`, `addresses`,
  `updates`) and no longer warns about the `v1` version segment.
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

- `from restful_checker import analyze_api` (imported on first use, so `import
  restful_checker` stays light), `restful_checker.__version__` and a `py.typed` marker;
  `analyze_api` returns `json_path`, as the README example uses.
- Helpers next to the checks: `is_json_media_type`, `is_binary_media_type`,
  `is_pagination_parameter`, `is_structured_error`, `server_kind` and `covers`. Names
  importable from the submodules in 3.1.1 stay importable.
- The command line helpers live in `restful_checker.cli_io`; `restful_checker.main` still
  exposes them under the same names.

### Known limitations

- References to other files or URLs are not resolved (deferred to a later release).

## [3.1.1]

Last release before this changelog.
