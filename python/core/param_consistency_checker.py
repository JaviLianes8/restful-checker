import re
from collections import defaultdict
from .rest_docs import linkify

def check_param_consistency(all_paths: dict):
    param_map = defaultdict(set)

    for path in all_paths.keys():
        for match in re.finditer(r"\{([^}]+)\}", path):
            param = match.group(1)
            param_map[param.lower()].add(param)

    issues = []
    penalty = 0

    for group in param_map.values():
        if len(group) > 1:
            group_list = ", ".join(sorted(group))
            issues.append(linkify(f"⚠️ Inconsistent parameter naming: {group_list}", "param_consistency"))
            penalty -= 1

    if not issues:
        issues.append("✅ Path parameters look consistent")

    return issues, penalty