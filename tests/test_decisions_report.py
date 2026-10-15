"""Plain-text messages, the JSON report built from data, the light import, deep documents."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import all_messages, document, ok_operation, write_json

from restful_checker import analyze_api
from restful_checker.checks.naming_checker import check_naming
from restful_checker.engine.openapi_loader import load_openapi
from restful_checker.report.extract_json_from_html import extract_json_from_html
from restful_checker.report.html_report import generate_html, render_message
from restful_checker.report.json_report import build_json_report

ROOT = Path(__file__).resolve().parents[1]
ODD = "/v1/<b>&'\"x"


def test_checker_messages_are_plain_text() -> None:
    messages, _ = check_naming("/v1/<data>")
    assert messages == ["⚠️ Last segment `<data>` might not be plural (use plural for collections)"]


def test_html_escapes_and_links_problems_only() -> None:
    assert render_message("❌ a<b", "Naming") == (
        '❌ a&lt;b <a href="https://restfulapi.net/resource-naming/" target="_blank">More info</a>'
    )
    assert render_message("✅ a<b", "Naming") == "✅ a&lt;b"
    assert render_message("⚠️ a", "Unknown section") == "⚠️ a"
    assert render_message("Routes: /a<b>", None) == "<strong>Routes:</strong> /a&lt;b&gt;"
    assert render_message("HTTP methods: GET", None) == "<strong>HTTP methods:</strong> GET"
    assert render_message("other <x>", None) == "other &lt;x&gt;"


def test_reports_from_a_spec_with_markup(tmp_path: Path) -> None:
    doc = document({ODD: {"get": ok_operation("200", "404")}})
    result = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path / "out")
    report = result["json_report"]
    texts = [m["message"] for m in all_messages(report)]
    assert any(ODD in text for text in texts)
    assert not any("&lt;" in text or "&#x27;" in text or "More info" in text for text in texts)
    page = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "<b>&" not in page and "/v1/&lt;b&gt;&amp;&#x27;&quot;x" in page
    assert json.loads(Path(result["json_path"]).read_text(encoding="utf-8")) == report
    assert extract_json_from_html(result["html_path"]) == report


def test_json_lists_errors_then_warnings_then_the_rest() -> None:
    block = {"title": "/v1/a", "score": 0.5, "items": ["Routes: /v1/a", "HTTP methods: GET, PUT",
             "### X", "✅ fine", "⚠️ meh", "❌ bad", "note"]}  # fmt: skip
    data = build_json_report([block], 50, "now")
    assert data == {
        "title": "RESTful API Report",
        "score": 50,
        "generated": "now",
        "sections": [{"score": 50, "items": [{"category": "X", "messages": [
            {"message": "bad", "level": "error"}, {"message": "meh", "level": "warn"},
            {"message": "fine", "level": "info"}, {"message": "note", "level": "info"}]}],
            "path": "/v1/a", "httpMethods": ["GET", "PUT"]}],
    }  # fmt: skip


def test_global_sections_and_plain_items(tmp_path: Path) -> None:
    report = [{"title": "Global Parameter Consistency", "items": ["### Parameters", "✅ <ok>"],
               "score": 1.0}]  # fmt: skip
    out = Path(generate_html(report, 100, output=tmp_path / "r.html"))
    assert "<li>✅ &lt;ok&gt;</li>" in out.read_text(encoding="utf-8")
    data = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert data["sections"] == [
        {"score": 100, "items": [{"category": "Parameters", "messages": [
            {"message": "<ok>", "level": "info"}]}], "section": "Global Parameter Consistency"}
    ]  # fmt: skip


def run_python(code: str) -> str:
    done = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def test_import_is_light_and_analyze_api_loads_on_use() -> None:
    code = (
        "import sys, restful_checker as r\n"
        "heavy = ('restful_checker.engine.analyzer', 'yaml', 'requests', 'bs4')\n"
        "print([m for m in heavy if m in sys.modules])\n"
        "f = r.analyze_api\n"
        "print(f.__module__, 'analyze_api' in dir(r), 'bs4' in sys.modules)"
    )
    assert run_python(code).splitlines() == ["[]", "restful_checker.engine.analyzer True False"]


def test_unknown_attributes_still_raise() -> None:
    import restful_checker

    with pytest.raises(AttributeError, match="has no attribute 'nope'"):
        restful_checker.nope  # noqa: B018


def nested(depth: int) -> str:
    return '{"openapi": "3.0.3", "paths": {}, "x": ' + "[" * depth + "]" * depth + "}"


DEEP = {"deep.json": nested(100_000), "deep.yaml": "openapi: 3.0.3\nx: " + "[" * 100_000}


@pytest.mark.parametrize("name", sorted(DEEP))
def test_deep_documents_raise_a_clear_error(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_text(DEEP[name], encoding="utf-8")
    with pytest.raises(ValueError, match=f"^{name} is nested too deeply to read$"):
        load_openapi(path)
    with pytest.raises(ValueError, match="nested too deeply"):
        analyze_api(path, output_dir=tmp_path / "out")


def test_deep_documents_on_the_command_line(tmp_path: Path) -> None:
    path = tmp_path / "deep.json"
    path.write_text(nested(100_000), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-m", "restful_checker", str(path), "--output-folder", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )  # fmt: skip
    assert done.returncode == 1
    assert "deep.json is nested too deeply to read" in done.stdout
    assert "Traceback" not in done.stdout + done.stderr


def test_all_of_cycles_and_fan_out_stay_bounded(tmp_path: Path) -> None:
    schemas: dict[str, Any] = {"A": {"allOf": [{"$ref": "#/components/schemas/B"}]},
                               "B": {"allOf": [{"$ref": "#/components/schemas/A"}]}}  # fmt: skip
    for level in range(40):  # each level refers twice to the next: 2**40 paths unbounded
        nxt = {"$ref": f"#/components/schemas/L{level + 1}"}
        schemas[f"L{level}"] = {"allOf": [nxt, nxt]}
    schemas["L40"] = {"properties": {"code": {}, "message": {}}}
    get = ok_operation("200", "404")
    for code, name in (("404", "A"), ("400", "L0")):
        media = {"schema": {"$ref": f"#/components/schemas/{name}"}, "example": {}}
        get["responses"][code] = {"content": {"application/json": media}}
    doc = document({"/v1/users": {"get": get}}, components={"schemas": schemas})
    report = analyze_api(write_json(tmp_path, doc), output_dir=tmp_path / "o")["json_report"]
    texts = [m["message"] for m in all_messages(report, "Error Format")]
    assert texts == ["GET /v1/users error 404 has no structured schema"]
