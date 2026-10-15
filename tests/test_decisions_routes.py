"""The 3.2.0 decisions on servers, examples, versions and verbs in routes."""

from __future__ import annotations

from typing import Any

import pytest

from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.https_checker import check_https_usage, server_kind
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.response_example_checker import check_response_examples
from restful_checker.checks.version_checker import (
    VERSION_REGEX,
    check_resource_static_only,
    check_versioning,
)

MIXED = "✅ All servers use HTTPS or a URL relative to the document"
NONE = (["✅ No schemes listed: the API uses the scheme of the document"], 1.0)


def https(*servers: Any) -> tuple[list[str], float]:
    return check_https_usage({"openapi": "3.1.0", "servers": list(servers)})


@pytest.mark.parametrize(
    ("server", "kind"),
    [
        ({"url": "https://a"}, "secure"), ({"url": "HTTPS://a"}, "secure"),
        ({"url": "wss://a"}, "secure"), ({"url": "http://a"}, "insecure"),
        ({"url": "ws://a"}, "insecure"), ({"url": "https:/a"}, "insecure"),
        ({"url": "localhost:8080"}, "insecure"), ({"url": ""}, "insecure"), ({}, "insecure"),
        ("https://a", "insecure"), ({"url": 3}, "insecure"), ({"url": "/api"}, "relative"),
        ({"url": "//host/api"}, "relative"), ({"url": "api/v1"}, "relative"),
        ({"url": "/{base}"}, "relative"), ({"url": "https://{region}.a"}, "secure"),
        ({"url": "http://{region}.a"}, "insecure"), ({"url": "{scheme}://a"}, "unresolved"),
        ({"url": "{s}://a", "variables": {"s": {"default": "https"}}}, "secure"),
        ({"url": "{s}://a", "variables": {"s": {"default": "http"}}}, "insecure"),
        ({"url": "{s}://a", "variables": {"s": {"enum": ["https", "http"]}}}, "insecure"),
        ({"url": "{s}://a", "variables": {"s": {"enum": ["https"], "default": "http"}}}, "secure"),
        ({"url": "{s}://a", "variables": {"s": {"enum": [1], "default": "https"}}}, "secure"),
        ({"url": "{s}", "variables": {"s": {"enum": ["https://a", "/b"]}}}, "relative"),
        ({"url": "{s}://a", "variables": {"s": "https"}}, "unresolved"),
        ({"url": "{s}://a", "variables": []}, "unresolved"),
    ],
)  # fmt: skip
def test_server_kinds(server: Any, kind: str) -> None:
    assert server_kind(server) == kind


def test_server_messages() -> None:
    assert https({"url": "https://a"}) == (["✅ All servers use HTTPS"], 1.0)
    assert https({"url": "https://a"}, {"url": "/b"}) == ([MIXED], 1.0)
    assert https({"url": "/b"}) == ([MIXED], 1.0)
    unresolved = (["⚠️ A server URL uses a variable without a default or enum"], 0.8)
    assert https({"url": "https://a"}, {"url": "{x}://b"}) == unresolved
    assert https({"url": "{x}://b"}, {"url": "http://c"}) == (["❌ Not all servers use HTTPS"], 0.0)
    assert check_https_usage({"openapi": "3.0.3"}) == (
        ["⚠️ No servers defined in OpenAPI spec"],
        0.8,
    )


