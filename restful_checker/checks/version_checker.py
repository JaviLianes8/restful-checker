"""Version segment of a route."""

from __future__ import annotations

import re

from restful_checker.checks.check_result import CheckResult

# `v1`, `v2.1`, and the pre-release forms `v1beta1`, `v2alpha` (as Kubernetes and Google use).
VERSION_REGEX = re.compile(r"^v[0-9]+(\.[0-9]+)*((alpha|beta)[0-9]*)?$", re.IGNORECASE)
PARAM_REGEX = re.compile(r"\{[^}]+}")

# === Individual Checks ===


def check_no_version_segment(parts: list[str], result: CheckResult) -> list[int]:
    version_indices = [i for i, part in enumerate(parts) if VERSION_REGEX.fullmatch(part)]
    if not version_indices:
        result.error("No version segment found in route.")
    return version_indices


def check_multiple_versions(version_indices: list[int], result: CheckResult) -> None:
    if len(version_indices) > 1:
        result.error("Multiple version segments found (e.g., /v1/v2/...).")


def check_version_too_deep(version_index: int, result: CheckResult) -> None:
    if version_index > 2:
        result.error("Version segment is too deep in the path.")


def check_version_position(version_index: int, result: CheckResult) -> None:
    if version_index > 1:
        result.warning("Version segment should ideally be at the start or second position.")


def check_empty_after_version(parts: list[str], version_index: int, result: CheckResult) -> None:
    if len(parts) <= version_index + 1:
        result.error("Version segment found but no resource segment follows.")


def check_resource_is_id(resource_parts: list[str], result: CheckResult) -> None:
    if resource_parts and PARAM_REGEX.fullmatch(resource_parts[0]):
        result.error("Resource immediately after version is an ID parameter, which is not RESTful.")


def check_resource_static_only(resource_parts: list[str], result: CheckResult) -> None:
    # Kept for callers of 3.1; `check_versioning` no longer runs it, since every collection
    # route such as /v1/users is static and the warning fired on all of them.
    if resource_parts and all(not PARAM_REGEX.search(part) for part in resource_parts):
        result.warning("Version segment exists but no dynamic resource parameter is found.")


# === Main Function ===


def check_versioning(base_path: str) -> tuple[list[str], float]:
    """
    Check if versioning is present and correctly positioned in the route.

    Validates:
    - Version segment exists (e.g., /v1/)
    - Only one version segment
    - It's close to the root (ideally first or second)
    - Is followed by a proper resource, not an ID

    >>> check_versioning("/v1beta1/users")
    (['✅ Versioning detected'], 1.0)
    >>> check_versioning("/users")
    (['❌ No version segment found in route.'], 0.0)

    Args:
        base_path (str): The API base path to check (normalized with {id} replacements).

    Returns:
        tuple[list[str], float]: List of result messages and score.
    """
    parts = base_path.strip("/").split("/")
    result = CheckResult("versioning")

    version_indices = check_no_version_segment(parts, result)
    if not version_indices:
        return result.messages, result.finalize_score()

    check_multiple_versions(version_indices, result)
    version_index = version_indices[0]

    check_version_too_deep(version_index, result)
    check_version_position(version_index, result)
    check_empty_after_version(parts, version_index, result)

    resource_parts = parts[version_index + 1 :]

    check_resource_is_id(resource_parts, result)

    if not result.messages:
        result.success("Versioning detected")

    return result.messages, result.finalize_score()
