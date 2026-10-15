from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Any, Callable, List, Tuple

from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.content_type_checker import check_content_type
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.https_checker import check_https_usage
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.resource_nesting_checker import check_resource_nesting
from restful_checker.checks.response_example_checker import check_response_examples
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.version_checker import check_versioning
from restful_checker.engine.normalizer import normalize_paths
from restful_checker.engine.openapi_loader import load_openapi
from restful_checker.engine.path_grouper import group_paths
from restful_checker.report.extract_json_from_html import extract_json_from_html
from restful_checker.report.html_report import generate_html

CheckOutput = Tuple[List[str], float]  # a runtime alias: subscripted builtins need 3.9


def _per_path(
    check: Callable[[str, dict[str, Any]], CheckOutput],
    raw_paths: set[str],
    paths: dict[str, dict[str, Any]],
) -> CheckOutput:
    # Each real route of a group is checked against its own operations; the group's
    # normalised name (`{id}`, no trailing slash) is not a key of the Paths Object.
    runs = [check(raw, paths.get(raw, {})) for raw in sorted(raw_paths)]
    messages = [message for run_messages, _ in runs for message in run_messages]
    if len(runs) > 1:
        # Routes of one group (`/users`, `/users/`) repeat the same success line; keep it once.
        messages = list(dict.fromkeys(messages))
    return messages, sum(score for _, score in runs) / len(runs)


def _analyze_group(
    base_path: str, info: dict[str, set[str]], paths: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    methods = sorted(info["collection"].union(info["item"]))
    items = [
        f"<strong>Routes:</strong> {escape(', '.join(sorted(info['raw'])))}",
        f"<strong>HTTP methods:</strong> {escape(', '.join(methods or ['none']))}",
    ]
    scores: list[float] = []

    def process_section(title: str, output: CheckOutput) -> None:
        items.append(f"### {title}")
        items.extend(output[0])
        scores.append(output[1])

    # Run all checkers for this resource
    raw = info["raw"]
    process_section("Versioning", check_versioning(base_path))
    process_section("Naming", check_naming(base_path))
    process_section("HTTP Methods", check_http_methods(base_path, set(methods)))
    process_section("Status Codes", _per_path(check_status_codes, raw, paths))
    process_section("Content Types", _per_path(check_content_type, raw, paths))
    process_section("Response Examples", _per_path(check_response_examples, raw, paths))
    process_section("Error Format", _per_path(check_error_format, raw, paths))

    # Analyze each raw path (used for GETs, filters, nesting, etc.)
    for raw_path in sorted(raw):
        path_obj = paths.get(raw_path, {})
        if "get" in path_obj and not re.search(r"/\{[^}]+}/?$", raw_path):
            process_section("Filters", check_query_filters(raw_path, path_obj))
        process_section("Pagination", check_pagination(raw_path, path_obj))
        process_section("Resource Nesting", check_resource_nesting(raw_path, path_obj))

    score = round(sum(scores) / len(scores), 2)
    return {"title": base_path, "items": items, "score": score}


def analyze_api(
    path: str | Path, output_dir: str | Path = "html", output_format: str = "html"
) -> dict[str, Any]:
    """
    Analyze an OpenAPI specification for RESTful compliance and generate a report.

    Args:
        path (str or Path): Path to the OpenAPI file (.json or .yaml/.yml).
        output_dir (str or Path): Output directory for the report (default: "html").
        output_format (str): Not used here, but compatible with caller (html, json, both).

    Returns:
        dict: Contains:
            - 'html_path': Path to the generated HTML report.
            - 'json_path': Path to the JSON report written next to it.
            - 'json_report': Parsed JSON report extracted from the HTML.
    """
    # Load and parse the OpenAPI spec
    data = load_openapi(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not hold an OpenAPI document")
    paths = normalize_paths(data)
    resources = group_paths(paths)

    report: list[dict[str, Any]] = []
    score_sum = 0.0
    total_blocks = 0

    # Analyze each grouped resource
    for base_path, info in resources.items():
        block = _analyze_group(base_path, info, paths)
        report.append(block)
        score_sum += block["score"]
        total_blocks += 1

    # Global checks
    https_msgs, https_score = check_https_usage(data)
    report.append(
        {"title": "SSL", "items": ["### Servers"] + https_msgs, "score": round(https_score, 2)}
    )
    score_sum += https_score
    total_blocks += 1

    param_msgs, param_score = check_param_consistency(paths)
    report.append(
        {
            "title": "Global Parameter Consistency",
            "items": ["### Parameters"] + param_msgs,
            "score": round(param_score, 2),
        }
    )
    score_sum += param_score
    total_blocks += 1

    final_score = round((score_sum / total_blocks) * 100)

    # Output
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = generate_html(report, final_score, output=output_dir / "rest_report.html")

    return {
        "html_path": str(html_path),
        "json_path": str(Path(html_path).with_suffix(".json")),
        "json_report": extract_json_from_html(html_path),
    }
