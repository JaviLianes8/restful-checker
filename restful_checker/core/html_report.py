from datetime import datetime
from pathlib import Path
import importlib.resources

def render_ordered_section(messages):
    html = ""
    errors = [m for m in messages if m.startswith("❌")]
    warnings = [m for m in messages if m.startswith("⚠️")]
    others = [m for m in messages if not m.startswith(("❌", "⚠️"))]
    for m in errors + warnings + others:
        html += f"<li>{m}</li>"
    html += "</ul>"
    return html

def generate_html(report, score, output=None):
    print("Using analyze_api updated")
    if output is None:
        output = Path(__file__).parent.parent / "html" / "rest_report.html"

    level = "Low" if score < 70 else "Acceptable" if score < 90 else "Excellent"
    color = "#e74c3c" if score < 70 else "#f39c12" if score < 90 else "#2ecc71"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        inline_css = importlib.resources.read_text("restful_checker.core.data", "style.css")
    except Exception:
        inline_css = "/* Failed to load CSS */"

    html = f"""<html><head>
    <meta charset='utf-8'>
    <title>RESTful API Report</title>
    <style>{inline_css}</style>
</head><body>
    <h1>RESTful API Report</h1>
    <p><strong>Generated:</strong> {now}</p>
    <div class='section'><div class='score' style='background:{color}'>{score}% - {level}</div></div>
"""

    for block in report:
        block_items = block['items']
        level_class = "section-ok"
        emoji = "🟢"
        if any("❌" in item for item in block_items):
            level_class = "section-error"
            emoji = "🔴"
        elif any("⚠️" in item for item in block_items):
            level_class = "section-warn"
            emoji = "🟡"

        html += f"<div class='section {level_class}'><h2>{emoji}&nbsp;{block['title']}</h2>"

        current_section = None
        section_messages = []

        for item in block_items:
            if item.startswith("### "):
                if section_messages:
                    html += render_ordered_section(section_messages)
                    section_messages = []
                current_section = item[4:]
                html += f"<h3>{current_section}</h3><ul>"
            else:
                section_messages.append(item)

        if section_messages:
            html += render_ordered_section(section_messages)

        html += "</div>"

    html += "</body></html>"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding='utf-8')
    return str(output)