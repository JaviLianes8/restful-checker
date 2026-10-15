"""Contracts for the ground-truth review: nested servers, pointers, 3.1 schemas, media types."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from conftest import all_messages, document, write_json

from restful_checker import analyze_api
from restful_checker.checks.check_error_format import is_structured_error
from restful_checker.checks.content_type_checker import is_binary_media_type, is_json_media_type
from restful_checker.checks.https_checker import check_https_usage
from restful_checker.engine.normalizer import resolve

ERROR = (["❌ Not all servers use HTTPS"], 0.0)
HTTPS = (["✅ All servers use HTTPS"], 1.0)


def oas3(item: dict[str, Any], servers: Any = "keep") -> dict[str, Any]:
    doc = document({"/v1/a": item})  # top-level servers: https://api.example.com
    if servers is None:
        del doc["servers"]
    elif servers != "keep":
        doc["servers"] = servers
    return doc


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        (oas3({"servers": [{"url": "http://a"}], "get": {}}), ERROR),
        (oas3({"get": {"servers": [{"url": "http://a"}]}}), ERROR),
        (oas3({"additionalOperations": {"COPY": {"servers": [{"url": "http://a"}]}}}), ERROR),
        (oas3({"get": {"servers": [{"url": "http://a"}]}}, servers=None), ERROR),
        (oas3({"get": {"servers": [{"url": "https://b"}]}}), HTTPS),
        (oas3({"get": {"servers": [{"url": "/b"}]}}),
         (["✅ All servers use HTTPS or a URL relative to the document"], 1.0)),
        (oas3({"get": {"servers": [{"url": "https://b"}]}}, servers=[]),
         (["⚠️ No servers defined in OpenAPI spec"], 0.8)),
        ({"swagger": "2.0", "schemes": ["https"], "paths": {"/a": {"get": {"schemes": ["http"]}}}},
         ERROR),
        ({"swagger": "2.0", "paths": {"/a": {"get": {"schemes": ["ws"]}}}}, ERROR),
        ({"swagger": "2.0", "schemes": ["https"], "paths": {"/a": {"get": {"schemes": ["wss"]}}}},
         HTTPS),
    ],
)  # fmt: skip
def test_servers_and_schemes_of_paths_and_operations(doc: Any, expected: Any) -> None:
    assert check_https_usage(doc) == expected


def test_referenced_path_items_and_operations_are_read() -> None:
    doc = oas3({"$ref": "#/x-item"})
    doc["x-item"] = {"get": {"$ref": "#/x-op"}}
    doc["x-op"] = {"servers": [{"url": "http://a"}]}
    assert check_https_usage(doc) == ERROR


def test_pointers_follow_rfc_6901() -> None:
    root = {"a": {"b": 1}, "a/b": 2, "l": ["x", "y"], "~": 3}
    assert resolve({"$ref": "#/a%2Fb"}, root) == 1  # decoded before it is split
    assert resolve({"$ref": "#/a~1b"}, root) == 2
    assert resolve({"$ref": "#/~0"}, root) == 3
    assert resolve({"$ref": "#/l/1"}, root) == "y"
    for bad in ("#/l/01", "#/l/١", "#/l/-1", "#/l/2"):
        assert resolve({"$ref": bad}, root) == {"$ref": bad}


def report(tmp_path: Path, version: str, schema: dict[str, Any]) -> list[str]:
    media = {"application/json": {"schema": schema}}
    get = {"responses": {"200": {"content": media}, "404": {"content": media}}}
    components = {"schemas": {"Base": {"type": "object"}}}
    doc = document({"/v1/users": {"get": get}}, components=components, openapi=version)
    result = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path)["json_report"]
    return [m["message"] for m in all_messages(result) if m["level"] == "warn"]


SIBLINGS = {"$ref": "#/components/schemas/Base", "examples": [{}],
            "properties": {"code": {}, "message": {}}}  # fmt: skip


@pytest.mark.parametrize("version", ["3.1.0", "3.2.0"])
def test_keywords_next_to_a_ref_apply_from_3_1(tmp_path: Path, version: str) -> None:
    warnings = report(tmp_path, version, SIBLINGS)
    assert not [w for w in warnings if "example" in w or "error 404" in w]


def test_keywords_next_to_a_ref_are_ignored_in_3_0(tmp_path: Path) -> None:
    warnings = report(tmp_path, "3.0.3", SIBLINGS)
    assert "GET /v1/users error 404 has no structured schema" in warnings
    assert any("response 200 is missing example" in w for w in warnings)


def test_sequential_and_binary_media_types() -> None:
    for name in ("application/jsonl", "application/x-ndjson", "application/json-seq",
                 "application/geo+json-seq"):  # fmt: skip
        assert is_json_media_type(name)
    assert not is_json_media_type("text/event-stream")
    assert is_binary_media_type("application/epub+zip")
    sheet = {"schema": {"contentMediaType": "application/vnd.ms-excel"}}
    assert is_binary_media_type("application/vnd.ms-excel", sheet)
    encoded = {"schema": {"contentMediaType": "image/png", "contentEncoding": "base64"}}
    assert not is_binary_media_type("text/plain", encoded)
    assert is_structured_error("application/problem+xml", None)


def test_item_schema_examples_count(tmp_path: Path) -> None:
    media = {"application/jsonl": {"itemSchema": {"$ref": "#/components/schemas/E"}}}
    doc = document({"/v1/events": {"get": {"responses": {"200": {"content": media}}}}},
                   components={"schemas": {"E": {"examples": [{}]}}}, openapi="3.2.0")  # fmt: skip
    result = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path)["json_report"]
    texts = {m["message"] for m in all_messages(result, "Response Examples")}
    assert texts == {"All responses define at least one example"}
    content = {m["message"] for m in all_messages(result, "Content Types")}
    assert content == {"All request and response bodies use application/json"}


@pytest.mark.parametrize("name", ["filter[author]", "FILTER[x]", "filter[]"])
def test_json_api_filter_family(tmp_path: Path, name: str) -> None:
    params = [{"name": name, "in": "query", "schema": {"type": "string"}}]
    doc = document({"/v1/posts": {"get": {"parameters": params, "responses": {}}}})
    result = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path)["json_report"]
    texts = [m["message"] for m in all_messages(result, "Filters")]
    assert texts == ["Collection endpoints support query filters"]