def test_many_variable_values_fall_back_to_the_defaults() -> None:
    variables = {f"v{i}": {"enum": ["a", "b", "c"], "default": "a"} for i in range(9)}
    url = "".join(f"{{v{i}}}" for i in range(9)) + "://x"
    assert server_kind({"url": url, "variables": variables}) == "insecure"  # `aaaaaaaaa`
    variables["v0"] = {"enum": ["https", "http", "x"], "default": "https"}
    variables.update({f"v{i}": {"enum": ["", "b", "c"], "default": ""} for i in range(1, 9)})
    assert server_kind({"url": url, "variables": variables}) == "secure"
    variables["v8"] = {"enum": ["", "b", "c"]}  # no default: the first enum value
    assert server_kind({"url": url, "variables": variables}) == "secure"


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        ({"swagger": "2.0"}, NONE),
        ({"swagger": "2.0", "schemes": []}, NONE),
        ({"swagger": "2.0", "schemes": "https"}, NONE),
        ({"swagger": "2.0", "schemes": ["HTTPS"]}, (["✅ All servers use HTTPS"], 1.0)),
        ({"swagger": "2.0", "schemes": ["https", "http"]}, (["❌ Not all servers use HTTPS"], 0.0)),
        ({"swagger": "2.0", "schemes": [None]}, (["❌ Not all servers use HTTPS"], 0.0)),
        ({"swagger": "2.0", "servers": []}, (["⚠️ No servers defined in OpenAPI spec"], 0.8)),
    ],
)  # fmt: skip
def test_swagger_2_is_judged_by_its_schemes(doc: dict[str, Any], expected: Any) -> None:
    assert check_https_usage(doc) == expected


def examples(media: dict[str, Any]) -> float:
    ops = {"get": {"responses": {"200": {"content": {"application/json": media}}}}}
    return check_response_examples("/v1/a", ops)[1]


def test_schema_level_examples_count() -> None:
    assert examples({"schema": {"example": {}}}) == 1.0
    assert examples({"schema": {"examples": [{}]}}) == 1.0
    assert examples({"schema": {"allOf": [{"type": "object"}, {"example": 1}]}}) == 1.0
    assert examples({"schema": {"properties": {"a": {"example": 1}}}}) == 0.8
    assert examples({"schema": "x"}) == 0.8


@pytest.mark.parametrize(
    "version", ["v1", "V2", "v1.2", "v1.0.3", "v1beta", "v1beta1", "v2alpha5", "V1BETA2"]
)
def test_version_segments(version: str) -> None:
    assert VERSION_REGEX.fullmatch(version)
    assert check_versioning(f"/{version}/users") == (["✅ Versioning detected"], 1.0)
    assert check_naming(f"/{version}/users") == (["✅ Resource naming looks RESTful"], 1.0)


@pytest.mark.parametrize("segment", ["v", "v1-beta", "version1", "v1.", "v1gamma", "1", "vbeta"])
def test_not_version_segments(segment: str) -> None:
    assert not VERSION_REGEX.fullmatch(segment)
    assert check_versioning(f"/{segment}/users")[1] == 0.0


def test_static_collections_are_not_warned() -> None:
    assert check_versioning("/v1/users/active") == (["✅ Versioning detected"], 1.0)
    result = CheckResult("versioning")  # the 3.1 helper still warns when called itself
    check_resource_static_only(["users"], result)
    assert result.messages == [
        "⚠️ Version segment exists but no dynamic resource parameter is found."
    ]


VERBS = ["get-users", "create-order", "delete-user", "update-profile", "fetch-items",
         "make-payment", "do-something", "add-item", "put-file", "addtocart", "additem",
         "dologin", "dosomething", "doaction", "addfavorite", "doIt", "add_item"]  # fmt: skip
NOUNS = ["add-ons", "add-on", "post-processing", "post-mortems", "documents", "domains",
         "downloads", "dogs", "doors", "donations", "dossiers", "dots", "doubles", "dozens",
         "dormitories", "addresses", "additions", "addons", "additives", "addenda", "adds",
         "posts", "makers", "updates", "dosages", "doses", "dolphins", "dolls", "donors",
         "doughnuts", "doves", "dojos", "addicts", "adders"]  # fmt: skip


@pytest.mark.parametrize("segment", VERBS)
def test_verb_segments_are_errors(segment: str) -> None:
    messages, score = check_naming(f"/v1/{segment}")
    assert f"❌ Contains verb-like segment: `{segment}`" in messages
    assert score == 0.0


@pytest.mark.parametrize("segment", NOUNS)
def test_nouns_are_not_verbs(segment: str) -> None:
    assert not any("verb" in m for m in check_naming(f"/v1/{segment}")[0])
