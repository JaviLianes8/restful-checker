from pathlib import Path
import re

from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.response_example_checker import check_response_examples
from restful_checker.engine.openapi_loader import load_openapi
from restful_checker.engine.path_grouper import group_paths
from restful_checker.checks.version_checker import check_versioning
from restful_checker.checks.naming_checker import check_naming
from restful_checker.report.html_report import generate_html
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.https_checker import check_https_usage
from restful_checker.checks.content_type_checker import check_content_type
from restful_checker.checks.resource_nesting_checker import check_resource_nesting


def strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[✅❌⚠️]', '', text)
    return text.strip()

def analyze_api(path, output_dir="html", output_format="html"):
    data = load_openapi(path)
    paths = data.get("paths", {})
    resources = group_paths(paths)
    report = []
    score_sum = 0
    total_blocks = 0

    for base, info in resources.items():
        items = [f"<strong>Routes:</strong> {', '.join(sorted(info['raw']))}"]
        json_items = [{"type": "info", "text": f"Routes: {', '.join(sorted(info['raw']))}"}]
        all_methods = sorted(info['collection'].union(info['item']))
        items.append(f"<strong>HTTP methods:</strong> {', '.join(all_methods) or 'none'}")
        json_items.append({"type": "info", "text": f"HTTP methods: {', '.join(all_methods) or 'none'}"})

        block_score = 0.0
        section_count = 0

        def process_section(title, msgs, score):
            nonlocal block_score, section_count
            block_score += score
            section_count += 1
            items.append(f"### {title}")
            items.extend(msgs)
            clean_msgs = [strip_html(m) for m in msgs]
            json_items.append({"type": "section", "title": title, "messages": clean_msgs})

        process_section("Versioning", *check_versioning(base))
        process_section("Naming", *check_naming(base))
        process_section("HTTP Methods", *check_http_methods(base, info['collection'].union(info['item'])))
        process_section("Status Codes", *check_status_codes(base, paths.get(base, {})))
        process_section("Content Types", *check_content_type(base, paths.get(base, {})))
        process_section("Response Examples", *check_response_examples(base, paths.get(base, {})))
        process_section("Error Format", *check_error_format(base, paths.get(base, {})))

        for raw_path in info['raw']:
            if "get" in paths.get(raw_path, {}) and not raw_path.endswith("}"):
                process_section("Filters", *check_query_filters(raw_path, paths.get(raw_path, {})))
            process_section("Pagination", *check_pagination(raw_path, paths.get(raw_path, {})))
            process_section("Resource Nesting", *check_resource_nesting(raw_path, paths.get(raw_path, {})))

        normalized_score = round(block_score / section_count, 2) if section_count > 0 else 1.0

        report.append({
            "title": f"{base}",
            "items": items,
            "json_items": json_items,
            "score": normalized_score
        })
        score_sum += normalized_score
        total_blocks += 1

    https_msgs, https_score = check_https_usage(data)
    clean_https_msgs = [strip_html(m) for m in https_msgs]
    report.append({
        "title": "SSL",
        "items": ["### Servers"] + https_msgs,
        "json_items": [{"type": "section", "title": "Servers", "messages": clean_https_msgs}],
        "score": round(https_score, 2)
    })
    score_sum += https_score
    total_blocks += 1

    param_report, param_score = check_param_consistency(paths)
    clean_param_report = [strip_html(m) for m in param_report]
    report.append({
        "title": "Global Parameter Consistency",
        "items": ["### Parameters"] + param_report,
        "json_items": [{"type": "section", "title": "Parameters", "messages": clean_param_report}],
        "score": round(param_score, 2)
    })
    score_sum += param_score
    total_blocks += 1

    final_score = round((score_sum / total_blocks) * 100)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = generate_html(report, final_score, output=output_dir / "rest_report.html")

    return {
        "html_path": str(html_path),
        "json_report": {
            "score": final_score,
            "sections": [
                {
                    "title": section["title"],
                    "score": section["score"],
                    "items": section.get("json_items")
                } for section in report
            ]
        }
    }