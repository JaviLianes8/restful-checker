# restful-checker 3.2.0 certification report

The certification bar of the catalogue's 1.0.0 releases, applied to 3.2.0.

Progress:
- [x] Branch `release/3.2.0` created from `main` (64f7afd, the merged improvement round)
- [x] Baseline gates run on `main` (203 passed, 1 skipped; ruff, mypy clean)
- [x] Owner's design decisions implemented with contracts (item 1)
- [x] Plain-text messages, JSON built from data, lazy import, deep documents (items 1, 5)
- [x] Packaging: metadata in pyproject, Python 3.8+ (items 13, 14)
- [x] Ground truth: fetched specs and real public OpenAPI documents (item 7)
- [x] Docstrings, doctests, contract, fuzz (items 2, 3, 6, 9)
- [x] Docs: README, CHANGELOG (items 11, 12)
- [x] Author mutation round (item 18)
- [x] e2e and upgrade from PyPI 3.1.1, every interpreter (items 8, 10)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer (item 16)
- [ ] Gates (item 15)
- [ ] PR open and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Ground truth (item 7)

Sources fetched on 2026-10-15 by `scripts/fetch_upstream.py` into the ignored
`tests/upstream/` folder; `tests/upstream/MANIFEST.json` records URL, revision, licence,
size and SHA-256 of each, and their tests skip when the folder is empty. Nothing of them is
committed or shipped.

- OpenAPI 2.0, 3.0.4, 3.1.2 and 3.2.1 (OAI/OpenAPI-Specification ffb3e579): Responses
  Object ranges, Server Object URL and variables, the default server, Swagger 2.0
  `schemes`, `format: binary`, multipart bodies, the Path Item operation fields.
- RFC 9110 (registered methods), RFC 9457 (problem details members and media type),
  RFC 6839 (`+json`), RFC 8259 (byte order mark).
- JSON:API 1.1 (json-api/json-api bde79ceb, CC0): the `page[...]` parameter family.
- Google AIP-185 (aip-dev/google.aip.dev 615875bf, CC BY 4.0): version segments
  `v1`, `v1.4.2`, `v1beta`, `v1beta1`, `v1alpha5`.
- Real documents: eleven OpenAPI examples from OAI/learn.openapis.org 82b82f37 (CC BY 4.0;
  Swagger 2.0, 3.0, 3.1 and the 3.2 QUERY example) and GitHub's REST description
  (github/rest-api-description a7fb3ea2, MIT, 13.5 MB). Every one is analyzed, its JSON
  report must equal the JSON file and the report read back from its HTML, and the server
  verdicts are checked against what each document declares (`tests/test_real_documents.py`).

`tests/test_sources_rules.py` checks each 3.2.0 rule against the sentence or table of the
source it rests on. No independent linter shares these style rules, so there is no oracle
for the verdicts themselves; the HTML reader is cross-checked against the JSON built from
data on every real document and on fuzzed ones.

## Supported Pythons (item 10)

From the installed wheel, the whole suite (the e2e module skips) on this PC's 3.8.20,
3.9.25, 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded; with the e2e
module (wheel, sdist, clean venvs, console script, upgrade from PyPI 3.1.1, suite from the
sdist) on 3.14.2 on the second build machine.

## Author mutation round (item 18)

Each mutation was applied alone to a fresh clone at 0b0a971 on the second build machine,
the suite run with `-x` without bytecode (the e2e module excluded), the file restored.
50 mutations: 41 killed, 1 equivalent (M07), 8 survived and were closed by
`tests/test_contract_mutations.py`, each checked to fail with its mutant.

