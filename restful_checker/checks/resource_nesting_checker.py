from restful_checker.checks.check_result import CheckResult
import re

def check_resource_nesting(path: str, methods: dict) -> tuple[list[str], float]:
    result = CheckResult("ResourceNesting")

    segments = path.strip("/").split("/")

    for i in range(len(segments) - 1):
        current = segments[i]
        next_segment = segments[i + 1]

        is_current_id = re.fullmatch(r"\{[^{}]+}", current)
        is_next_id = re.fullmatch(r"\{[^{}]+}", next_segment)

        if not is_current_id and not next_segment.startswith("{"):
            if next_segment.endswith("s") and current.endswith("s"):
                result.error(f"Route '{path}' may be missing parent ID in nesting (e.g., /{current}/{{id}}/{next_segment})")

        if is_current_id and is_next_id:
            result.warning(f"Route '{path}' contains multiple consecutive IDs — check if nesting is appropriate")

    if not result.messages:
        result.success("Route nesting appears valid")

    return result.messages, result.finalize_score()