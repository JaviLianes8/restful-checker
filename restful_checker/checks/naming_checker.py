from __future__ import annotations

import re
from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.version_checker import VERSION_REGEX

COMMON_VERBS = [
    "get", "create", "update", "delete", "post", "put", "fetch", "make", "do", "add"
]

GENERIC_TERMS = {"data", "info", "object", "thing", "stuff", "item"}
PREPOSITIONS = {"of", "for", "by", "with", "from", "to"}

# === Individual Checks ===

def _starts_with_verb(segment: str, verb: str) -> bool:
    # The verb must be a word of its own: `getUsers`, `get_users`, `create`; a noun that
    # merely starts with the same letters (`posts`, `documents`, `addresses`) is not one.
    if not re.fullmatch(rf"{verb}[A-Za-z0-9_]*", segment, re.IGNORECASE):
        return False
    rest = segment[len(verb) :]
    return not rest or rest[0].isupper() or rest[0].isdigit() or rest[0] == "_"


def check_contains_verb(segments: list[str], result: CheckResult) -> None:
    for segment in segments:
        for verb in COMMON_VERBS:
            if _starts_with_verb(segment, verb):
                result.error(f"Contains verb-like segment: `{segment}`")
                break

def check_last_segment_plural(segments: list[str], result: CheckResult) -> None:
    if not segments:
        return
    last = segments[-1]
    if "{" in last:
        return
    if not re.search(r"s\b", last):
        result.warning(f"Last segment `{last}` might not be plural (use plural for collections)")

def check_pascal_or_camel_case(segments: list[str], result: CheckResult) -> None:
    for segment in segments:
        if re.match(r"[A-Z][a-z]+[A-Z]", segment):  # PascalCase
            result.error(f"PascalCase not recommended in URL segment: `{segment}`")
        elif re.match(r"[a-z]+[A-Z][a-z]+", segment):  # camelCase
            result.error(f"camelCase not recommended in URL segment: `{segment}`")

def check_contains_numbers(segments: list[str], result: CheckResult) -> None:
    for segment in segments:
        if VERSION_REGEX.fullmatch(segment):
            continue  # `v1` is the version segment the versioning check asks for
        if re.search(r"[a-zA-Z]+[0-9]+", segment):
            result.warning(f"Segment `{segment}` contains mixed alphanumeric name")

def check_generic_resource_name(segments: list[str], result: CheckResult) -> None:
    for segment in segments:
        if segment.lower() in GENERIC_TERMS:
            result.warning(f"Segment `{segment}` is too generic")

def check_segment_preposition(segments: list[str], result: CheckResult) -> None:
    for segment in segments:
        if segment.lower() in PREPOSITIONS:
            result.error(f"Segment `{segment}` looks like a preposition, not RESTful")

# === Main Function ===

def check_naming(base_path: str) -> tuple[list[str], float]:
    """
    Check if the base path follows RESTful naming conventions.

    Args:
        base_path (str): Normalized API base path (e.g., "/users/{id}")

    Returns:
        tuple[list[str], float]: List of messages and a score between 0.0 and 1.0
    """
    segments = base_path.strip("/").split("/")
    result = CheckResult("naming")

    check_contains_verb(segments, result)
    check_last_segment_plural(segments, result)
    check_pascal_or_camel_case(segments, result)
    check_contains_numbers(segments, result)
    check_generic_resource_name(segments, result)
    check_segment_preposition(segments, result)

    if not result.messages:
        result.success("Resource naming looks RESTful")

    return result.messages, result.finalize_score()