| Id | Mutation | File | Result | Caught by |
| --- | --- | --- | --- | --- |
| M01 | QUERY dropped from usual methods | `http_method_checker.py` | killed | `tests/test_decisions_checks.py::test_registered_methods_are_not_unusual[QUERY]` |
| M02 | HEAD dropped from usual methods | `http_method_checker.py` | killed | `tests/test_decisions_checks.py::test_registered_methods_are_not_unusual[HEAD]` |
| M03 | range key built from the second digit | `status_code_checker.py` | killed | `tests/test_decisions_checks.py::test_ranges_stand_for_every_code_of_their_class` |
| M04 | ranges not upper-cased | `status_code_checker.py` | killed | `tests/test_decisions_checks.py::test_ranges_stand_for_every_code_of_their_class` |
| M05 | POST 201 rule ignores ranges | `status_code_checker.py` | killed | `tests/test_sources_rules.py::test_status_code_ranges[oas-3.0.4.md]` |
| M06 | PUT success ignores 204 | `status_code_checker.py` | killed after a new contract | `tests/test_contract_mutations.py::test_put_with_204_is_a_success_code` |
| M07 | range regex accepts 6XX | `status_code_checker.py` | equivalent | only expected codes of classes 2 and 4 and the `5` prefix are looked up, so a `6XX` key is never read |
| M08 | problem+json not recognised | `check_error_format.py` | killed | `tests/test_decisions_checks.py::test_problem_details_are_structured_errors` |
| M09 | one problem member is enough | `check_error_format.py` | killed | `tests/test_decisions_checks.py::test_one_problem_member_is_not_enough` |
| M10 | code alone is enough | `check_error_format.py` | killed | `tests/test_checks_bodies.py::test_error_format` |
| M11 | allOf members ignored | `schema_tools.py` | killed | `tests/test_decisions_checks.py::test_all_of_members_add_properties` |
| M12 | outer properties lose to members | `schema_tools.py` | killed after a new contract | `tests/test_contract_mutations.py::test_own_properties_win_over_all_of_members` |
| M13 | schema budget off | `schema_tools.py` | killed after a new contract | `tests/test_contract_mutations.py::test_schemas_are_read_up_to_the_limit` |
| M14 | schema examples ignored | `schema_tools.py` | killed | `tests/test_decisions_routes.py::test_schema_level_examples_count` |
| M15 | multipart not binary | `content_type_checker.py` | killed | `tests/test_decisions_checks.py::test_binary_and_multipart_bodies_are_accepted[multipart/form-data; boundary=x]` |
| M16 | octet-stream not binary | `content_type_checker.py` | killed | `tests/test_decisions_checks.py::test_binary_and_multipart_bodies_are_accepted[application/octet-stream]` |
| M17 | binary schema not read | `content_type_checker.py` | killed | `tests/test_doctests.py::test_module_examples_pass[restful_checker.checks.content_type_checker]` |
| M18 | binary message never shown | `content_type_checker.py` | killed | `tests/test_decisions_checks.py::test_binary_and_multipart_bodies_are_accepted[multipart/form-data; boundary=x]` |
| M19 | media type case kept | `content_type_checker.py` | killed | `tests/test_decisions_checks.py::test_binary_and_multipart_bodies_are_accepted[Multipart/Mixed]` |
| M20 | offset not a pagination name | `pagination_checker.py` | killed | `tests/test_decisions_checks.py::test_pagination_names[offset]` |
| M21 | page[...] family dropped | `pagination_checker.py` | killed | `tests/test_decisions_checks.py::test_pagination_names[page[number]]` |
| M22 | pagination case-sensitive | `pagination_checker.py` | killed | `tests/test_decisions_checks.py::test_pagination_names[perPage]` |
| M23 | swagger 2.0 still warns no servers | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_swagger_2_is_judged_by_its_schemes[doc0-expected0]` |
| M24 | wss not secure | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server2-secure]` |
| M25 | relative server is insecure | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server11-relative]` |
| M26 | enum ignored, default only | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server20-insecure]` |
| M27 | scheme compared case-sensitively | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server1-secure]` |
| M28 | unresolved reported as secure | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server17-unresolved]` |
| M29 | relative wins over insecure | `https_checker.py` | killed after a new contract | `tests/test_contract_mutations.py::test_insecure_wins_over_relative` |
| M30 | missing // accepted | `https_checker.py` | killed | `tests/test_decisions_routes.py::test_server_kinds[server5-insecure]` |
| M31 | beta versions refused | `version_checker.py` | killed | `tests/test_decisions_routes.py::test_version_segments[v1beta]` |
| M32 | static collection warning back | `version_checker.py` | killed | `tests/test_checks_naming.py::test_versioning_rules` |
| M33 | kebab verbs ignored | `verb_words.py` | killed | `tests/test_checks_naming.py::test_kebab_verbs_are_errors[get-users]` |
| M34 | post- prefix not a noun | `verb_words.py` | killed | `tests/test_decisions_routes.py::test_nouns_are_not_verbs[post-processing]` |
| M35 | do/add compounds never verbs | `verb_words.py` | killed | `tests/test_decisions_routes.py::test_verb_segments_are_errors[addtocart]` |
| M36 | addition stem shortened | `verb_words.py` | killed | `tests/test_decisions_routes.py::test_verb_segments_are_errors[additem]` |
| M37 | messages escaped again | `check_result.py` | killed after a new contract | `tests/test_contract_mutations.py::test_error_messages_are_plain_text` |
| M38 | HTML not escaped | `html_report.py` | killed | `tests/test_analyzer.py::test_markup_from_the_spec_is_escaped` |
| M39 | success lines get the link | `html_report.py` | killed | `tests/test_decisions_report.py::test_html_escapes_and_links_problems_only` |
| M40 | JSON keeps the given order | `json_report.py` | killed | `tests/test_decisions_report.py::test_json_lists_errors_then_warnings_then_the_rest` |
| M41 | JSON keeps the symbol | `json_report.py` | killed | `tests/test_analyzer.py::test_item_paths_are_checked_against_their_own_operations` |
| M42 | global sections reported as paths | `json_report.py` | killed | `tests/test_analyzer.py::test_score_and_global_sections` |
| M43 | none method kept | `json_report.py` | killed after a new contract | `tests/test_contract_mutations.py::test_a_none_methods_line_gives_no_methods` |
| M44 | deep JSON leaks RecursionError | `openapi_loader.py` | killed | `tests/test_decisions_report.py::test_deep_documents_raise_a_clear_error[deep.json]` |
| M45 | allOf refs not followed | `normalizer.py` | killed | `tests/test_decisions_report.py::test_all_of_cycles_and_fan_out_stay_bounded` |
| M46 | allOf expansion unbounded | `normalizer.py` | killed | `timeout` |
| M47 | HTML depth unbounded | `extract_json_from_html.py` | killed after a new contract | `tests/test_contract_mutations.py::test_pages_deeper_than_64_are_refused` |
| M48 | parenthesis groups kept | `extract_json_from_html.py` | killed | `tests/test_report.py::test_old_style_titles_are_still_read` |
| M49 | analyzer imported eagerly | `__init__.py` | killed | `tests/test_decisions_report.py::test_import_is_light_and_analyze_api_loads_on_use` |
| M50 | linear brace pattern reverted | `path_grouper.py` | killed after a new contract | `tests/test_contract_mutations.py::test_long_routes_are_handled_in_linear_time[group]` |

