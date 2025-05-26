from datetime import datetime
from pathlib import Path

def generate_html(report, score, output=None):
    if output is None:
        output = Path(__file__).parent.parent / "html" / "rest_report.html"

    level = "Low" if score < 70 else "Acceptable" if score < 90 else "Excellent"
    color = "#e74c3c" if score < 70 else "#f39c12" if score < 90 else "#2ecc71"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<html><head>
    <meta charset='utf-8'>
    <title>RESTful API Report</title>
    <link rel="stylesheet" href="css/style.css">
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

        html += f"<div class='section {level_class}'><h2>{emoji}&nbsp;{block['title']}</h2><ul>"
        for item in block_items:
            if item.startswith("### "):
                html += f"</ul><h3>{item[4:]}</h3><ul>"
            else:
                html += f"<li>{item}</li>"
        html += "</ul></div>"

    html += "</body></html>"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding='utf-8')
    return str(output)