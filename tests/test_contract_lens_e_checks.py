"""Contracts found missing by a blind mutation round: checks and reports."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.content_type_checker import is_binary_media_type
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.https_checker import check_https_usage, server_kind
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.response_example_checker import check_response_examples
from restful_checker.checks.schema_tools import keyword
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.report.extract_json_from_html import extract_json_from_html
from restful_checker.report.html_report import render_message

# --- checks -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "/v1/removeUser",
            "❌ GET used for action-like path: `/v1/removeUser`, consider using POST",
        ),
        (
            "/v1/triggerBuild",
            "❌ GET used for side-effect path: `/v1/triggerBuild`, should be POST",
        ),
    ],
)
def test_get_verbs_remove_and_trigger(path: str, expected: str) -> None:
    assert any(m.startswith(expected) for m in check_http_methods(path, {"GET"})[0])


def test_post_with_an_id_anywhere_in_the_route_warns() -> None:
    messages = check_http_methods("/v1/users/{id}/orders", {"POST"})[0]
    assert messages == [
        "⚠️ POST used with resource ID in path `/v1/users/{id}/orders`, consider using PUT or PATCH"
    ]


def test_naming_generic_and_pascal_case() -> None:
    assert "⚠️ Segment `item` is too generic" in check_naming("/v1/item")[0]
    assert "⚠️ Segment `Data` is too generic" in check_naming("/v1/Data")[0]
    messages, score = check_naming("/v1/UserAccounts")
    assert "❌ PascalCase not recommended in URL segment: `UserAccounts`" in messages
    assert score == 0.0


def test_a_plural_word_before_a_hyphen_counts_as_plural() -> None:
    assert check_naming("/v1/orders-archive") == (["✅ Resource naming looks RESTful"], 1.0)


def test_pagination_reads_method_keys_in_any_case() -> None:
    assert check_pagination("/v1/users", {"GET": {}}) == (
        ["⚠️ GET /v1/users does not support pagination parameters (e.g., `page`, `limit`)"],
        0.8,
    )


def test_param_consistency_value_and_pascal_case() -> None:
    assert check_param_consistency({"/v1/things/{value}": {}})[0] == [
        "⚠️ Generic parameter name used: `value`, consider using more specific names"
    ]
    assert check_param_consistency({"/v1/a/{Order}": {}, "/v1/b/{order_id}": {}}) == (
        ["✅ Path parameters look consistent"],
        1.0,
    )


def _filters(*params: dict[str, Any]) -> list[str]:
    return check_query_filters("/v1/users", {"get": {"parameters": list(params)}})[0]


def test_query_filters_rules() -> None:
    typed = {"type": "string"}
    assert _filters({"name": "status", "in": "header", "schema": typed}) == [
        "⚠️ GET collection endpoint `/v1/users` has no query filters, consider supporting "
        "`?filter=` or `?status=`"
    ]
    ok = ["✅ Collection endpoints support query filters"]
    assert _filters({"name": "sort", "in": "query", "schema": typed}) == ok
    assert _filters({"name": "filterx", "in": "query", "schema": typed}) == [
        "⚠️ GET /v1/users has query params but none look like useful filters (e.g., `filter`, "
        "`status`)"
    ]
    untyped = _filters({"name": "status", "in": "query", "schema": {"oneOf": []}})
    assert untyped == ["⚠️ Query parameter `status` has no defined type"]


def test_examples_warn_once_and_skip_empty_content() -> None:
    body: dict[str, Any] = {"content": {"application/json": {}}}
    messages = check_response_examples("/v1/u", {"get": {"responses": {200: body, "200": body}}})[0]
    assert messages == ["⚠️ GET /v1/u response 200 is missing example or examples"]
    empty: dict[str, Any] = {"get": {"responses": {"200": {"content": {}}}}}
    assert check_response_examples("/v1/u", empty) == (
        ["✅ No response bodies to evaluate for examples"],
        1.0,
    )


def test_post_expects_409() -> None:
    assert check_status_codes("/v1/u", {"post": {"responses": {"201": {}, "400": {}}}})[0] == [
        "⚠️ POST /v1/u is missing expected status codes: 409"
    ]


def test_missing_status_codes_are_listed_sorted_whatever_the_hash_seed() -> None:
    code = (
        "from restful_checker.checks.status_code_checker import check_status_codes as c;"
        "print(c('/v1/u', {'post': {'responses': {'500': {}}}})[0][0])"
    )
    for seed in range(8):
        env = dict(os.environ, PYTHONHASHSEED=str(seed), PYTHONIOENCODING="utf-8")
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True)
        assert out.stdout.decode("utf-8").strip().endswith("codes: 201, 400, 409"), seed


def test_error_bodies_with_empty_properties_are_structured_but_incomplete() -> None:
    schema = {"type": "object", "properties": {}}
    methods = {"get": {"responses": {"404": {"content": {"application/json": {"schema": schema}}}}}}
    assert check_error_format("/v1/u", methods)[0] == [
        "⚠️ GET /v1/u error 404 should include 'code' and 'message' fields or RFC 9457 problem "
        "details members"
    ]


def test_server_variable_combinations_limit_and_defaults() -> None:
    hosts = {"default": "h0", "enum": [f"h{i}" for i in range(128)]}
    url = "{scheme}://{host}.example.com"
    both = {"default": "https", "enum": ["https", "http"]}
    assert server_kind({"url": url, "variables": {"scheme": both, "host": hosts}}) == "insecure"
    many = {"default": "h0", "enum": [f"h{i}" for i in range(129)]}
    first_http = {"default": "https", "enum": ["http", "https"]}
    variables = {"scheme": first_http, "host": many}  # 258 combinations: defaults only
    assert server_kind({"url": url, "variables": variables}) == "secure"


def test_swagger_schemes_only_on_operations() -> None:
    doc = {"swagger": "2.0", "paths": {"/a": {"get": {"schemes": ["https"]}}}}
    assert check_https_usage(doc) == (
        ["✅ No schemes listed: the API uses the scheme of the document"],
        1.0,
    )


def test_binary_needs_string_type_and_raw_contents_no_encoding() -> None:
    encoded = {"schema": {"contentMediaType": "image/png", "contentEncoding": "base64"}}
    assert is_binary_media_type("application/x-custom", encoded) is False
    assert is_binary_media_type("application/x-custom", {"schema": {"format": "binary"}}) is False


def test_keyword_reads_all_of_members_in_document_order() -> None:
    assert keyword({"allOf": [{"type": "string"}, {"type": "object"}]}, "type") == "string"


# --- reports ------------------------------------------------------------------------------


def test_server_problems_link_to_their_best_practice() -> None:
    html = render_message("⚠️ No servers defined in OpenAPI spec", "Servers")
    assert 'href="https://restfulapi.net/security-essentials/"' in html


def test_reading_back_titles_and_missing_scores(tmp_path: Path) -> None:
    page = tmp_path / "r.html"
    page.write_text(
        "<div class='section'><h2>🟢 /v1/users <span class='score-inline'>n/a</span></h2></div>"
        "<div class='section'><h2>🟢 /v1/a (x) b (80%)</h2></div>",
        encoding="utf-8",
    )
    sections = extract_json_from_html(page)["sections"]
    assert (sections[0]["path"], sections[0]["score"]) == ("/v1/users", 100)
    assert (sections[1]["path"], sections[1]["score"]) == ("/v1/a b", 80)
