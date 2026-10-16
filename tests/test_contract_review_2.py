"""Contracts the second independent review's mutation round found missing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from restful_checker import analyze_api
from restful_checker.checks.https_checker import server_kind
from restful_checker.checks.naming_checker import check_naming
from restful_checker.cli_remote import utf8_body


def _spec(tmp_path: Path, paths: dict[str, Any]) -> Path:
    doc = {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}, "paths": paths}
    spec = tmp_path / "openapi.json"
    spec.write_text(json.dumps(doc), encoding="utf-8")
    return spec


def test_a_nested_output_folder_is_created(tmp_path: Path) -> None:
    out = tmp_path / "reports" / "api" / "v1"
    result = analyze_api(_spec(tmp_path, {}), output_dir=out)
    assert Path(result["html_path"]) == out / "rest_report.html"
    assert (out / "rest_report.json").is_file()


def test_routes_without_get_have_no_filters_section(tmp_path: Path) -> None:
    paths = {"/v1/users": {"post": {"responses": {"201": {"description": "created"}}}}}
    report = analyze_api(_spec(tmp_path, paths), output_dir=tmp_path / "o")["json_report"]
    users = next(s for s in report["sections"] if s.get("path") == "/v1/users")
    categories = [item["category"] for item in users["items"]]
    assert "Filters" not in categories
    assert "Pagination" in categories


def test_a_quoted_charset_is_honoured() -> None:
    headers = {"content-type": 'application/json; charset="ISO-8859-1"'}
    assert utf8_body("é".encode("latin-1"), headers) == "é".encode()


@pytest.mark.parametrize("url", ["h2c://api.example.com", "x-custom+http://api.example.com"])
def test_any_rfc_3986_scheme_is_a_scheme(url: str) -> None:
    assert server_kind({"url": url}) == "insecure"


def test_a_capital_followed_by_a_digit_is_a_mixed_name() -> None:
    messages, _ = check_naming("/v1/usersV2")
    assert "⚠️ Segment `usersV2` contains mixed alphanumeric name" in messages
