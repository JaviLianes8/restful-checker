import re
from collections import defaultdict
from .rest_docs import linkify

class ParamConsistencyCheckResult:
    def __init__(self):
        self.messages = []
        self.has_error = False
        self.has_warning = False

    def error(self, msg):
        self.messages.append(linkify(f"❌ {msg}", "param_consistency"))
        self.has_error = True

    def warning(self, msg):
        self.messages.append(linkify(f"⚠️ {msg}", "param_consistency"))
        self.has_warning = True

    def finalize_score(self):
        if self.has_error:
            return -2
        if self.has_warning:
            return -1
        return 0

def check_param_consistency(all_paths: dict):
    result = ParamConsistencyCheckResult()
    param_map = defaultdict(set)

    all_params = set()

    for path in all_paths.keys():
        for match in re.finditer(r"\{([^}]+)\}", path):
            param = match.group(1)
            param_map[param.lower()].add(param)
            all_params.add(param)

    for group in param_map.values():
        if len(group) > 1:
            group_list = ", ".join(sorted(group))
            result.warning(f"Inconsistent parameter naming: {group_list}")

    snake_case = {p for p in all_params if "_" in p}
    camel_case = {p for p in all_params if re.search(r"[a-z][A-Z]", p)}

    if snake_case and camel_case:
        result.warning("Mixed parameter styles detected (snake_case and camelCase)")

    for param in all_params:
        if param.lower() in {"id", "name", "value"}:
            result.warning(f"Generic parameter name used: `{param}` — consider using more specific names")

    if not result.messages:
        result.messages.append("✅ Path parameters look consistent")

    return result.messages, result.finalize_score()