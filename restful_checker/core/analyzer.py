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

def normalize_block_score(score):
    if score <= -2:
        return 0.0
    elif score == -1:
        return 0.5
    else:
        return 1.0

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

        block_score = 0

        v_msgs, v_penalty = check_versioning(base)
        block_score += v_penalty
        items.append("### Versioning")
        items.extend(v_msgs)

        n_msgs, n_penalty = check_naming(base)
        block_score += n_penalty
        items.append("### Naming")
        items.extend(n_msgs)

        items.append("### HTTP Methods")
        m_msgs, m_penalty = check_http_methods(base, info['collection'].union(info['item']))
        block_score += m_penalty
        items.extend(m_msgs)

        items.append("### Status Codes")
        s_msgs, s_penalty = check_status_codes(base, paths.get(base, {}))
        block_score += s_penalty
        items.extend(s_msgs)

        for raw_path in info['raw']:
            if "get" in paths.get(raw_path, {}) and not raw_path.endswith("}"):
                f_msgs, f_penalty = check_query_filters(raw_path, paths.get(raw_path, {}))
                block_score += f_penalty
                items.append("### Filters")
                items.extend(f_msgs)
                break

        report.append({
            "title": f"{base}",
            "items": items,
            "score": block_score
        })
        score_sum += normalize_block_score(block_score)
        total_blocks += 1

    param_report, param_penalty = check_param_consistency(paths)
    report.append({
        "title": "Global Parameter Consistency",
        "items": ["### Parameters"] + param_report,
        "score": param_penalty
    })
    score_sum += normalize_block_score(param_penalty)
    total_blocks += 1

    final_score = round((score_sum / total_blocks) * 100)
    output_path = Path(__file__).parent.parent / "html" / "rest_report.html"
    return generate_html(report, final_score, output=output_path)