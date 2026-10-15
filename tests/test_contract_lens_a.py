"""Contracts for the API and docs review: references, error types, compatible names."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from conftest import all_messages, document, write_json

import restful_checker
from restful_checker import analyze_api
from restful_checker.checks.content_type_checker import is_json_media_type
from restful_checker.checks.status_code_checker import covers
from restful_checker.engine.normalizer import normalize_paths


def test_parameter_schemas_given_by_reference_are_followed(tmp_path: Path) -> None:
    components = {
        "parameters": {"Status": {"name": "status", "in": "query",
                                  "schema": {"$ref": "#/components/schemas/State"}}},
        "schemas": {"State": {"type": "string"}},
    }  # fmt: skip
    get = {"parameters": [{"$ref": "#/components/parameters/Status"}], "responses": {}}
    doc = document({"/v1/users": {"get": get}}, components=components)
    ops = normalize_paths(doc)["/v1/users"]
    assert ops["get"]["parameters"][0]["schema"] == {"type": "string"}
    report = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path)["json_report"]
    assert not [m for m in all_messages(report, "Filters") if "no defined type" in m["message"]]


@pytest.mark.parametrize(
    ("name", "text", "message"),
    [
        ("bad.yaml", "openapi: 3.0.0\npaths: {\n  /a: [\n", "^bad.yaml is not valid YAML: "),
        ("list.yaml", "- a\n", "does not hold an OpenAPI document$"),
        ("str.json", '"str"', "does not hold an OpenAPI document$"),
        ("bad.json", "{", "Expecting property name"),
    ],
)
def test_unreadable_documents_raise_value_error(
    tmp_path: Path, name: str, text: str, message: str
) -> None:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        analyze_api(path, output_dir=tmp_path / "out")


def test_long_yaml_errors_are_cut() -> None:
    from restful_checker.engine.openapi_loader import _short

    assert _short(ValueError("a\n  b")) == "a b"
    cut = _short(ValueError("x" * 1000))
    assert len(cut) == 300 and cut.endswith("...")
    assert _short(ValueError("y" * 300)) == "y" * 300


NAMES_OF_3_1 = [
    ("restful_checker.checks.check_result", "linkify"),
    ("restful_checker.engine.analyzer", "generate_html"),
    ("restful_checker.engine.analyzer", "extract_json_from_html"),
    ("restful_checker.report.html_report", "extract_json_from_html"),
    ("restful_checker.main", "requests"),
    ("restful_checker.main", "yaml"),
    ("restful_checker.main", "tempfile"),
    ("restful_checker.main", "urlparse"),
]


@pytest.mark.parametrize(("module", "name"), NAMES_OF_3_1)
def test_names_of_3_1_stay_importable(module: str, name: str) -> None:
    assert hasattr(importlib.import_module(module), name)


def test_submodules_of_checks_stay_modules() -> None:
    from restful_checker.checks import check_error_format

    assert check_error_format.__name__ == "restful_checker.checks.check_error_format"


def test_the_package_lists_only_its_api() -> None:
    public = [name for name in dir(restful_checker) if not name.startswith("_")]
    assert public == ["analyze_api"]


def test_helpers_document_examples() -> None:
    for helper in (is_json_media_type, covers):
        assert ">>> " in (helper.__doc__ or "")
