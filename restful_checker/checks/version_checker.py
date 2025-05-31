import re
from restful_checker.checks.check_result import CheckResult

VERSION_REGEX = re.compile(r"^v[0-9]+$", re.IGNORECASE)
PARAM_REGEX = re.compile(r"\{[^}]+}")

# === Individual Checks ===

def check_no_version_segment(parts, result):
    version_indices = [i for i, part in enumerate(parts) if VERSION_REGEX.fullmatch(part)]
    if not version_indices:
        result.error("No version segment found in route.")
    return version_indices

def check_multiple_versions(version_indices, result):
    if len(version_indices) > 1:
        result.error("Multiple version segments found (e.g., /v1/v2/...).")

def check_version_too_deep(version_index, result):
    if version_index > 2:
        result.error("Version segment is too deep in the path.")

def check_version_position(version_index, result):
    if version_index > 1:
        result.warning("Version segment should ideally be at the start or second position.")

def check_empty_after_version(parts, version_index, result):
    if len(parts) <= version_index + 1:
        result.error("Version segment found but no resource segment follows.")

def check_resource_is_id(resource_parts, result):
    if resource_parts and PARAM_REGEX.fullmatch(resource_parts[0]):
        result.error("Resource immediately after version is an ID parameter, which is not RESTful.")

def check_resource_static_only(resource_parts, result):
    if resource_parts and all(not PARAM_REGEX.search(part) for part in resource_parts):
        result.warning("Version segment exists but no dynamic resource parameter is found.")

# === Main Function ===

def check_versioning(base: str):
    parts = base.strip("/").split("/")
    result = CheckResult("versioning")

    version_indices = check_no_version_segment(parts, result)
    if not version_indices:
        return result.messages, result.finalize_score()

    check_multiple_versions(version_indices, result)
    version_index = version_indices[0]

    check_version_too_deep(version_index, result)
    check_version_position(version_index, result)
    check_empty_after_version(parts, version_index, result)

    resource_parts = parts[version_index + 1:]

    check_resource_is_id(resource_parts, result)
    check_resource_static_only(resource_parts, result)

    if not result.messages:
        result.success("Versioning detected")

    return result.messages, result.finalize_score()