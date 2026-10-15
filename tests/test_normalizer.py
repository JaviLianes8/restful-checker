"""The Paths Object is read as the OpenAPI specification defines it."""

from __future__ import annotations

import copy
from typing import Any

from restful_checker.engine.normalizer import OPERATION_KEYS, normalize_paths, resolve


def test_only_operation_fields_are_methods() -> None:
    item = {
        "summary": "s",
        "description": "d",
        "servers": [{"url": "https://x"}],
        "parameters": [{"name": "id", "in": "path"}],
        "x-internal": True,
        "get": {"responses": {}},
        "query": {"responses": {}},
    }
    assert set(normalize_paths({"paths": {"/a/{id}": item}})["/a/{id}"]) == {"get", "query"}


def test_every_operation_key_is_read() -> None:
    item: dict[str, Any] = {key: {"responses": {}} for key in OPERATION_KEYS}
    assert list(normalize_paths({"paths": {"/a": item}})["/a"]) == list(OPERATION_KEYS)


def test_additional_operations_keep_their_name() -> None:
    item = {"get": {}, "additionalOperations": {"COPY": {}, "get": {"summary": "dup"}}}
    ops = normalize_paths({"paths": {"/a": item}})["/a"]
    assert set(ops) == {"get", "COPY"}
    assert "summary" not in ops["get"]


def test_extension_keys_of_paths_are_not_paths() -> None:
    result = normalize_paths({"paths": {"x-tag": {"get": {}}, "/a": {"get": {}}}})
    assert list(result) == ["/a"]


def test_missing_or_broken_paths_give_nothing() -> None:
    assert normalize_paths({}) == {}
    assert normalize_paths({"paths": None}) == {}
    assert normalize_paths({"paths": []}) == {}
    assert normalize_paths([]) == {}
    assert normalize_paths({"paths": {"/a": None}}) == {"/a": {}}
    assert normalize_paths({"paths": {"/a": {"get": "nope"}}}) == {"/a": {}}


def test_status_codes_become_strings() -> None:
    ops = normalize_paths({"paths": {"/a": {"get": {"responses": {200: {}, "default": {}}}}}})
    assert list(ops["/a"]["get"]["responses"]) == ["200", "default"]


def test_path_level_parameters_are_merged_and_overridden() -> None:
    item = {
        "parameters": [
            {"name": "page", "in": "query", "description": "shared"},
            {"name": "id", "in": "path"},
        ],
        "get": {"parameters": [{"name": "page", "in": "query", "description": "own"}]},
        "post": {},
    }
    ops = normalize_paths({"paths": {"/a/{id}": item}})["/a/{id}"]
    assert ops["get"]["parameters"] == [
        {"name": "id", "in": "path"},
        {"name": "page", "in": "query", "description": "own"},
    ]
    assert [p["name"] for p in ops["post"]["parameters"]] == ["page", "id"]


def test_same_name_in_other_location_is_not_an_override() -> None:
    item = {
        "parameters": [{"name": "id", "in": "header"}],
        "get": {"parameters": [{"name": "id", "in": "query"}]},
    }
    params = normalize_paths({"paths": {"/a": item}})["/a"]["get"]["parameters"]
    assert len(params) == 2


def test_operation_without_parameters_gets_none_added() -> None:
    assert "parameters" not in normalize_paths({"paths": {"/a": {"get": {}}}})["/a"]["get"]


def test_local_references_are_followed() -> None:
    doc: dict[str, Any] = {
        "paths": {
            "/a": {"$ref": "#/x-items/a"},
        },
        "x-items": {
            "a": {
                "get": {
                    "parameters": [{"$ref": "#/components/parameters/page"}],
                    "requestBody": {"$ref": "#/components/requestBodies/b"},
                    "responses": {"200": {"$ref": "#/components/responses/ok"}},
                }
            }
        },
        "components": {
            "parameters": {"page": {"name": "page", "in": "query"}},
            "requestBodies": {"b": {"content": {"application/json": {}}}},
            "responses": {
                "ok": {"content": {"application/json": {"schema": {"$ref": "#/c/s"}}}},
            },
        },
        "c": {"s": {"properties": {"code": {}}}},
    }
    original = copy.deepcopy(doc)
    get = normalize_paths(doc)["/a"]["get"]
    assert get["parameters"] == [{"name": "page", "in": "query"}]
    assert get["requestBody"] == {"content": {"application/json": {}}}
    schema = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema == {"properties": {"code": {}}}
    assert doc == original


def test_responses_object_given_as_reference() -> None:
    doc = {"paths": {"/a": {"get": {"responses": {"$ref": "#/r"}}}}, "r": {"204": {}}}
    assert normalize_paths(doc)["/a"]["get"]["responses"] == {"204": {}}


def test_content_that_is_not_a_map_is_kept() -> None:
    doc = {"paths": {"/a": {"get": {"responses": {"200": {"content": "text"}}}}}}
    assert normalize_paths(doc)["/a"]["get"]["responses"]["200"] == {"content": "text"}


def test_media_type_given_as_reference_and_without_schema() -> None:
    doc = {
        "paths": {"/a": {"get": {"responses": {"200": {"content": {"a/b": {"$ref": "#/m"}}}}}}},
        "m": {"example": 1},
    }
    content = normalize_paths(doc)["/a"]["get"]["responses"]["200"]["content"]
    assert content == {"a/b": {"example": 1}}


def test_reference_chains_cycles_and_dead_ends() -> None:
    root = {"a": {"$ref": "#/b"}, "b": {"$ref": "#/c"}, "c": {"ok": 1}, "x": {"$ref": "#/x"}}
    assert resolve({"$ref": "#/a"}, root) == {"ok": 1}
    assert resolve({"$ref": "#/x"}, root) == {"$ref": "#/x"}
    assert resolve({"$ref": "#/missing"}, root) == {"$ref": "#/missing"}
    assert resolve({"$ref": "other.yaml#/a"}, root) == {"$ref": "other.yaml#/a"}
    assert resolve({"$ref": 5}, root) == {"$ref": 5}
    assert resolve([1], root) == [1]


def test_long_reference_chain_stops() -> None:
    root: dict[str, Any] = {f"r{i}": {"$ref": f"#/r{i + 1}"} for i in range(40)}
    root["r40"] = {"end": True}
    assert resolve({"$ref": "#/r0"}, root) != {"end": True}
    assert resolve({"$ref": "#/r10"}, root) == {"end": True}


def test_pointer_unescapes_tilde_one_before_tilde_zero() -> None:
    # RFC 6901: "~01" names the key "~1", not "/".
    root = {"a~1b": 1, "a/b": 2}
    assert resolve({"$ref": "#/a~01b"}, root) == 1


def test_operation_keys_in_capitals_are_still_read() -> None:
    assert list(normalize_paths({"paths": {"/a": {"GET": {}}}})["/a"]) == ["GET"]


def test_json_pointer_escapes_and_arrays() -> None:
    root = {"paths": {"/a/b": {"get": 1}}, "t~n": [10, 20], "%": 3}
    assert resolve({"$ref": "#/paths/~1a~1b/get"}, root) == 1
    assert resolve({"$ref": "#/t~0n/1"}, root) == 20
    assert resolve({"$ref": "#/t~0n/2"}, root) == {"$ref": "#/t~0n/2"}
    assert resolve({"$ref": "#/%25"}, root) == 3
    assert resolve({"$ref": "#"}, {"$ref": "#"}) == {"$ref": "#"}
    assert resolve({"$ref": "#"}, {"k": 1}) == {"k": 1}
