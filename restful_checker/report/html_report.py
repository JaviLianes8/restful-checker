"""Write the HTML report, and the JSON report built from the same data."""

from __future__ import annotations

import html as html_lib
import importlib.resources
import json
import pkgutil
from datetime import datetime
from pathlib import Path
from typing import Any

from restful_checker.report.json_report import build_json_report, ordered
from restful_checker.report.rest_docs import REST_BEST_PRACTICES, SECTION_KEYS

# Labels of the lines that open a route section; the label is shown in bold.
LABELS = ("Routes:", "HTTP methods:")


def render_ordered_section(messages: list[str]) -> str:
    """List already rendered messages, errors first, then warnings, then the rest."""
    return "<ul>" + "".join(f"<li>{m}</li>" for m in ordered(messages)) + "</ul>"


def get_score_level(score: int) -> tuple[str, str]:
    if score < 30:
        return "Very Low", "#c0392b"
    elif score < 50:
        return "Low", "#e74c3c"
    elif score < 70:
        return "Medium", "#f39c12"
    elif score < 80:
        return "Good", "#f1c40f"
    elif score < 95:
        return "Very Good", "#2ecc71"
    return "Excellent", "#27ae60"


def _read_css() -> str:
    # importlib.resources.files arrived in 3.9; pkgutil keeps 3.8 working.
    if hasattr(importlib.resources, "files"):
        resource = importlib.resources.files("restful_checker.data").joinpath("style.css")
        return resource.read_text(encoding="utf-8")
    data = pkgutil.get_data("restful_checker.data", "style.css")
    if data is None:
        raise FileNotFoundError("style.css")
    return data.decode("utf-8")


def render_message(message: str, section: str | None) -> str:
    """Escape a plain-text message; errors and warnings link to their best practice.

    >>> render_message("⚠️ Segment `<b>` is too generic", "Naming")[:40]
    '⚠️ Segment `&lt;b&gt;` is too generic <a'
    """
    text = html_lib.escape(message)
    if section is None:
        for label in LABELS:
            if message.startswith(label):
                return f"<strong>{label}</strong>{html_lib.escape(message[len(label) :])}"
        return text
    key = SECTION_KEYS.get(section)
    if key is None or not message.startswith(("❌", "⚠️")):
        return text
    link = REST_BEST_PRACTICES[key]["link"]
    return f'{text} <a href="{link}" target="_blank">More info</a>'


def _block_html(block: dict[str, Any]) -> list[str]:
    block_score = block.get("score", 1.0)
    emoji, level_class = (
        ("🔴", "section-error")
        if block_score < 0.5
        else ("🟡", "section-warn")
        if block_score < 0.7
        else ("🟢", "section-ok")
    )
    title = html_lib.escape(str(block["title"]))
    parts = [
        f"<div class='section {level_class}'><h2>{emoji}&nbsp;{title} "
        f"<span class='score-inline'>({round(block_score * 100)}%)</span></h2>"
    ]
    section: str | None = None
    messages: list[str] = []
    for item in block["items"]:
        if item.startswith("### "):
            if messages:
                parts.append(render_ordered_section(messages))
                messages = []
            section = item[4:]
            parts.append(f"<h3>{html_lib.escape(section)}</h3>")
        else:
            messages.append(render_message(item, section))
    if messages:
        parts.append(render_ordered_section(messages))
    parts.append("</div>")
    return parts


def render_html(report: list[dict[str, Any]], score: int, generated: str) -> str:
    """Return the HTML page of a report."""
    level, color = get_score_level(score)
    try:
        inline_css = _read_css()
    except Exception:
        inline_css = "/* Failed to load CSS */"
    parts = [
        "<html><head>",
        "<meta charset='utf-8'>",
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>RESTful API Report</title>",
        f"<style>{inline_css}</style>",
        "</head><body>",
        '<div class="container">',
        "<h1>RESTful API Report</h1>",
        f"<p><strong>Generated:</strong> {generated}</p>",
        f"<div class='section'><div class='score' style='background:{color}'>{score}% - "
        f"{level}</div></div>",
    ]
    for block in report:
        parts.extend(_block_html(block))
    parts.append("</div></body></html>")
    return "\n".join(parts)


def write_reports(
    report: list[dict[str, Any]], score: int, output: Path, write_json: bool = True
) -> tuple[str, dict[str, Any]]:
    """Write the HTML page (and its JSON twin); return the page path and the JSON report."""
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = build_json_report(report, score, generated)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(report, score, generated), encoding="utf-8")
    if write_json:
        output.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(output), data


def generate_html(
    report: list[dict[str, Any]],
    score: int,
    output: str | Path | None = None,
    write_json: bool = True,
) -> str:
    """Write the HTML report (and ``rest_report.json`` next to it) and return its path."""
    path = Path(output or Path(__file__).parent.parent / "html" / "rest_report.html")
    return write_reports(report, score, path, write_json)[0]
