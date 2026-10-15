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
- [x] Docs: README factual fixes, CHANGELOG
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Mutation run
- [x] Independent review findings fixed
- [x] Pull request opened (#1), guard clean

Every change keeps the public surface: `analyze_api(path, output_dir, output_format)`, its
return keys, every checker function and its `(messages, score)` tuple, the CLI options and the
HTML and JSON layouts. Fixes and additions only; anything that changes a verdict on purpose
for a reason other than a bug is listed under Proposals for the owner, at the end.

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
  Proposals for the owner.
- External `$ref`s (other files or URLs): they stay unresolved, as before.

## Verification

- Gates from a fresh clone of the branch on another machine, after the fetch script had
  fetched every source and matched the manifest: `ruff format --check .`, `ruff check .`,
  `mypy --strict restful_checker tests` and `pytest` exit 0 on CPython 3.14. With
  `RESTFUL_CHECKER_E2E=1` the installed-wheel test builds the wheel and sdist, checks their
  contents (stylesheet, `py.typed` and the new module in the wheel, no planning notes or
  fetched files in the sdist), installs the wheel in a fresh venv and drives the
  `restful-checker` script, `python -m restful_checker` and the package API from an empty
  folder. The suite also passes on CPython 3.8 and 3.9 (the end-to-end test skipped there).
  Line coverage of the package was 99% before the review fixes; what was left is the plural
  check's unreachable guard, the missing-help-module exit and the `__main__` guard.
- Path Item operation fields of OpenAPI 2.0, 3.0.4, 3.1.2 and 3.2.1, the Paths Object key
  rules, the path-level parameter rule, the status code key wording, the RFC 9110 method
  table, the RFC 6839 suffix, the RFC 9457 media type and the RFC 8259 byte order mark rule
  are read from the pinned files in `tests/test_sources.py`.
- Guarded logic was changed one piece at a time from a clean clone, without bytecode and
  with a timeout per mutant, the suite green before. First run: 65 mutants, 10 alive (the
  JSON pointer escape order, capital operation keys, averaging several routes, the Filters
  skip for single resources, a section colour threshold, the `none` methods line, a JSON
  body under a `.yaml` URL, POST with 200 and 201, DELETE with 200 and 204, nesting under a
  singular parent); a test was added for each. Second run, after the review fixes: 78
  mutants, 4 alive, all in the new word rules (short verbs followed by `_` or a digit, the
  camel and acronym splits); tests were added and each was checked to fail with its mutant.

## Review fixes

An independent review attacked the branch; each finding below is fixed with a test that
fails on the code before the fix (`tests/test_review_fixes.py`):

- `analyze_api` still crashed on a `responses` that is a list or a string and on a
  `content` that is a list. The normaliser reads malformed ones as empty and the checkers
  guard against them when called directly.
- The naming and method fixes had gone further than the bug: all-lower-case compounds
  (`getusers`, `createorder`, `deleteuser`, `resetpassword`, `startjob`) and acronym routes
  (`HTTPReset`) were no longer caught. A verb now counts at the start of a word unless what
  follows is a noun ending (`posts`, `updates`, `makers`, `deleted`); `do` and `add`, which
  start too many nouns, count only as words of their own. Method checks also catch a verb
  at the end of a word (`userdelete`).
- A remote spec served in a declared non-UTF-8 charset failed; a declared charset other
  than UTF-8 is now converted, UTF-8 and undeclared bodies are kept as sent.
- The single-resource rule with a trailing slash (`/users/{id}/`) is shared by Pagination,
  Filters and the analyzer.
- `get` next to `GET`, or `additionalOperations` repeating a fixed field in other capitals,
  counted twice; operation keys are read case-insensitively, once, and the exact field wins.
- Several routes in one group repeated the same success line; it is shown once.
- `main.py` was over 200 lines; the input and output helpers moved to `cli_io.py` and are
  still importable from `main` under their names.
- An invalid remote document was reported by the path of the deleted temporary file; the
  message names the URL.
- This file referred to a proposals section that did not exist yet.

## Proposals for the owner

These would change verdicts or scores that existing users see, or are design choices, so
they are not in the code. Each is a suggestion, ranked by how often it should bite.

1. **HEAD, OPTIONS, TRACE and QUERY are "unusual".** `VALID_METHODS` holds five methods;
   RFC 9110 registers HEAD, OPTIONS and TRACE, and OpenAPI 3.2 adds QUERY. A spec that
   documents HEAD or OPTIONS loses points.
2. **Status code ranges.** `2XX`, `4XX` and friends are valid Responses keys in every
   OpenAPI 3 version, but a GET with `2XX` and `404` is still told it misses 200.
3. **Error format and RFC 9457.** Problem details (`type`, `title`, `status`, `detail`,
   `instance`) are the standard JSON error body, yet they get "should include 'code' and
   'message'". Schemas built with `allOf` also read as unstructured.
4. **Binary bodies.** `application/octet-stream` downloads and `multipart/form-data`
   uploads are errors (score 0) in Content Types, although there is no JSON alternative.
5. **Pagination names.** Only `page` and `limit` count; `offset`, `cursor`, `per_page`,
   `pageSize`, `size` and JSON:API `page[...]` (the page the check links to) do not.
6. **Swagger 2.0 servers.** A 2.0 document has `schemes` and `host`, never `servers`, so it
   always gets "No servers defined". Relative server URLs (`/api`) and templated ones
   (`{scheme}://...`) are errors.
7. **Response examples.** A schema-level `example` and the 2.0 response `examples` field
   are not counted.
8. **Versioning.** `v1.2` and `v1beta1` are not version segments, and every static
   collection (`/v1/users`) is warned that it has no dynamic parameter.
9. **Verb detection edges.** Kebab forms (`get-users`) were never caught, and lower-case
   compounds of `do` and `add` (`addtocart`) are no longer caught, because those two
   verbs start too many nouns (`documents`, `addresses`). A small noun list could catch
   them without bringing the false positives back.
10. **Output formats.** `--output-format json` still writes the HTML report, and `html`
    also writes `rest_report.json`. The JSON is rebuilt by parsing the HTML; building both
    from the same data would keep the format and drop the BeautifulSoup round trip.
11. **Escaped messages in the Python API.** Checker messages are HTML-escaped (`&#x27;`,
    `&lt;`), which is right for the report but odd for callers of the checker functions.
12. **External references.** `$ref`s to other files or URLs stay unresolved.
13. **Supported Pythons and version.** `setup.py` says 3.7, the README 3.8, and the code
    needs 3.8 (`typing.Literal`); the branch is tested on 3.8, 3.9 and 3.14. Suggest
    `python_requires=">=3.8"` and, since `json_path` and the package exports are additions,
    release as 3.2.0.
14. **Packaging.** Metadata could move from `setup.py` to `pyproject.toml` with one version
    source; `setup.py` was left as written.
15. **Very deep documents.** A JSON spec nested thousands of levels deep raises
    `RecursionError` from the standard `json` module; it could become a clear error.
16. **Import cost.** `import restful_checker` now loads the analyzer (and BeautifulSoup) to
    offer `analyze_api` at package level; a lazy attribute would keep the import light.
