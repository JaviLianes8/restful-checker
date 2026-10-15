"""Each 3.2.0 rule is checked against the pinned source it rests on.

The sources are fetched by scripts/fetch_upstream.py (see tests/upstream/MANIFEST.json);
these tests skip while they are absent. The quoted fragments are short facts checked in the
fetched text, not copies of it.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from conftest import upstream

from restful_checker.checks.check_error_format import PROBLEM_MEMBERS, check_error_format
from restful_checker.checks.content_type_checker import is_binary_media_type
from restful_checker.checks.http_method_checker import VALID_METHODS, check_http_methods
from restful_checker.checks.https_checker import check_https_usage, server_kind
from restful_checker.checks.pagination_checker import is_pagination_parameter
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.version_checker import VERSION_REGEX
from restful_checker.engine.normalizer import OPERATION_KEYS

OAS3 = ["oas-3.0.4.md", "oas-3.1.2.md", "oas-3.2.1.md"]


@pytest.mark.parametrize("name", OAS3)
def test_status_code_ranges(name: str) -> None:
    text = upstream(name)
    assert "Only the following range definitions are allowed: `1XX`, `2XX`, `3XX`, `4XX`" in text
    assert "explicit code definition takes precedence over the range definition" in text
    get: dict[str, Any] = {"get": {"responses": {"2XX": {}, "4XX": {}}}}
    assert check_status_codes("/v1/users", get)[1] == 1.0
    post: dict[str, Any] = {"post": {"responses": {"200": {}, "2XX": {}, "400": {}, "409": {}}}}
    assert check_status_codes("/v1/users", post) == (["✅ Status code definitions look valid"], 1.0)


def test_methods_registered_by_rfc_9110_and_openapi_3_2_are_usual() -> None:
    table = upstream("rfc9110.txt")
    for method in ("HEAD", "OPTIONS", "TRACE"):
        assert re.search(rf"^   \| {method} +\|", table, re.M)
    assert "query" in OPERATION_KEYS and "QUERY" in VALID_METHODS
    usual = {"GET", "HEAD", "OPTIONS", "TRACE", "QUERY"}
    assert check_http_methods("/v1/users", usual) == (["✅ HTTP method usage looks valid"], 1.0)


@pytest.mark.parametrize("name", OAS3)
def test_relative_servers_and_the_default_server(name: str) -> None:
    text = upstream(name)
    assert "MAY be relative, to indicate that the host location is relative" in text
    assert "If the `servers` field is not provided, or is an empty array" in text
    assert server_kind({"url": "/v1"}) == "relative"
    assert check_https_usage({"servers": [{"url": "/v1"}]})[1] == 1.0


@pytest.mark.parametrize("name", OAS3)
def test_server_variables_are_substituted(name: str) -> None:
    text = upstream(name)
    assert "Variable substitutions will be made when a variable is named in `{`braces`}`" in text
    variables = {"scheme": {"enum": ["https", "http"], "default": "https"}}
    assert server_kind({"url": "{scheme}://h", "variables": variables}) == "insecure"
    assert server_kind({"url": "{scheme}://h", "variables": {"scheme": {"default": "https"}}}) == (
        "secure"
    )


def test_swagger_2_schemes() -> None:
    text = upstream("oas-2.0.md")
    assert "If the `schemes` is not included, the default scheme to be used is the one" in text
    assert re.search(r'list: `"http"`, `"https"`, `"ws"`, `"wss"`', text)
    assert check_https_usage({"swagger": "2.0"})[1] == 1.0
    assert check_https_usage({"swagger": "2.0", "schemes": ["https", "wss"]})[1] == 1.0
    assert check_https_usage({"swagger": "2.0", "schemes": ["https", "ws"]})[1] == 0.0


def test_problem_details_members() -> None:
    text = upstream("rfc9457.txt")
    members = set(re.findall(r'^3\.1\.\d\.  "(\w+)"$', text, re.M))
    assert members == PROBLEM_MEMBERS
    assert '"application/problem+json"' in text
    schema: dict[str, Any] = {"properties": {"type": {}, "title": {}, "status": {}, "detail": {}}}
    media = {"application/json": {"schema": schema}}
    assert check_error_format("/a", {"get": {"responses": {"404": {"content": media}}}})[1] == 1.0


@pytest.mark.parametrize("name", ["oas-3.0.4.md", "oas-3.1.2.md", "oas-3.2.1.md"])
def test_binary_and_multipart_bodies(name: str) -> None:
    text = upstream(name)
    assert "multipart/form-data" in text and "application/octet-stream" in text
    assert is_binary_media_type("multipart/form-data")
    assert is_binary_media_type("application/octet-stream")


def test_openapi_3_0_binary_schema() -> None:
    text = upstream("oas-3.0.4.md")
    assert re.search(r"type: string\n\s+format: binary", text)
    binary = {"schema": {"type": "string", "format": "binary"}}
    assert is_binary_media_type("text/plain", binary)


def test_json_api_page_family() -> None:
    text = upstream("jsonapi-1.1.md")
    assert "The `page` [query parameter family] is reserved for pagination." in text
    for name in re.findall(r"`(page\[\w+\])`", text):
        assert is_pagination_parameter(name), name


def test_versions_named_by_aip_185() -> None:
    text = upstream("aip-185.md")
    versions = set(re.findall(r"`(v\d[\w.]*)`", text))
    assert {"v1", "v1.0", "v1.4.2", "v1beta", "v1alpha", "v1beta1", "v1alpha5"} <= versions
    for version in versions:
        assert VERSION_REGEX.fullmatch(version), version
