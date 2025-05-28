# RESTful API Checker

**RESTful API Checker** is a lightweight Python CLI tool to **validate RESTful best practices** on OpenAPI/Swagger specs. It generates an easy-to-read **HTML report** with ✅ correct cases, 🟡 warnings, and ❌ critical issues to help you improve your API design before release.

---

## 📦 Installation

### ▶️ From PyPI

```bash
pip install restful-checker
Requires Python 3.8+.

🚀 Quick Usage
restful-checker path/to/openapi.json
This will generate an HTML report at:

html/rest_report.html

You can then open it in your browser.

🧪 What It Checks
Category	Description
✅ Versioning	Ensures /v1/, /v2/... appears early in the path
✅ Resource Naming	Detects verbs in URIs and suggests pluralization
✅ HTTP Methods	Validates usage of GET, POST, PUT, DELETE, etc. per REST rules
✅ Status Codes	Checks response codes like 200, 201, 400, 404, 409
✅ Path Parameters	Verifies correct usage and definition of path params
✅ Query Filters	Recommends filters in GET collections like ?status= or ?filter=

📁 Structure (if cloning)
restful-checker/
├── html/                   # HTML report output
│   └── rest_report.html
├── python/                 # Source code
│   └── main.py
│   └── core/               # All analyzers
└── requirements.txt

💡 Why Use It?
✅ Prevent API design issues before code review
🧩 Enforce consistent RESTful practices across teams
🛡️ Improve long-term API maintainability
🕵️ Catch design mistakes early and automatically

👨‍💻 Programmatic Use (Optional)
You can also run the analyzer in code:

from restful_checker.core.analyzer import analyze_api
html_path = analyze_api("path/to/openapi.json")

📌 License
MIT – Free to use and modify

```

## Contributors

<a href="https://github.com/alejandrosenior">
  <img src="https://github.com/alejandrosenior.png" width="100" alt="alejandrosenior">
</a>
<a href="https://github.com/JaviLianes8">
  <img src="https://github.com/JaviLianes8.png" width="100" alt="JaviLianes8">
</a>

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>
