# restful-checker guide

How restful-checker reads a document, what each check looks for, how scores are computed and
what the reports hold. The README has the quick start; the CHANGELOG lists every change.

## Reading the document

- JSON (`.json`) or YAML (`.yaml`, `.yml`, any case) in UTF-8; a byte order mark is accepted.
  A URL is downloaded first (60 seconds, 50 MB at most) and read as JSON or YAML from its
  path or, without an extension, from its content.
- Swagger 2.0 and OpenAPI 3.0, 3.1 and 3.2 are read. Only the fields of the Path Item that
  hold operations count as methods (`get`, `put`, `post`, `delete`, `options`, `head`,
  `patch`, `trace`, `query`, and the 3.2 `additionalOperations`); `x-` keys are skipped.
- Path-level parameters apply to every operation; an operation parameter with the same name
  and location replaces one. Status codes are read as strings (`200:` in YAML is fine).
- Local references (`#/components/...`) are followed: path items, operations, parameters,
  request bodies, responses, media types, schemas and the members of `allOf`, `oneOf` and
  `anyOf`. Pointers are decoded as RFC 6901 says. In 3.1 and 3.2, keywords next to a schema
  `$ref` apply together with the target. References to other files or URLs are not read.
- A document is refused with `ValueError` when it is not a mapping, is nested too deeply for
  the parser, or expands through its references to more than 50,000 operations, responses
  and media types.

## Groups and scores

Routes are grouped by resource: `{anything}` becomes `{id}` and a trailing `/` is dropped, so
`/v1/users`, `/v1/users/` and `/v1/users/{userId}` form one group. Each group gets sections
(Versioning, Naming, HTTP Methods, Status Codes, Content Types, Response Examples, Error
Format, then Filters, Pagination and Resource Nesting per route). Two global blocks follow:
SSL (servers) and Global Parameter Consistency.

A section starts at 1.0. An error sets it to 0; each warning takes 0.2 off (never below 0)
unless an error already did. A block's score is the mean of its sections, the final score
the mean of all blocks, shown as a percentage.

## The checks

| Section | Errors | Warnings |
|---------|--------|----------|
| Versioning | no version segment; two of them; one deeper than the third segment; nothing after it; an ID right after it | a version segment third in the path |
| Naming | a verb segment (`getUsers`, `get_users`, `get-users`, `addtocart`); camelCase or PascalCase; a preposition | a last segment not ending in `s`; a letter followed by a digit; `data`, `info`, `object`, `thing`, `stuff`, `item` |
| HTTP Methods | GET on a route with create, update, delete, remove, reset, execute, trigger or start; POST on delete or remove | PUT on create; POST with an ID in the route; DELETE without one; a method other than GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, QUERY |
| Status Codes | no responses; POST answering 200 without 201; DELETE answering 200 without 204 | missing expected codes (GET 200, 404; POST 201, 400, 409; PUT and PATCH 200, 204, 400, 404; DELETE 204, 404); `default`; POST with 204; PUT or PATCH without 200 or 204; any `5xx` |
| Content Types | a body that is not JSON, binary or multipart | |
| Response Examples | | a response body without `example` or `examples` on its media type or schema |
| Error Format | | a 4xx, 5xx or `default` body that is not structured |
| Filters | | a collection GET without query parameters, without a useful one, with an `object` or untyped one |
| Pagination | | a collection GET without a pagination parameter |
| Resource Nesting | two plural segments in a row without an ID between them | two IDs in a row |
| Servers | a server (document, path or operation level) on plain HTTP | no top-level servers; a server variable without a value |
| Parameters | | one name in several casings; snake_case next to camelCase; `id`, `name`, `value` |

A range key (`2XX`) stands for every code of its class. JSON means `application/json`,
`+json` types and JSON sequences (`application/jsonl`, `application/x-ndjson`,
`application/json-seq`). Binary means octet-stream, PDF, zip, gzip, `+zip`, image, audio,
video, font and multipart types, and schemas describing raw file contents. A structured
error has `code` and `message`, or two RFC 9457 members (`type`, `title`, `status`,
`detail`, `instance`), or is served as `application/problem+json` or `+xml`. Pagination
parameters are `page`, `limit`, `offset`, `cursor`, `per_page`, `page_size`, `page_token`
(any case, camel forms too) and `page[...]`; useful filters are `filter`, `status`, `type`,
`sort`, `limit` and `filter[...]`. Single resources (`/users/{id}`) skip Filters and
Pagination. Swagger 2.0 is judged by `schemes`, a document without them passing.

## Reports

`rest_report.html` and `rest_report.json` are written to the output folder, whole or not at
all. The JSON holds `title`, `score`, `generated` and `sections`; a section has `score`
(percent), `items` (each a `category` with `messages`, every message a `message` and a
`level` of `error`, `warn` or `info`, errors first), `path` or `section`, and `httpMethods`
for route groups.

## Python API

`analyze_api(path, output_dir="html", output_format="html")` writes both reports and returns
`html_path`, `json_path` and `json_report`. Each check function returns `(messages, score)`;
messages are plain text starting with ✅, ⚠️ or ❌ (the HTML report escapes them and adds
the link). The README lists the stable functions and helpers and their modules.

## Upgrading from 3.1

Scores move where a verdict changed on purpose (see CHANGELOG 3.2.0): registered methods,
status ranges, problem details, binary bodies, pagination names, servers and schemes,
schema examples, version names, verbs. Messages are plain text instead of HTML. Python 3.8
or newer is needed, and `beautifulsoup4` is no longer installed with the package.
