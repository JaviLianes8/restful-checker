"""Pagination, filter, nesting, parameter consistency and HTTPS checks."""

from __future__ import annotations

from typing import Any

import pytest

from restful_checker.checks.https_checker import check_https_usage
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.resource_nesting_checker import check_resource_nesting


def get_with(*params: dict[str, Any]) -> dict[str, Any]:
    return {"get": {"parameters": list(params)}}


@pytest.mark.parametrize("path", ["/v1/users/{id}", "/v1/users/{userId}/", "/{id}"])
def test_pagination_skips_single_resources(path: str) -> None:
    assert check_pagination(path, get_with()) == (
        ["✅ Skipped pagination check (single resource)"],
        1.0,
    )


def test_pagination_on_collections() -> None:
    page = {"name": "page", "in": "query"}
    assert check_pagination("/v1/users", get_with(page))[1] == 1.0
    assert check_pagination("/v1/users", get_with({"name": "limit"}))[1] == 1.0
    messages, score = check_pagination("/v1/users", get_with({"name": "q"}, "junk"))  # type: ignore[arg-type]
    assert any("GET /v1/users does not support pagination" in m for m in messages)
    assert score == 0.8
    assert check_pagination("/v1/users", {"get": {"parameters": None}})[1] == 0.8
    assert check_pagination("/v1/users/{id}/orders", get_with())[1] == 0.8
    assert check_pagination("/v1/users", {"post": {}, "get": "x"})[0] == [
        "✅ No GET operations to validate for pagination"
    ]


def test_filters() -> None:
    assert check_query_filters("/v1/users/{id}", get_with())[0] == [
        "✅ Skipped query filter check (single resource)"
    ]
    assert check_query_filters("/v1/users", {})[0] == [
        "✅ No GET operation to validate for filters"
    ]
    assert any("has no query filters" in m for m in check_query_filters("/v1/users", get_with())[0])
    typed = {"name": "status", "in": "query", "schema": {"type": "string"}}
    assert check_query_filters("/v1/users", get_with(typed))[1] == 1.0
    vague = {"name": "q", "in": "query", "schema": {"type": "string"}}
    assert any(
        "none look like useful filters" in m for m in check_query_filters("/u", get_with(vague))[0]
    )
    obj = {"name": "sort", "in": "query", "schema": {"type": "object"}}
    assert any("type `object`" in m for m in check_query_filters("/u", get_with(obj))[0])
    untyped = {"name": "sort", "in": "query", "schema": "x"}
    assert any("no defined type" in m for m in check_query_filters("/u", get_with(untyped))[0])


def test_filters_read_swagger_2_parameter_type() -> None:
    swagger = {"name": "status", "in": "query", "type": "string"}
    assert check_query_filters("/u", get_with(swagger, "junk"))[1] == 1.0  # type: ignore[arg-type]
    assert check_query_filters("/u", {"get": {"parameters": None}})[1] == 0.8


def test_nesting() -> None:
    assert check_resource_nesting("/users", {})[0] == ["✅ Path too shallow to check nesting."]
    assert check_resource_nesting("/users/{id}/orders", {})[1] == 1.0
    messages, score = check_resource_nesting("/users/orders", {})
    assert any("missing parent ID" in m for m in messages)
    assert score == 0.0
    messages, score = check_resource_nesting("/users/{a}/{b}", {})
    assert any("multiple consecutive IDs" in m for m in messages)
    assert score == 0.8


def test_parameter_consistency() -> None:
    assert check_param_consistency({"/a/{userId}": {}}) == (
        ["✅ Path parameters look consistent"],
        1.0,
    )
    messages, _ = check_param_consistency({"/a/{userId}": {}, "/b/{userid}": {}})
    assert any("Inconsistent parameter naming: userId, userid" in m for m in messages)
    messages, _ = check_param_consistency({"/a/{user_id}": {}, "/b/{orderId}": {}})
    assert any("Mixed parameter styles" in m for m in messages)
    messages, score = check_param_consistency({"/a/{id}": {}})
    assert any("Generic parameter name used: `id`" in m for m in messages)
    assert score == 0.8


def test_https() -> None:
    assert check_https_usage({"servers": [{"url": "https://a"}]}) == (
        ["✅ All servers use HTTPS"],
        1.0,
    )
    assert check_https_usage({"servers": [{"url": "https://a"}, {"url": "http://b"}]})[1] == 0.0
    assert check_https_usage({})[1] == 0.8
    assert check_https_usage({"servers": "https://a"})[1] == 0.8
    assert check_https_usage({"servers": ["https://a"]})[1] == 0.0
    assert check_https_usage({"servers": [{"url": None}]})[1] == 0.0
