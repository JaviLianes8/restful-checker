from pathlib import Path

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

def analyze_api(path):
    data = load_openapi(path)
    paths = data.get("paths", {})
    resources = group_paths(paths)
    report = []
    score_sum = 0
    total_blocks = 0

    for base, info in resources.items():
        items = [f"<strong>Routes:</strong> {', '.join(sorted(info['raw']))}"]
        all_methods = sorted(info['collection'].union(info['item']))
        items.append(f"<strong>HTTP methods:</strong> {', '.join(all_methods) or 'none'}")

        block_score = 0.0
        section_count = 0

        v_msgs, v_score = check_versioning(base)
        block_score += v_score
        section_count += 1
        items.append("### Versioning")
        items.extend(v_msgs)

        n_msgs, n_score = check_naming(base)
        block_score += n_score
        section_count += 1
        items.append("### Naming")
        items.extend(n_msgs)

        m_msgs, m_score = check_http_methods(base, info['collection'].union(info['item']))
        block_score += m_score
        section_count += 1
        items.append("### HTTP Methods")
        items.extend(m_msgs)

        s_msgs, s_score = check_status_codes(base, paths.get(base, {}))
        block_score += s_score
        section_count += 1
        items.append("### Status Codes")
        items.extend(s_msgs)

        ct_msgs, ct_score = check_content_type(base, paths.get(base, {}))
        block_score += ct_score
        section_count += 1
        items.append("### Content Types")
        items.extend(ct_msgs)

        rx_msgs, rx_score = check_response_examples(base, paths.get(base, {}))
        block_score += rx_score
        section_count += 1
        items.append("### Response Examples")
        items.extend(rx_msgs)

        ef_msgs, ef_score = check_error_format(base, paths.get(base, {}))
        block_score += ef_score
        section_count += 1
        items.append("### Error Format")
        items.extend(ef_msgs)

        for raw_path in info['raw']:
            # Filters
            if "get" in paths.get(raw_path, {}) and not raw_path.endswith("}"):
                f_msgs, f_score = check_query_filters(raw_path, paths.get(raw_path, {}))
                block_score += f_score
                section_count += 1
                items.append("### Filters")
                items.extend(f_msgs)

            # Pagination
            p_msgs, p_score = check_pagination(raw_path, paths.get(raw_path, {}))
            block_score += p_score
            section_count += 1
            items.append("### Pagination")
            items.extend(p_msgs)

            # Resource Nesting
            nesting_msgs, nesting_score = check_resource_nesting(raw_path, paths.get(raw_path, {}))
            block_score += nesting_score
            section_count += 1
            items.append("### Resource Nesting")
            items.extend(nesting_msgs)

        if section_count > 0:
            normalized_score = round(block_score / section_count, 2)
        else:
            normalized_score = 1.0

        report.append({
            "title": f"{base}",
            "items": items,
            "score": normalized_score
        })
        score_sum += normalized_score
        total_blocks += 1

    # ✅ Global check: HTTPS
    https_msgs, https_score = check_https_usage(data)
    report.append({
        "title": "SSL",
        "items": ["### Servers"] + https_msgs,
        "score": round(https_score, 2)
    })
    score_sum += https_score
    total_blocks += 1

    # ✅ Global check: parameter consistency
    param_report, param_score = check_param_consistency(paths)
    report.append({
        "title": "Global Parameter Consistency",
        "items": ["### Parameters"] + param_report,
        "score": round(param_score, 2)
    })
    score_sum += param_score
    total_blocks += 1

    final_score = round((score_sum / total_blocks) * 100)
    output_path = Path(__file__).parent.parent / "html" / "rest_report.html"
    return generate_html(report, final_score, output=output_path)