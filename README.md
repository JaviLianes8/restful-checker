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
✅ Versioning	Ensures /v1/, /v2/ appears early in the path
✅ Resource Naming	Detects verbs in URIs and suggests pluralization
✅ HTTP Methods	Validates usage of GET, POST, PUT, DELETE, etc. per REST rules
✅ Status Codes	Checks use of proper HTTP codes (200, 201, 400, 404, 409)
✅ Path Parameters	Verifies consistent and correct usage of {param} in paths
✅ Query Filters	Recommends filters in GET collections like ?status= or ?filter=
✅ Pagination	Suggests support for ?page= and ?limit= in collection endpoints
✅ HTTPS Enforcement	Ensures all servers use HTTPS
✅ Content Types	Verifies application/json usage for requests and responses
✅ Response Examples	Encourages defining example or examples in responses
✅ Error Format	Suggests using structured fields like code and message
✅ Resource Nesting	Validates nesting such as /users/{id}/orders
✅ GZIP Support	Assumes gzip compression via Accept-Encoding
✅ Pretty Print	Recommends support for query param like ?pretty=true
✅ Response Wrapping	Warns about envelopes like { data: ... } unless justified

📁 Structure (if cloning)
restful-checker/
├── html/                   # HTML report output
│   └── rest_report.html
├── restful_checker/        # Source code
│   ├── checks/             # All individual check modules
│   ├── engine/             # OpenAPI loader and path grouping
│   └── report/             # HTML rendering
├── main.py                 # CLI entrypoint
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
