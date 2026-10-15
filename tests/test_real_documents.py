"""Real public OpenAPI documents, fetched by scripts/fetch_upstream.py (not committed).

Each expectation below was read from the fetched document; the tests skip while the
documents are absent.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from conftest import UPSTREAM, all_messages

from restful_checker import analyze_api
from restful_checker.report.extract_json_from_html import extract_json_from_html

DOCUMENTS = sorted(
    name
    for name, entry in json.loads((UPSTREAM / "MANIFEST.json").read_text("utf-8")).items()
    if name.startswith(("oai-", "github-"))
)


def analyzed(name: str, tmp_path: Path) -> dict[str, Any]:
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run python scripts/fetch_upstream.py")
    return analyze_api(path, output_dir=tmp_path)


def servers(report: dict[str, Any]) -> list[str]:
    return [m["message"] for m in all_messages(report, "Servers")]


@pytest.mark.parametrize("name", DOCUMENTS)
def test_every_document_is_analyzed_and_both_reports_agree(name: str, tmp_path: Path) -> None:
    result = analyzed(name, tmp_path)
    report = result["json_report"]
    assert json.loads(Path(result["json_path"]).read_text("utf-8")) == report
    assert extract_json_from_html(result["html_path"]) == report
    assert 0 <= report["score"] <= 100
    for message in all_messages(report):
        assert message["level"] in ("error", "warn", "info")
        assert "&#x27;" not in message["message"] and "<a " not in message["message"]
    assert not [m for m in all_messages(report) if "Unusual HTTP method" in m["message"]]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("oai-2.0-petstore.yaml", "Not all servers use HTTPS"),  # schemes: [http]
        ("oai-2.0-uber.json", "All servers use HTTPS"),  # schemes: [https]
        ("oai-3.0-petstore.yaml", "Not all servers use HTTPS"),  # http://petstore.swagger.io/v1
        ("oai-3.0-uspto.yaml", "Not all servers use HTTPS"),  # {scheme}, enum [https, http]
        ("oai-3.0-api-with-examples.yaml", "No servers defined in OpenAPI spec"),
    ],
)
def test_servers_of_real_documents(name: str, expected: str, tmp_path: Path) -> None:
    assert servers(analyzed(name, tmp_path)["json_report"]) == [expected]


def test_query_operation_of_openapi_3_2(tmp_path: Path) -> None:
    report = analyzed("oai-3.2-query-example.yaml", tmp_path)["json_report"]
    section = next(s for s in report["sections"] if s.get("path") == "/flights/search")
    assert section["httpMethods"] == ["QUERY"]
    methods = [m["message"] for m in all_messages(report, "HTTP Methods")]
    assert methods == ["HTTP method usage looks valid"]


def test_media_level_examples_count(tmp_path: Path) -> None:
    # Every response of this example carries `examples` next to its schema.
    report = analyzed("oai-3.0-api-with-examples.yaml", tmp_path)["json_report"]
    texts = {m["message"] for m in all_messages(report, "Response Examples")}
    assert "All responses define at least one example" in texts
    assert not any("missing example" in text for text in texts)


def test_a_large_real_document_is_fast(tmp_path: Path) -> None:
    started = time.perf_counter()
    report = analyzed("github-api.json", tmp_path)["json_report"]
    assert time.perf_counter() - started < 60
    assert servers(report) == ["All servers use HTTPS"]  # https://api.github.com
    assert len(report["sections"]) > 500
