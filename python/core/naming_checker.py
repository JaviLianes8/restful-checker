import re
from .rest_docs import linkify

COMMON_VERBS = [
    "get", "create", "update", "delete", "post", "put", "fetch", "make", "do", "add"
]

def check_naming(base_path: str):
    issues = []
    score_penalty = 0

    segments = base_path.strip("/").split("/")

    for segment in segments:
        if any(re.fullmatch(rf"{verb}[a-zA-Z0-9_]*", segment, re.IGNORECASE) for verb in COMMON_VERBS):
            issues.append(linkify(f"❌ Contains verb-like segment: `{segment}`", "naming"))
            score_penalty -= 4

    if segments:
        last = segments[-1]
        if not re.search(r"s\b", last) and "{" not in last:
            issues.append(linkify(
                f"⚠️ Last segment `{last}` might not be plural (use plural for collections)",
                "naming"
            ))
            score_penalty -= 1

    if not issues:
        issues.append("✅ Resource naming looks RESTful")

    return issues, score_penalty