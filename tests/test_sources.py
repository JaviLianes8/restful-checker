"""The spec reading is checked against the pinned specification files.

The files are fetched by scripts/fetch_upstream.py (see tests/upstream/MANIFEST.json); these
tests skip while they are absent.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from conftest import upstream

from restful_checker.checks.content_type_checker import is_json_media_type
from restful_checker.engine.normalizer import OPERATION_KEYS, normalize_paths

OAS3 = ["oas-3.0.4.md", "oas-3.1.2.md", "oas-3.2.1.md"]


def operation_fields(text: str) -> set[str]:
    """Path Item fields whose type is a single Operation Object."""
    item = text[text.index("Path Item Object") :]
    item = item[: item.index("Operation Object\n")]
    row = re.compile(r'<a name="path-?item-?[\w-]*"></a>(\w+) \| \[Operation Object\]', re.I)
    return {match.group(1) for match in row.finditer(item)}


def test_operation_keys_match_openapi_3_2() -> None:
    assert operation_fields(upstream("oas-3.2.1.md")) == set(OPERATION_KEYS)


@pytest.mark.parametrize("name", ["oas-3.0.4.md", "oas-3.1.2.md"])
def test_operation_keys_cover_openapi_3_0_and_3_1(name: str) -> None:
    assert operation_fields(upstream(name)) == set(OPERATION_KEYS) - {"query"}


def test_operation_keys_cover_swagger_2() -> None:
    assert operation_fields(upstream("oas-2.0.md")) == set(OPERATION_KEYS) - {"query", "trace"}


def test_additional_operations_field_is_read() -> None:
    text = upstream("oas-3.2.1.md")
    assert '<a name="path-item-additional-operations"></a>additionalOperations' in text
    item: dict[str, Any] = {"additionalOperations": {"COPY": {}}}
    assert list(normalize_paths({"paths": {"/a": item}})["/a"]) == ["COPY"]


@pytest.mark.parametrize("name", [*OAS3, "oas-2.0.md"])
def test_paths_start_with_a_slash_and_extensions_are_skipped(name: str) -> None:
    text = upstream(name)
    assert re.search(r"The field name MUST begin with a (forward )?slash", text)
    assert "^x-" in text
    assert list(normalize_paths({"paths": {"x-a": {}, "/a": {}}})) == ["/a"]


@pytest.mark.parametrize("name", [*OAS3, "oas-2.0.md"])
def test_path_level_parameters_apply_to_every_operation(name: str) -> None:
    text = upstream(name)
    assert "applicable for all the operations described under this path" in text
    assert "can be overridden at the operation level, but cannot be removed there" in text
    item = {"parameters": [{"name": "page", "in": "query"}], "get": {}, "put": {}}
    ops = normalize_paths({"paths": {"/a": item}})["/a"]
    assert ops["get"]["parameters"] == ops["put"]["parameters"] == item["parameters"]


@pytest.mark.parametrize("name", OAS3)
def test_status_codes_are_strings(name: str) -> None:
    text = upstream(name)
    # 3.0 and 3.1 say "enclosed in quotation marks", 3.2 "represented by a string".
    wording = r"MUST be (enclosed in quotation marks|represented by a string)"
    assert re.search(wording + r' \(for example, `?"200"', text)
    ops = normalize_paths({"paths": {"/a": {"get": {"responses": {200: {}}}}}})
    assert list(ops["/a"]["get"]["responses"]) == ["200"]


def test_rfc_9110_methods_are_operation_keys() -> None:
    text = upstream("rfc9110.txt")
    assert "The method token is case-sensitive" in text
    table = text[text.index("   | Method  | Description") :]
    registered = set(re.findall(r"^   \| ([A-Z]+) +\|", table[:2500], re.M))
    assert registered == {"GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE"}
    # CONNECT has no Path Item field; PATCH comes from RFC 5789, QUERY from RFC 10008
    # by way of OpenAPI 3.2.
    assert {m.lower() for m in registered} - {"connect"} < set(OPERATION_KEYS)


def test_json_suffix_media_types() -> None:
    assert "3.1.  The +json Structured Syntax Suffix" in upstream("rfc6839.txt")
    assert '"application/problem+json"' in upstream("rfc9457.txt")
    assert is_json_media_type("application/problem+json")


def test_byte_order_mark_may_be_ignored() -> None:
    text = " ".join(upstream("rfc8259.txt").split())
    assert "MAY ignore the presence of a byte order mark" in text
