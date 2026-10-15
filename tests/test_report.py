"""HTML writer and the JSON read back from it."""

from __future__ import annotations

from pathlib import Path

import pytest

from restful_checker.checks.check_result import CheckResult
from restful_checker.report import html_report
from restful_checker.report.extract_json_from_html import (
    classify_message_level_from_emoji,
    extract_json_from_html,
)
from restful_checker.report.html_report import (
    generate_html,
    get_score_level,
    render_ordered_section,
)
from restful_checker.report.rest_docs import REST_BEST_PRACTICES, linkify


def test_levels_from_emoji() -> None:
    assert classify_message_level_from_emoji("❌ x") == "error"
    assert classify_message_level_from_emoji("⚠️ x") == "warn"
    assert classify_message_level_from_emoji("✅ x") == "info"
    assert classify_message_level_from_emoji("plain") == "info"


@pytest.mark.parametrize(
    ("score", "level"),
    [(0, "Very Low"), (29, "Very Low"), (30, "Low"), (49, "Low"), (50, "Medium"), (69, "Medium"),
     (70, "Good"), (79, "Good"), (80, "Very Good"), (94, "Very Good"), (95, "Excellent")],
)  # fmt: skip
def test_score_levels(score: int, level: str) -> None:
    assert get_score_level(score)[0] == level


def test_errors_then_warnings_then_the_rest() -> None:
    html = render_ordered_section(["✅ a", "⚠️ b", "❌ c", "d"])
    assert html == "<ul><li>❌ c</li><li>⚠️ b</li><li>✅ a</li><li>d</li></ul>"


def test_round_trip(tmp_path: Path) -> None:
    report = [
        {"title": "/v1/a", "items": ["<strong>HTTP methods:</strong> GET, POST", "### One",
                                    "❌ bad", "⚠️ meh", "### Two", "✅ fine"], "score": 0.4},
        {"title": "/v1/b", "items": ["### Three", "✅ ok"], "score": 0.6},
        {"title": "SSL", "items": ["### Servers", "✅ ok"], "score": 1.0},
    ]  # fmt: skip
    out = Path(generate_html(report, 77, output=tmp_path / "r.html"))
    data = extract_json_from_html(out)
    assert data["score"] == 77
    first, second, ssl = data["sections"]
    assert first["path"] == "/v1/a" and first["score"] == 40
    assert first["httpMethods"] == ["GET", "POST"]
    assert [item["category"] for item in first["items"]] == ["One", "Two"]
    assert first["items"][0]["messages"] == [
        {"message": "bad", "level": "error"},
        {"message": "meh", "level": "warn"},
    ]
    assert second["score"] == 60 and "httpMethods" not in second
    assert ssl == {"score": 100, "items": [{"category": "Servers", "messages": [
        {"message": "ok", "level": "info"}]}], "section": "SSL"}  # fmt: skip
    html = out.read_text(encoding="utf-8")
    assert "section-error" in html and "section-warn" in html and "section-ok" in html
    assert out.with_suffix(".json").is_file()


def test_no_json_when_not_asked(tmp_path: Path) -> None:
    generate_html([], 100, output=tmp_path / "r.html", write_json=False)
    assert not (tmp_path / "r.json").exists()


def test_css_is_inlined_and_failure_is_tolerated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = Path(generate_html([], 1, output=tmp_path / "a.html")).read_text(encoding="utf-8")
    assert "box-sizing" in html

    def broken() -> str:
        raise OSError("gone")

    monkeypatch.setattr(html_report, "_read_css", broken)
    html = Path(generate_html([], 1, output=tmp_path / "b.html")).read_text(encoding="utf-8")
    assert "/* Failed to load CSS */" in html


def test_css_reader_without_importlib_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr("importlib.resources.files", raising=False)  # absent on 3.8
    assert "box-sizing" in html_report._read_css()
    monkeypatch.setattr("pkgutil.get_data", lambda *_: None)
    with pytest.raises(FileNotFoundError):
        html_report._read_css()


def test_old_style_titles_are_still_read(tmp_path: Path) -> None:
    page = tmp_path / "old.html"
    page.write_text(
        "<div class='section'><h2>🟢 /v1/x (55%)</h2><h3>A</h3><ul><li>✅ y</li></ul></div>"
        "<div class='section'><p>no heading</p></div><div class='section'><h2>SSL</h2></div>",
        encoding="utf-8",
    )
    sections = extract_json_from_html(page)["sections"]
    assert sections[0]["path"] == "/v1/x" and sections[0]["score"] == 55
    assert sections[1] == {"score": 100, "items": [], "section": "SSL"}


def test_linkify_and_check_result() -> None:
    assert linkify("<x>", "unknown") == "&lt;x&gt;"
    assert REST_BEST_PRACTICES["naming"]["link"] in linkify("m", "naming")
    result = CheckResult("naming")
    for _ in range(6):
        result.warning("w")
    assert result.finalize_score() == 0.0
    result = CheckResult("naming")
    result.error("e")
    result.warning("w")
    assert result.finalize_score() == 0.0
    assert result.score == 1.0
