import re
from .rest_docs import linkify  # ✅ Usamos la versión compartida

def check_versioning(base):
    parts = base.strip("/").split("/")
    version_pattern = re.compile(r"v[0-9]+", re.IGNORECASE)

    version_index = -1
    for i, part in enumerate(parts):
        if version_pattern.fullmatch(part):
            version_index = i
            break

    if version_index == -1:
        return [linkify("❌ No version segment found in route.", "versioning")], -5

    if version_index > 2:
        return [linkify("⚠️ Version segment is too deep in the path.", "versioning")], -2

    if len(parts) <= version_index + 1:
        return [linkify("⚠️ Version segment exists but no resource segment follows.", "versioning")], -2

    resource_parts = parts[version_index + 1:]
    contains_id = any(re.match(r"\{[^}]+\}", part) for part in resource_parts)
    all_static = all(not re.match(r"\{[^}]+\}", part) for part in resource_parts)

    if contains_id:
        return ["✅ Versioning detected"], 0
    elif all_static:
        return [linkify("⚠️ Version segment exists but does not apply to a resource (no parameter found).", "versioning")], -4
    else:
        return [linkify("⚠️ Version segment found but resource usage is unclear.", "versioning")], -2