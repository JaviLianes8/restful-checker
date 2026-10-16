"""Contracts the independent review's mutation round found missing."""

from __future__ import annotations

import pytest

from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.https_checker import check_https_usage
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.verb_words import words
from restful_checker.engine.normalizer import MAX_UNITS, normalize_paths


def test_a_lone_server_with_an_unresolved_variable_warns() -> None:
    doc = {"openapi": "3.1.0", "servers": [{"url": "{scheme}://api.example.com"}]}
    assert check_https_usage(doc) == (
        ["⚠️ A server URL uses a variable without a default or enum"],
        0.8,
    )


@pytest.mark.parametrize("name", ["filter[status", "filter["])
def test_an_unclosed_filter_family_name_is_not_a_useful_filter(name: str) -> None:
    get = {"get": {"parameters": [{"name": name, "in": "query", "schema": {"type": "string"}}]}}
    messages, score = check_query_filters("/v1/users", get)
    assert messages == [
        "⚠️ GET /v1/users has query params but none look like useful filters (e.g., `filter`, "
        "`status`)"
    ]
    assert score == 0.8


def test_a_const_schema_declares_the_type_of_a_query_parameter() -> None:
    param = {"name": "status", "in": "query", "schema": {"const": "active"}}
    assert check_query_filters("/v1/users", {"get": {"parameters": [param]}}) == (
        ["✅ Collection endpoints support query filters"],
        1.0,
    )


def test_a_run_of_capitals_stays_one_word() -> None:
    assert words("/v1/HTTPReset/RESETPASSWORD") == ["v1", "http", "reset", "resetpassword"]
    assert check_http_methods("/v1/RESETPASSWORD", {"GET"})[0] == [
        "❌ GET used for side-effect path: `/v1/RESETPASSWORD`, should be POST or PUT"
    ]


def test_operation_parameters_count_towards_the_expansion_limit() -> None:
    params = [{"name": f"p{i}", "in": "query"} for i in range(MAX_UNITS)]
    doc = {"paths": {"/v1/users": {"get": {"parameters": params}}}}
    with pytest.raises(ValueError, match="expands to more than 50000"):
        normalize_paths(doc)


def test_request_body_media_types_count_towards_the_expansion_limit() -> None:
    content: dict[str, dict[str, object]] = {f"application/x{i}+json": {} for i in range(MAX_UNITS)}
    doc = {"paths": {"/v1/users": {"post": {"requestBody": {"content": content}}}}}
    with pytest.raises(ValueError, match="expands to more than 50000"):
        normalize_paths(doc)


def test_one_short_of_the_limit_is_read() -> None:
    params = [{"name": f"p{i}", "in": "query"} for i in range(MAX_UNITS - 1)]
    doc = {"paths": {"/v1/users": {"get": {"parameters": params}}}}
    assert len(normalize_paths(doc)["/v1/users"]["get"]["parameters"]) == MAX_UNITS - 1
