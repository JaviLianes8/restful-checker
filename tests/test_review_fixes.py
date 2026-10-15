"""Findings of the independent review, each pinned by a test that failed before its fix."""

from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest
import yaml
from conftest import FakeResponse, all_messages, document, ok_operation, write_json

from restful_checker import analyze_api
from restful_checker import main as cli
from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.content_type_checker import check_content_type
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.response_example_checker import check_response_examples


def report_of(tmp_path: Path, paths: dict[str, Any]) -> dict[str, Any]:
    tmp_path.mkdir(exist_ok=True)
    source = write_json(tmp_path, document(paths))
    report: dict[str, Any] = analyze_api(source, output_dir=tmp_path / "out")["json_report"]
    return report


@pytest.mark.parametrize(
    "operation",
    [
        {"responses": ["200"]},
        {"responses": "x"},
        {"responses": {"404": {"content": ["application/json"]}}},
        {"responses": {"200": {"content": "text/plain"}}, "requestBody": {"content": 1}},
    ],
)
def test_malformed_responses_do_not_crash(tmp_path: Path, operation: dict[str, Any]) -> None:
    report = report_of(tmp_path, {"/v1/users": {"get": operation}})
    assert report["score"] is not None
    for check in (check_content_type, check_response_examples, check_error_format):
        check("/v1/users", {"get": operation})


@pytest.mark.parametrize("segment", ["getusers", "createorder", "deleteall", "fetchdata"])
def test_lower_case_verb_compounds_are_still_verbs(segment: str) -> None:
    assert any("verb-like" in m for m in check_naming(f"/v1/{segment}")[0])


@pytest.mark.parametrize("segment", ["updates", "makers", "postings", "addresses", "dogs"])
def test_nouns_made_from_a_verb_are_not_verbs(segment: str) -> None:
    assert not any("verb-like" in m for m in check_naming(f"/v1/{segment}")[0])


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/v1/users/deleteuser", "POST"),
        ("/v1/resetpassword", "GET"),
        ("/v1/jobs/startjob", "GET"),
        ("/v1/users/HTTPReset", "GET"),
        ("/v1/users/userdelete", "GET"),
    ],
)
def test_action_compounds_are_still_flagged(path: str, method: str) -> None:
    assert check_http_methods(path, {method})[1] == 0.0


def test_participles_are_not_actions() -> None:
    assert check_http_methods("/v1/users/deleted", {"GET"})[1] == 1.0


def test_trailing_slash_item_paths_get_no_filters(tmp_path: Path) -> None:
    report = report_of(tmp_path, {"/v1/users/{id}/": {"get": ok_operation("200", "404")}})
    assert not all_messages(report, "Filters")
    skipped = check_query_filters("/v1/users/{id}/", {"get": {}})[0]
    assert skipped == ["✅ Skipped query filter check (single resource)"]


def test_case_variant_operations_count_once(tmp_path: Path) -> None:
    item = {"get": ok_operation("200", "404"), "GET": {"responses": {}}}
    report = report_of(tmp_path, {"/v1/users": item})
    assert report["sections"][0]["httpMethods"] == ["GET"]
    assert not any("No status codes" in m["message"] for m in all_messages(report))
    upper_only = report_of(tmp_path / "u", {"/v1/users": {"GET": ok_operation("200", "404")}})
    assert all_messages(upper_only, "Filters")


def test_routes_of_one_group_do_not_repeat_success_lines(tmp_path: Path) -> None:
    report = report_of(tmp_path, {"/v1/users": {"get": {}}, "/v1/users/": {"get": {}}})
    texts = [m["message"] for m in all_messages(report, "Content Types")]
    assert texts == ["No request or response bodies to validate"]


def fetch(monkeypatch: pytest.MonkeyPatch, body: bytes, content_type: str) -> Any:
    response = FakeResponse(body, content_type)
    monkeypatch.setattr("restful_checker.cli_io.requests.get", lambda url, timeout: response)
    local = cli.resolve_openapi_path("https://a.example/openapi.yaml")
    try:
        with open(local, encoding="utf-8") as f:
            return yaml.safe_load(f)
    finally:
        os.remove(local)


def test_declared_charset_is_decoded(monkeypatch: pytest.MonkeyPatch) -> None:
    body = "openapi: 3.0.0\ninfo: {title: café}\n"
    data = fetch(monkeypatch, body.encode("latin-1"), "text/yaml; charset=ISO-8859-1")
    assert data["info"]["title"] == "café"
    data = fetch(monkeypatch, body.encode("utf-8"), "text/plain")
    assert data["info"]["title"] == "café"
    data = fetch(monkeypatch, body.encode("utf-8"), 'text/yaml; charset="UTF_8"')
    assert data["info"]["title"] == "café"
    data = fetch(monkeypatch, b"openapi: 3.0.0\n", "text/yaml; charset=no-such-charset")
    assert data == {"openapi": "3.0.0"}


def test_invalid_remote_document_names_the_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    response = FakeResponse(b"{}")
    monkeypatch.setattr("restful_checker.cli_io.requests.get", lambda url, timeout: response)
    args = Namespace(
        path="https://a.example/x.json", output_folder=str(tmp_path), output_format="html",
        open=False, quiet=True,
    )  # fmt: skip
    assert cli.run_checker(args) == 1
    assert "'https://a.example/x.json' is not a valid OpenAPI document" in capsys.readouterr().out
