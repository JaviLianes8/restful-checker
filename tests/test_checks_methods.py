"""HTTP method and status code checks."""

from __future__ import annotations

from typing import Any

import pytest

from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.status_code_checker import check_status_codes


@pytest.mark.parametrize("path", ["/v1/presets", "/v1/restarts", "/v1/updates", "/v1/startups"])
def test_words_containing_an_action_are_not_actions(path: str) -> None:
    assert check_http_methods(path, {"GET"}) == (["✅ HTTP method usage looks valid"], 1.0)


@pytest.mark.parametrize(
    ("path", "method", "text", "score"),
    [
        ("/v1/users/deleteUser", "GET", "action-like", 0.0),
        ("/v1/users/{id}/reset", "GET", "side-effect", 0.0),
        ("/v1/jobs/start-all", "GET", "side-effect", 0.0),
        ("/v1/users/remove_all", "POST", "deletion-like", 0.0),
        ("/v1/users/create", "PUT", "creation-like", 0.8),
        ("/v1/users/{id}", "POST", "resource ID", 0.8),
        ("/v1/users", "DELETE", "DELETE without ID", 0.8),
        ("/v1/users", "COPY", "Unusual HTTP method used: COPY", 0.8),
    ],
)
def test_method_rules(path: str, method: str, text: str, score: float) -> None:
    messages, result = check_http_methods(path, {method})
    assert any(text in m for m in messages)
    assert result == score


def test_one_message_per_rule_even_with_several_action_words() -> None:
    messages, _ = check_http_methods("/v1/createOrUpdate", {"GET"})
    assert len(messages) == 1


def ops(**methods: Any) -> dict[str, Any]:
    return {name: {"responses": {code: {} for code in codes}} for name, codes in methods.items()}


def test_complete_status_codes_pass() -> None:
    method_map = ops(
        get=["200", "404"], post=["201", "400", "409"], delete=["204", "404"], put=["200"]
    )
    method_map["put"]["responses"].update({"204": {}, "400": {}, "404": {}})
    assert check_status_codes("/v1/a", method_map) == (
        ["✅ Status code definitions look valid"],
        1.0,
    )


def test_integer_status_codes_from_yaml_do_not_crash() -> None:
    messages, score = check_status_codes("/v1/a", {"get": {"responses": {200: {}, 404: {}}}})
    assert messages == ["✅ Status code definitions look valid"]
    assert score == 1.0
    messages, _ = check_status_codes("/v1/a", {"get": {"responses": {200: {}, 500: {}}}})
    assert any("defines 500 manually" in m for m in messages)


def test_non_operation_entries_are_skipped() -> None:
    method_map = {"parameters": [{"name": "id"}], "summary": "s", **ops(get=["200", "404"])}
    assert check_status_codes("/v1/a", method_map)[1] == 1.0


@pytest.mark.parametrize(
    ("method_map", "text", "score"),
    [
        ({"get": {}}, "No status codes defined", 0.0),
        ({"get": {"responses": []}}, "No status codes defined", 0.0),
        (ops(get=["200", "404", "default"]), "Default response used", 0.8),
        (ops(get=["200"]), "missing expected status codes: 404", 0.8),
        (ops(post=["200", "400", "409"]), "should return 201", 0.0),
        (ops(post=["201", "204", "400", "409"]), "includes 204", 0.8),
        (ops(delete=["200", "404"]), "should return 204", 0.0),
        (ops(patch=["400", "404"]), "missing 200 or 204", 0.6),
    ],
)
def test_status_code_rules(method_map: dict[str, Any], text: str, score: float) -> None:
    messages, result = check_status_codes("/v1/a", method_map)
    assert any(text in m for m in messages)
    assert result == score
