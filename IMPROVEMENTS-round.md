# restful-checker improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: OpenAPI 2.0, 3.0.4, 3.1.2, 3.2.1, RFC 9110, RFC 6839, RFC 9457, RFC 8259
- [x] Spec reading: operations only, path-level parameters, local references, string status codes
- [x] Analyzer: item paths checked against their own operations
- [x] Checker false positives (verb prefixes, version segment, item pagination, JSON media types, word matching)
- [x] Report: escaped HTML, correct `httpMethods`, `json_path` returned
- [x] Command line: remote YAML, encodings, temporary file, Windows console
- [x] Python 3.8 and 3.9 import and run
- [x] Tests and coverage, contracts, pinned sources
- [x] Typing: mypy --strict, py.typed
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Mutation run
- [ ] Independent review findings fixed
- [ ] Pull request opened, guard clean

Every change keeps the public surface: `analyze_api(path, output_dir, output_format)`, its
return keys, every checker function and its `(messages, score)` tuple, the CLI options and the
HTML and JSON layouts. Fixes and additions only; anything that changes a verdict on purpose
for a reason other than a bug is listed under Proposals for the owner.

## Starting point

`3.1.1` had no tests. Probed with small specs on CPython 3.13, 3.9 and 3.8:

- The package does not import on Python 3.8 (`tuple[list[str], float]` in a signature) or 3.9
  (`str | Path`), although `setup.py` says 3.7 and the README says 3.8.
- A YAML spec with unquoted status codes (`200:`) crashes the whole run in the status code
  check (`int` has no `startswith`). PyYAML reads them as integers.
- Every non-operation key of a Path Item is read as an HTTP method: a path-level
  `parameters` list becomes method `PARAMETERS` ("Unusual HTTP method") and crashes the
  status code check when the same item is looked up with `.get`; `summary`, `description`,
  `servers` and `x-` extensions crash it too. `x-` keys in the Paths Object become paths.
- The status code, content type, response example and error format checks look the group
  up by its normalised path (`/v1/users/{id}`, trailing `/` stripped). Any item path whose
  parameter is not literally `{id}`, and any path with a trailing slash, finds nothing and
  reports "looks valid" with a full score.
- Naming flags `posts`, `documents`, `addresses`, `domains`, `makers` as verbs (prefix match
  on `post`, `do`, `add`, `make`) with an error, and warns on `v1` as a "mixed alphanumeric"
  segment, so every versioned API loses points for doing what the versioning check asks.
- The method checks match by substring: GET `/v1/presets` is a "side-effect path" (`reset`),
  GET `/v1/restarts` too (`start`).
- Pagination is demanded on single-resource GETs (`/v1/users/{id}`); the README and the
  filter check say it is for collections.
- `application/problem+json` (RFC 9457) and `application/json; charset=utf-8` are reported as
  "does not use application/json" errors.
- Parameters, responses, request bodies and schemas given as `$ref` are not followed, and
  path-level parameters are ignored, so a `$ref` to a `page` parameter still gets the
  pagination warning.
- The JSON report's `httpMethods` ends with the first letter of the next heading (`"GET\nV"`),
  because the regex reading it back from the HTML crosses the line.
- Route names and section titles are written into the HTML unescaped; a remote spec can put
  markup into the report the user opens with `--open`.
- The README's Python example reads `result['json_path']`, which `analyze_api` never returned.
- A remote spec whose URL has a query string or no extension is saved as `.json` and fails
  to load when it is YAML; the body is decoded with the charset `requests` guesses
  (ISO-8859-1 for `text/*` without one); the temporary file is never deleted. A UTF-8 BOM
  makes a local JSON file fail. On a Windows console with a legacy code page, redirected
  output crashes on the status emoji.

## Sources (fetched 2026-10-15)

- OpenAPI Specification 2.0, 3.0.4, 3.1.2 and 3.2.1, the Markdown sources at
  OAI/OpenAPI-Specification commit ffb3e579dfb4ef5ae1a68d11af125e2a593505fc
  (`versions/<v>.md`): Paths Object (`/` keys and `^x-` extensions), Path Item fixed fields
  (eight operations, `query` and `additionalOperations` from 3.2, `parameters` apply to every
  operation and are overridden by name and location), Responses Object keys (quoted codes,
  `default`, `2XX` ranges), Reference Object and JSON Pointer fragments, Media Type Object
  (`example`, `examples`).
- RFC 9110, https://www.rfc-editor.org/rfc/rfc9110.txt: method names are case-sensitive
  (9.1), the registered methods, safe and idempotent methods (9.2), status code classes (15).
- RFC 6839, https://www.rfc-editor.org/rfc/rfc6839.txt: the `+json` structured syntax suffix.
- RFC 9457, https://www.rfc-editor.org/rfc/rfc9457.txt: `application/problem+json` and the
  problem details members.
- RFC 8259, https://www.rfc-editor.org/rfc/rfc8259.txt: JSON exchanged between systems is
  UTF-8 and a parser may ignore a BOM (8.1).
- None of these files is committed. `tests/upstream/MANIFEST.json` records URL, revision,
  size, sha256 and licence; `scripts/fetch_upstream.py` fetches and checks them into the
  ignored `tests/upstream/` folder; the tests that read them skip while they are absent.

## Ranked improvements

1. **Read the spec as the spec says.** One normalisation step before the checks: only
   operation keys (and 3.2 `additionalOperations`) count as methods, `x-` keys are skipped,
   path-level parameters are merged into each operation (operation wins by name and
   location), local `$ref`s to path items, parameters, request bodies, responses and media
   schemas are followed with a cycle guard, status code keys become strings. The caller's
   document is never modified.
2. **Check item paths against their own operations.** Each group runs the per-operation
   checks on its real paths, so `/v1/users/{userId}` and `/v1/users/` are checked.
3. **Remove false positives that contradict the check's own purpose**: verb prefixes need a
   word boundary, version segments are not "mixed alphanumeric", method action words match
   whole words, pagination skips single resources, JSON media types include parameters and
   `+json` suffixes.
4. **Report fixes.** Escape everything taken from the spec, read `httpMethods` back from its
   own line, return `json_path` as the README shows.
5. **Command line.** Remote YAML detected by content, bytes kept as sent, temporary file
   removed, BOM accepted, `.JSON` accepted, safe printing on legacy consoles.
6. **Runs on 3.8+.** Postponed annotations and a resource reader that works on 3.8.
7. **Tests, typing, gates.** Behaviour tests per checker and per bug, contract tests for the
   public surface, pinned-source tests, `mypy --strict`, ruff, a local gate script, a
   mutation run.

## Out of scope

- New checks or new scoring rules, a new CLI option, changes to message levels: see
  Proposals.
- External `$ref`s (other files or URLs): they stay unresolved, as before.
