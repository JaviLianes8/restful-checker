from pathlib import Path

from .openapi_loader import load_openapi
from .path_grouper import group_paths
from .version_checker import check_versioning
from .naming_checker import check_naming
from .html_report import generate_html
from .http_method_checker import check_http_methods
from .status_code_checker import check_status_codes
from .param_consistency_checker import check_param_consistency
from .query_filter_checker import check_query_filters

def analyze_api(path):
    data = load_openapi(path)
    paths = data.get("paths", {})
    resources = group_paths(paths)
    report = []
    score = 100

    for base, info in resources.items():
        items = [f"<strong>Routes:</strong> {', '.join(sorted(info['raw']))}"]
        all_methods = sorted(info['collection'].union(info['item']))
        items.append(f"<strong>HTTP methods:</strong> {', '.join(all_methods) or 'none'}")

        v_msgs, v_penalty = check_versioning(base)
        score += v_penalty
        items.append("### Versioning")
        items.extend(v_msgs)

        n_msgs, n_penalty = check_naming(base)
        score += n_penalty
        items.append("### Naming")
        items.extend(n_msgs)

        items.append("### HTTP Methods")
        m_msgs, m_penalty = check_http_methods(base, info['collection'].union(info['item']))
        score += m_penalty
        items.extend(m_msgs)

        items.append("### Status Codes")
        s_msgs, s_penalty = check_status_codes(base, paths.get(base, {}))
        score += s_penalty
        items.extend(s_msgs)

        for raw_path in info['raw']:
            if "get" in paths.get(raw_path, {}) and not raw_path.endswith("}"):
                f_msgs, f_penalty = check_query_filters(raw_path, paths.get(raw_path, {}))
                score += f_penalty
                items.append("### Filters")
                items.extend(f_msgs)
                break

        report.append({
            "title": f"{base}",
            "items": items
        })

    # Global consistency
    param_report, param_penalty = check_param_consistency(paths)
    score += param_penalty
    report.append({
        "title": "Global Parameter Consistency",
        "items": ["### Parameters"] + param_report
    })

    output_path = Path(__file__).parent.parent / "html" / "rest_report.html"
    return generate_html(report, max(min(score, 100), 0), output=output_path)
