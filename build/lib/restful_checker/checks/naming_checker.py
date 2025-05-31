import re
from restful_checker.checks.check_result import CheckResult

COMMON_VERBS = [
    "get", "create", "update", "delete", "post", "put", "fetch", "make", "do", "add"
]

GENERIC_TERMS = {"data", "info", "object", "thing", "stuff", "item"}
PREPOSITIONS = {"of", "for", "by", "with", "from", "to"}

# === Individual Checks ===

def check_contains_verb(segments, result):
    for segment in segments:
        for verb in COMMON_VERBS:
            if re.fullmatch(rf"{verb}[A-Za-z0-9_]*", segment, re.IGNORECASE):
                result.error(f"Contains verb-like segment: `{segment}`")
                break

def check_last_segment_plural(segments, result):
    if not segments:
        return
    last = segments[-1]
    if "{" in last:
        return
    if not re.search(r"s\b", last):
        result.warning(f"Last segment `{last}` might not be plural (use plural for collections)")

def check_pascal_or_camel_case(segments, result):
    for segment in segments:
        if re.match(r"[A-Z][a-z]+[A-Z]", segment):  # PascalCase
            result.error(f"PascalCase not recommended in URL segment: `{segment}`")
        elif re.match(r"[a-z]+[A-Z][a-z]+", segment):  # camelCase
            result.error(f"camelCase not recommended in URL segment: `{segment}`")

def check_contains_numbers(segments, result):
    for segment in segments:
        if re.search(r"[a-zA-Z]+[0-9]+", segment):
            result.warning(f"Segment `{segment}` contains mixed alphanumeric name")

def check_generic_resource_name(segments, result):
    for segment in segments:
        if segment.lower() in GENERIC_TERMS:
            result.warning(f"Segment `{segment}` is too generic")

def check_segment_preposition(segments, result):
    for segment in segments:
        if segment.lower() in PREPOSITIONS:
            result.error(f"Segment `{segment}` looks like a preposition — not RESTful")

# === Main Function ===

def check_naming(base_path: str):
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