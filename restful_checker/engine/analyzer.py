from pathlib import Path

from restful_checker.engine.openapi_loader import load_openapi
from restful_checker.engine.path_grouper import group_paths
from restful_checker.checks.version_checker import check_versioning
from restful_checker.checks.naming_checker import check_naming
from restful_checker.report.html_report import generate_html
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters

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

        v_msgs, v_score = check_versioning(base)
        block_score += v_score
        items.append("### Versioning")
        items.extend(v_msgs)

        n_msgs, n_score = check_naming(base)
        block_score += n_score
        items.append("### Naming")
        items.extend(n_msgs)

        items.append("### HTTP Methods")
        m_msgs, m_score = check_http_methods(base, info['collection'].union(info['item']))
        block_score += m_score
        items.extend(m_msgs)

        items.append("### Status Codes")
        s_msgs, s_score = check_status_codes(base, paths.get(base, {}))
        block_score += s_score
        items.extend(s_msgs)

        for raw_path in info['raw']:
            if "get" in paths.get(raw_path, {}) and not raw_path.endswith("}"):
                f_msgs, f_score = check_query_filters(raw_path, paths.get(raw_path, {}))
                block_score += f_score
                items.append("### Filters")
                items.extend(f_msgs)
                break

        report.append({
            "title": f"{base}",
            "items": items,
            "score": round(block_score / 5, 2)
        })
        score_sum += block_score / 5
        total_blocks += 1

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