"""Content type, response example and error format checks."""

from __future__ import annotations

from typing import Any

import pytest

from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.content_type_checker import check_content_type, is_json_media_type
from restful_checker.checks.response_example_checker import check_response_examples


def responses(media_type: str, code: str = "200", **media: Any) -> dict[str, Any]:
    return {"get": {"responses": {code: {"content": {media_type: media}}}}}


@pytest.mark.parametrize(
    "media_type",
    [
        "application/json",
        "application/json; charset=utf-8",
        "Application/JSON",
        "application/problem+json",
        "application/vnd.api+json",
        "application/hal+json;v=1",
    ],
)
def test_json_media_types(media_type: str) -> None:
    assert is_json_media_type(media_type)
    assert check_content_type("/a", responses(media_type))[1] == 1.0


@pytest.mark.parametrize("media_type", ["application/xml", "text/plain", "+json", "json", 3, None])
def test_non_json_media_types(media_type: object) -> None:
    assert not is_json_media_type(media_type)


def test_non_json_bodies_are_errors() -> None:
    messages, score = check_content_type("/a", responses("application/xml"))
    assert any("response 200 does not use application/json" in m for m in messages)
    assert score == 0.0
    body: dict[str, Any] = {"post": {"requestBody": {"content": {"text/csv": {}}}}}
    messages, score = check_content_type("/a", body)
    assert any("POST /a requestBody does not use application/json" in m for m in messages)
    assert score == 0.0


def test_content_type_success_messages_and_odd_nodes() -> None:
    assert check_content_type("/a", {}) == (["✅ No request or response bodies to validate"], 1.0)
    odd = {"get": {"requestBody": [], "responses": {"200": None, "204": {"content": []}}}}
    assert check_content_type("/a", {"x": 1, **odd})[1] == 1.0
    ok: dict[str, Any] = {"post": {"requestBody": {"content": {"application/json": {}}}}}
    assert check_content_type("/a", ok)[0] == [
        "✅ All request and response bodies use application/json"
    ]


def test_examples() -> None:
    assert check_response_examples("/a", responses("application/json", example=1))[1] == 1.0
    assert check_response_examples("/a", responses("application/json", examples={}))[1] == 1.0
    messages, score = check_response_examples("/a", responses("application/json"))
    assert any("GET /a response 200 is missing example" in m for m in messages)
    assert score == 0.8
    assert check_response_examples("/a", {"get": {"responses": {"204": {}}}})[0] == [
        "✅ No response bodies to evaluate for examples"
    ]
    odd = {"get": {"responses": {"200": {"content": {"a/b": "x"}}, "201": None}}, "s": "x"}
    assert check_response_examples("/a", odd)[1] == 0.8


def error_schema(schema: Any, code: Any = "404") -> dict[str, Any]:
    return responses("application/json", code=code, schema=schema)


def test_error_format() -> None:
    good: dict[str, Any] = {"properties": {"code": {}, "message": {}}}
    assert check_error_format("/a", error_schema(good))[0] == [
        "✅ All error responses include 'code' and 'message'"
    ]
    assert check_error_format("/a", error_schema(good, code=500))[1] == 1.0
    messages, score = check_error_format("/a", error_schema({"properties": {"code": {}}}))
    assert any("should include &#x27;code&#x27; and &#x27;message&#x27;" in m for m in messages)
    assert score == 0.8
    schemas: tuple[Any, ...] = ({}, {"properties": []}, "x")
    for schema in schemas:
        messages, _ = check_error_format("/a", error_schema(schema, code="default"))
        assert any("has no structured schema" in m for m in messages)
    assert check_error_format("/a", error_schema(good, code="200"))[0] == [
        "✅ No 4xx or 5xx responses to validate"
    ]
    odd = {"get": {"responses": {"400": None, "401": {"content": {"a/b": None}}}}, "s": 1}
    assert any("401 has no structured schema" in m for m in check_error_format("/a", odd)[0])
