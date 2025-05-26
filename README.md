# RESTful API Checker

**RESTful API Checker** is a lightweight and modular Python tool that analyzes a Swagger/OpenAPI specification and validates its compliance with RESTful best practices.

It generates a comprehensive **HTML report** with ✅ status, 🟡 warnings, and ❌ critical issues, helping you improve your API design before deployment or review.

---

## What It Checks

| Category                 | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **Versioning**           | Ensures version segments like `/v1/` are present early in the path          |
| **Resource Naming**      | Detects verbs in URIs and checks for plural usage where needed              |
| **HTTP Methods**         | Validates correct HTTP verbs for actions (GET for read, POST for create...) |
| **Status Codes**         | Checks if responses include standard codes (200, 201, 400, 409, etc.)       |
| **Parameter Consistency**| Verifies that path parameters are well defined and used properly            |
| **Query Filters**        | Recommends use of filters in GET collections (e.g., `?status=`, `?filter=`) |

---

## Project Structure

```text
restful-checker/
├── html/                   # HTML report output
│   └── rest_report.html
├── json/                   # OpenAPI files
│   └── openapi.json
├── css/                    # Optional: shared stylesheet
│   └── style.css
├── python/
│   ├── main.py
│   └── core/
│       ├── analyzer.py
│       ├── html_report.py
│       ├── naming_checker.py
│       ├── openapi_loader.py
│       ├── path_grouper.py
│       ├── version_checker.py
│       ├── http_method_checker.py
│       ├── status_code_checker.py
│       ├── param_consistency_checker.py
│       ├── query_filter_checker.py
│       └── rest_docs.py
├── run_checker.bat         # Double-click to run
├── requirements.txt
└── README.md

---

## How to Run

### 
1. Install dependencies
	pip install -r requirements.txt
	
2. Add your OpenAPI file
	Drop your openapi.json or swagger.json file into the json/ folder.

3. Run the checker
	Double-click run_checker.bat (Windows) or run manually:
	python python/main.py json/openapi.json

4. View the report
	Open html/rest_report.html in your browser.

Why Use This?
	1.Avoid rejections during API review
	2.Standardize APIs across teams
	3.Improve long-term maintainability
	4.Catch inconsistencies early

Resources

RESTful API Design
OpenAPI Specification
VSCode Markdown Preview

Requirements
Python 3.8+

Dependencies in requirements.txt (currently none)