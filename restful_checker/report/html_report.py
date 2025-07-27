from datetime import datetime
from pathlib import Path
import importlib.resources
import json

from restful_checker.report.extract_json_from_html import extract_json_from_html


def render_ordered_section(messages: list[str]) -> str:
    errors = [m for m in messages if m.startswith("❌")]
    warnings = [m for m in messages if m.startswith("⚠️")]
    others = [m for m in messages if not m.startswith(("❌", "⚠️"))]
    return "<ul>" + "".join(f"<li>{m}</li>" for m in errors + warnings + others) + "</ul>"


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


def generate_html(report: list[dict], score: int, output: str | Path = None, write_json=True) -> str:
    output = Path(output or Path(__file__).parent.parent / "html" / "rest_report.html")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level, color = get_score_level(score)

    try:
        inline_css = importlib.resources.files("restful_checker.data").joinpath("style.css").read_text()
    except Exception:
        inline_css = "/* Failed to load CSS */"

    html_parts = [
        "<html><head>",
        "<meta charset='utf-8'>",
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>RESTful API Report</title>",
        f"<style>{inline_css}</style>",
        "</head><body>",
        '<div class="container">',
        "<h1>RESTful API Report</h1>",
        f"<p><strong>Generated:</strong> {now}</p>",
        f"<div class='section'><div class='score' style='background:{color}'>{score}% - {level}</div></div>"
    ]

    for block in report:
        block_score = block.get("score", 1.0)
        emoji, level_class = (
            ("🔴", "section-error") if block_score < 0.5 else
            ("🟡", "section-warn") if block_score < 0.7 else
            ("🟢", "section-ok")
        )

        html_parts.append(f"<div class='section {level_class}'><h2>{emoji}&nbsp;{block['title']} <span class='score-inline'>({round(block_score * 100)}%)</span></h2>")

        section_messages = []
        for item in block["items"]:
            if item.startswith("### "):
                if section_messages:
                    html_parts.append(render_ordered_section(section_messages))
                    section_messages = []
                current_section = item[4:]
                html_parts.append(f"<h3>{current_section}</h3>")
            else:
                section_messages.append(item)

        if section_messages:
            html_parts.append(render_ordered_section(section_messages))

        html_parts.append("</div>")

    html_parts.append("</div></body></html>")
    html = "\n".join(html_parts)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    # Optional: generate matching .json file
    if write_json:
        json_output = output.with_suffix(".json")
        json_output.write_text(json.dumps(extract_json_from_html(output), indent=2), encoding="utf-8")

    return str(output)