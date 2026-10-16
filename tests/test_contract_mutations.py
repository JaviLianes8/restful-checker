"""Contracts added after the author mutation round, one per surviving mutation."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import pytest

from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.https_checker import server_kind
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.schema_tools import MAX_SCHEMAS, merged_properties
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.verb_words import words
from restful_checker.engine.path_grouper import group_paths
from restful_checker.report.extract_json_from_html import extract_json_from_html
from restful_checker.report.json_report import build_json_report


def test_put_with_204_is_a_success_code() -> None:
    ops: dict[str, Any] = {"put": {"responses": {"204": {}, "400": {}, "404": {}}}}
    assert check_status_codes("/v1/a/{id}", ops) == (
        ["⚠️ PUT /v1/a/{id} is missing expected status codes: 200"],
        0.8,
    )


def test_own_properties_win_over_all_of_members() -> None:
    schema = {"properties": {"a": 1}, "allOf": [{"properties": {"a": 2, "b": 3}}]}
    assert merged_properties(schema) == {"a": 1, "b": 3}


def test_schemas_are_read_up_to_the_limit() -> None:
    members: list[Any] = [{"properties": {f"p{i}": {}}} for i in range(MAX_SCHEMAS + 50)]
    merged = merged_properties({"allOf": members})
    assert merged is not None and len(merged) == MAX_SCHEMAS - 1  # the outer schema counts


def test_insecure_wins_over_relative() -> None:
    server = {"url": "{s}", "variables": {"s": {"enum": ["/b", "http://a"]}}}
    assert server_kind(server) == "insecure"


def test_error_messages_are_plain_text() -> None:
    result = CheckResult("naming")
    result.error("a <b> & 'c'")
    assert result.messages == ["❌ a <b> & 'c'"]


def test_a_none_methods_line_gives_no_methods() -> None:
    block = {"title": "/x", "items": ["HTTP methods: none", "### A"], "score": 1.0}
    assert "httpMethods" not in build_json_report([block], 100, "now")["sections"][0]


def page(depth: int) -> str:
    return "<div>" * depth + "<div class='section'><h2>/a (50%)</h2></div>" + "</div>" * depth


def test_pages_deeper_than_64_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "p.html"
    path.write_text(page(62), encoding="utf-8")
    assert extract_json_from_html(path)["sections"] == [{"score": 50, "items": [], "path": "/a"}]
    path.write_text(page(64), encoding="utf-8")
    with pytest.raises(ValueError, match="nested too deeply"):
        extract_json_from_html(path)


LONG = 200_000
LINEAR: list[tuple[str, Callable[[], Any]]] = [
    ("group", lambda: group_paths({"/" + "{" * LONG: {"get": {}}})),
    ("params", lambda: check_param_consistency({"/" + "{" * LONG: {}})),
    ("words", lambda: words("A" * LONG)),
    ("naming", lambda: check_naming("/v1/" + "a" * LONG)),
    ("pagination", lambda: check_pagination("/{" * LONG, {})),
    ("methods", lambda: check_http_methods("/{" * LONG, {"POST", "DELETE"})),
]


@pytest.mark.parametrize("action", [a for _, a in LINEAR], ids=[n for n, _ in LINEAR])
def test_long_routes_are_handled_in_linear_time(action: Callable[[], Any]) -> None:
    started = time.perf_counter()
    action()
    assert time.perf_counter() - started < 3  # the quadratic patterns took minutes
