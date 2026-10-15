"""End to end through analyze_api: the bugs of 3.1.1 stay fixed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import all_messages, document, ok_operation, write_json

from restful_checker import analyze_api


def run(tmp_path: Path, doc: Any, name: str = "openapi.json") -> dict[str, Any]:
    if name.endswith(".json"):
        source = write_json(tmp_path, doc, name)
    else:
        source = tmp_path / name
        source.write_text(doc, encoding="utf-8")
    return analyze_api(source, output_dir=tmp_path / "out")


def section(report: dict[str, Any], path: str) -> dict[str, Any]:
    return next(s for s in report["sections"] if s.get("path") == path)


def test_return_value_has_the_documented_keys(tmp_path: Path) -> None:
    result = run(tmp_path, document({"/v1/users": {"get": ok_operation("200", "404")}}))
    assert set(result) == {"html_path", "json_path", "json_report"}
    assert Path(result["html_path"]) == tmp_path / "out" / "rest_report.html"
    assert json.loads(Path(result["json_path"]).read_text(encoding="utf-8")) == result["json_report"]


def test_item_paths_are_checked_against_their_own_operations(tmp_path: Path) -> None:
    doc = document({"/v1/users/{userId}": {"get": ok_operation("500")}})
    report = run(tmp_path, doc)["json_report"]
    texts = [m["message"] for m in all_messages(report, "Status Codes")]
    assert "GET /v1/users/{userId} is missing expected status codes: 200, 404" in texts
    assert section(report, "/v1/users/{id}")["score"] < 100


def test_trailing_slash_paths_are_checked(tmp_path: Path) -> None:
    report = run(tmp_path, document({"/v1/users/": {"get": {"responses": {}}}}))["json_report"]
    assert any("No status codes defined" in m["message"] for m in all_messages(report))


def test_yaml_with_unquoted_status_codes(tmp_path: Path) -> None:
    spec = """openapi: 3.0.3
info: {title: t, version: '1'}
servers: [{url: 'https://a.example'}]
paths:
  /v1/users:
    get:
      parameters: [{name: page, in: query, schema: {type: integer}}]
      responses:
        200: {description: ok}
        404: {description: missing}
"""
    report = run(tmp_path, spec, "openapi.yaml")["json_report"]
    assert section(report, "/v1/users")["httpMethods"] == ["GET"]
    assert all(m["level"] == "info" for m in all_messages(report, "Status Codes"))


def test_path_level_parameters_are_not_a_method(tmp_path: Path) -> None:
    item = {"parameters": [{"name": "userId", "in": "path"}], "summary": "s", "x-a": 1}
    item["get"] = ok_operation("200", "404")
    report = run(tmp_path, document({"/v1/users/{userId}": item}))["json_report"]
    assert section(report, "/v1/users/{id}")["httpMethods"] == ["GET"]
    assert not any("Unusual" in m["message"] for m in all_messages(report))


def test_http_methods_in_json_are_exact(tmp_path: Path) -> None:
    doc = document({"/v1/users": {"get": ok_operation("200"), "post": ok_operation("201")}})
    report = run(tmp_path, doc)["json_report"]
    assert section(report, "/v1/users")["httpMethods"] == ["GET", "POST"]


def test_referenced_page_parameter_counts(tmp_path: Path) -> None:
    get = ok_operation("200", "404")
    get["parameters"] = [{"$ref": "#/components/parameters/page"}]
    components = {"parameters": {"page": {"name": "page", "in": "query"}}}
    report = run(tmp_path, document({"/v1/users": {"get": get}}, components=components))
    assert all(m["level"] == "info" for m in all_messages(report["json_report"], "Pagination"))


def test_problem_json_errors_are_json(tmp_path: Path) -> None:
    get = ok_operation("200", "404")
    get["responses"]["404"]["content"] = {"application/problem+json": {"example": {}}}
    report = run(tmp_path, document({"/v1/users": {"get": get}}))["json_report"]
    assert all(m["level"] == "info" for m in all_messages(report, "Content Types"))


def test_markup_from_the_spec_is_escaped(tmp_path: Path) -> None:
    doc = document({"/v1/<b>x</b>": {"get": ok_operation("200")}})
    result = run(tmp_path, doc)
    html = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "<b>x</b>" not in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert section(result["json_report"], "/v1/<b>x</b>")["httpMethods"] == ["GET"]


def test_titles_with_parentheses_survive(tmp_path: Path) -> None:
    report = run(tmp_path, document({"/v1/a(b)s": {"get": ok_operation("200")}}))["json_report"]
    assert report["sections"][0]["path"] == "/v1/a(b)s"


def test_several_routes_in_one_group(tmp_path: Path) -> None:
    doc = document({"/v1/users": {"get": ok_operation("200", "404")}, "/v1/users/": {"get": {}}})
    report = run(tmp_path, doc)["json_report"]
    assert len(report["sections"]) == 3
    assert any("GET /v1/users/" in m["message"] for m in all_messages(report, "Status Codes"))


def test_score_and_global_sections(tmp_path: Path) -> None:
    report = run(tmp_path, document({}))["json_report"]
    assert [s.get("section") for s in report["sections"]] == ["SSL", "Global Parameter Consistency"]
    assert report["score"] == 100
    assert report["title"] == "RESTful API Report"
    assert report["generated"]


def test_not_a_document_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not hold an OpenAPI document"):
        run(tmp_path, [1, 2])


def test_unknown_suffix_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "spec.txt"
    source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file extension"):
        analyze_api(source, output_dir=tmp_path)


def test_byte_order_mark_is_accepted(tmp_path: Path) -> None:
    source = tmp_path / "openapi.JSON"
    source.write_bytes(b"\xef\xbb\xbf" + json.dumps(document({})).encode())
    assert analyze_api(source, output_dir=tmp_path / "o")["json_report"]["score"] == 100
