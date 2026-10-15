"""The 3.2.0 decisions on methods, status codes, error bodies, media types and pagination."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import problems

from restful_checker.checks.check_error_format import check_error_format, is_structured_error
from restful_checker.checks.content_type_checker import check_content_type, is_binary_media_type
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.pagination_checker import check_pagination, is_pagination_parameter
from restful_checker.checks.status_code_checker import check_status_codes, covers


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "TRACE", "QUERY", "head", "query"])
def test_registered_methods_are_not_unusual(method: str) -> None:
    assert check_http_methods("/v1/users", {method}) == (["✅ HTTP method usage looks valid"], 1.0)


def codes(method: str, *keys: str) -> tuple[list[str], float]:
    return check_status_codes("/v1/a", {method: {"responses": {key: {} for key in keys}}})


def test_ranges_stand_for_every_code_of_their_class() -> None:
    assert codes("get", "2XX", "4XX")[1] == 1.0
    assert codes("get", "2xx", "404")[1] == 1.0  # lower case is tolerated
    assert codes("get", "2XX") == (["⚠️ GET /v1/a is missing expected status codes: 404"], 0.8)
    assert codes("put", "2XX", "4XX")[1] == 1.0
    assert codes("patch", "2XX", "400", "404")[1] == 1.0
    assert codes("delete", "200", "2XX", "404")[1] == 1.0
    assert codes("post", "2XX", "4XX")[1] == 1.0


def test_explicit_codes_keep_their_rules() -> None:
    assert any("returns 200, should return 201" in m for m in codes("post", "200", "400")[0])
    assert any("returns 200, should return 204" in m for m in codes("delete", "200", "404")[0])
    assert any("includes 204" in m for m in codes("post", "201", "204", "400", "409")[0])
    assert codes("get", "200", "404", "5XX") == (
        ["⚠️ GET /v1/a defines 5XX manually, server errors should be implicit"],
        0.8,
    )


@pytest.mark.parametrize("key", ["6XX", "2X", "20X", "XXX", "2XXX"])
def test_only_the_five_ranges_count(key: str) -> None:
    messages, _ = codes("get", key, "404")
    assert "⚠️ GET /v1/a is missing expected status codes: 200" in messages


def test_covers() -> None:
    assert covers({"201"}, "201") and covers({"2XX"}, "204") and not covers({"3XX"}, "204")


def error(media_type: str, schema: Any = None, code: str = "404") -> tuple[list[str], float]:
    media: dict[str, Any] = {} if schema is None else {"schema": schema}
    responses = {code: {"content": {media_type: media}}}
    return check_error_format("/v1/a", {"get": {"responses": responses}})


def test_problem_details_are_structured_errors() -> None:
    ok = ["✅ All error responses use 'code' and 'message' or problem details"]
    assert error("application/problem+json") == (ok, 1.0)
    assert error("Application/Problem+JSON; charset=utf-8", {"type": "string"})[1] == 1.0
    assert error("application/json", {"properties": {"title": {}, "detail": {}}}) == (ok, 1.0)
    assert error("application/json", {"properties": {"code": {}, "message": {}}}, "5XX")[1] == 1.0


def test_one_problem_member_is_not_enough() -> None:
    assert error("application/json", {"properties": {"title": {}, "error": {}}}) == (
        [
            "⚠️ GET /v1/a error 404 should include 'code' and 'message' fields or RFC 9457 "
            "problem details members"
        ],
        0.8,
    )
    assert not is_structured_error(None, {"properties": {"code": {}}})


def test_all_of_members_add_properties() -> None:
    schema: dict[str, Any] = {
        "allOf": [{"properties": {"code": {}}}, {"properties": {"message": {}}}]
    }
    assert error("application/json", schema)[1] == 1.0
    nested: dict[str, Any] = {"allOf": [{"allOf": [{"properties": {"type": {}, "status": {}}}]}]}
    assert error("application/json", nested)[1] == 1.0
    bare = {"allOf": [{"type": "object"}]}
    assert problems(error("application/json", bare)[0]) == [
        "⚠️ GET /v1/a error 404 has no structured schema"
    ]


BINARY = ["multipart/form-data; boundary=x", "Multipart/Mixed", "application/octet-stream",
          "application/pdf", "application/zip", "application/gzip", "image/png", "audio/mpeg",
          "video/mp4", "font/woff2"]  # fmt: skip


@pytest.mark.parametrize("media_type", BINARY)
def test_binary_and_multipart_bodies_are_accepted(media_type: str) -> None:
    assert is_binary_media_type(media_type)
    ops: dict[str, Any] = {"post": {"requestBody": {"content": {media_type: {}}}}}
    assert check_content_type("/v1/a", ops) == (
        ["✅ All request and response bodies use application/json, binary or multipart types"],
        1.0,
    )
    response: dict[str, Any] = {"get": {"responses": {"200": {"content": {media_type: {}}}}}}
    assert check_content_type("/v1/a", response)[1] == 1.0


@pytest.mark.parametrize(
    ("media_type", "schema"),
    [("application/x-www-form-urlencoded", None), ("text/csv", None), ("text/plain", "string"),
     ("application/xml", None), (None, None)],
)  # fmt: skip
def test_other_bodies_still_need_json(media_type: Any, schema: Any) -> None:
    media = {"schema": {"type": schema}} if schema else {}
    assert not is_binary_media_type(media_type, media)
    ops = {"post": {"requestBody": {"content": {media_type: media}}}}
    assert check_content_type("/v1/a", ops)[1] == 0.0


def test_json_next_to_binary_keeps_the_json_message() -> None:
    content: dict[str, Any] = {"application/json": {}, "application/pdf": {}}
    ops = {"get": {"responses": {"200": {"content": content}}}}
    assert check_content_type("/v1/a", ops)[0] == [
        "✅ All request and response bodies use application/json"
    ]


@pytest.mark.parametrize(
    "name",
    ["page", "limit", "offset", "cursor", "per_page", "perPage", "page_size", "pageSize",
     "page_token", "pageToken", "PAGE", "page[number]", "page[cursor]", "page[]"],
)  # fmt: skip
def test_pagination_names(name: str) -> None:
    assert is_pagination_parameter(name)
    get = {"get": {"parameters": [{"name": name, "in": "query"}]}}
    assert check_pagination("/v1/users", get) == (
        ["✅ GET endpoints support pagination parameters"],
        1.0,
    )


@pytest.mark.parametrize("name", ["pages", "page[", "size", "next", "", None, 3, "xpage[a]"])
def test_other_names_do_not_page(name: Any) -> None:
    assert not is_pagination_parameter(name)
    get = {"get": {"parameters": [{"name": name, "in": "query"}]}}
    assert check_pagination("/v1/users", get) == (
        ["⚠️ GET /v1/users does not support pagination parameters (e.g., `page`, `limit`)"],
        0.8,
    )