## QA lenses (item 19)

Each lens was a fresh reviewer that read the certification rules first, worked in its own
clone, ran things rather than reading, and reported back privately. One reviewer ran at a
time; heavy runs went to the second build machine under a turn.

| Lens | Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- | --- |
| a | 1 | dfb84d5 | FAIL | parameter schema `$ref`s not followed (false "no defined type"), malformed YAML raised `yaml.YAMLError` instead of the documented `ValueError`, README import path for the checks, 3.1.1 names no longer importable, CHANGELOG wording, typing names in `dir()`, missing examples. Fixed in 9bb4810 (`tests/test_contract_lens_a.py`) |
| a | 2 | 9bb4810 | PASS | two low notes: typed query parameters through `oneOf`/`anyOf`/`allOf`/`enum`/`content`, and the stable helpers named in the CHANGELOG. Fixed in 73226df |
| b | 1 | 73226df | FAIL | path and operation servers and 2.0 operation schemes ignored; 3.1 `$ref` siblings dropped; RFC 6901 decoding; `contentMediaType`, sequential JSON, `problem+xml`, JSON:API `filter[...]`; status-code conventions, missing servers and minor versions documented as choices. Fixed in e78d370 and 0694382 (`tests/test_contract_lens_b.py`) |
| b | 2 | 0694382 | FAIL | siblings replaced the target's keywords; typed `text/*` read as binary; upper-case operation servers. Fixed in f1a90a0 |
| b | 3 | f1a90a0 | FAIL | plain 3.1 `$ref`s wrapped in `allOf` hid the target's `type` and `format`. Fixed in 427f487 |
| b | 4 | 427f487 | PASS | independent resolver agrees with every count on GitHub's 3.0.3 and 3.1 descriptions; learn.openapis.org verdicts as predicted |
| c | 1 | e6ad2d4 | FAIL | references or YAML aliases growing work with the cube of the input; remote downloads unbounded in time and size; tracebacks on deep remote bodies and odd charsets; credentials and queries printed; a lone surrogate left an empty HTML report; exit 120 on a closed stdout; direct calls with non-string keys. Fixed in 7ce0a5a (`tests/test_contract_lens_c.py`) |
| c | 2 | 7ce0a5a | PASS | 3,000 fuzzed documents and 1,000 hostile pages without a crash or injection, every scaling ratio linear; three notes (operation parameters and request bodies in the expansion count, IPv6 brackets in messages, a temporary file after a failed write) fixed in 85eb2c4 |
| d | 1 | fae08f1 | PASS | wheel and sdist built and inspected, `twine check --strict`, console script and `python -m` from an empty folder on real documents and a local server, suite from the sdist against the installed package, in-place upgrade from PyPI 3.1.1 with every report difference traced to the CHANGELOG, suite from the wheel on 3.8.20 to 3.14.2 and 3.14.2 free-threaded (566 passed each); two cosmetic notes (program name under `python -m`, options missing from the no-argument help) fixed in the next commit |
| e | 1 | bd497b6 | PASS with contracts | blind round of 199 mutations over every module: 151 killed, 3 equivalent (A8: every group has a method, so the `none` label is unreachable; SC3: no check reads a `1XX` key; V3: a digit after a verb already counts, 1,080,000 random segments compared), 45 closed by `tests/test_contract_lens_e_cli.py` and `tests/test_contract_lens_e_checks.py`, each checked to fail on its mutant and pass on the original |
