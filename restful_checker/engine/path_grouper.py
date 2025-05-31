import re
from collections import defaultdict

def group_paths(paths):
    resources = defaultdict(lambda: {"collection": set(), "item": set(), "raw": set()})
    for path, methods in paths.items():
        raw = path
        base = re.sub(r"\{[^}]+}", "{id}", path).rstrip("/")
        is_item = "{" in path
        for method in methods:
            resources[base]["raw"].add(raw)
            if is_item:
                resources[base]["item"].add(method.upper())
            else:
                resources[base]["collection"].add(method.upper())
    return resources