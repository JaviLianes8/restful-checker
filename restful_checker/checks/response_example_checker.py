"""Examples of the response bodies of one route."""

from __future__ import annotations

from typing import Any

from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.schema_tools import has_example as schema_has_example


def check_response_examples(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that each response defines at least one example.

    Accepts `example` or `examples` in the media type block or in its schema (also
    through ``allOf``). Skips content-less responses. Avoids duplicate warnings per
    method/status.

    >>> media = {"schema": {"type": "object", "example": {"id": 1}}}
    >>> ok = {"responses": {"200": {"content": {"application/json": media}}}}
    >>> check_response_examples("/v1/users", {"get": ok})
    (['✅ All responses define at least one example'], 1.0)

    Args:
        path (str): API path being evaluated.
        methods (dict): HTTP method definitions for this path.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
    result = CheckResult("ResponseExamples")
    evaluated = False
    seen: set[tuple[str, str, str]] = set()

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for status_code, response in responses.items():
            content = response.get("content") if isinstance(response, dict) else None
            if not content or not isinstance(content, dict):
                continue

            evaluated = True
            has_example = any(
                isinstance(media, dict)
                and (
                    "example" in media
                    or "examples" in media
                    or schema_has_example(media.get("schema"))
                )
                for media in content.values()
            )

            if not has_example:
                key = (method_name.upper(), path, str(status_code))
                if key not in seen:
                    seen.add(key)
                    result.warning(
                        f"{method_name.upper()} {path} response {status_code} is missing example "
                        "or examples"
                    )

    if not evaluated:
        result.success("No response bodies to evaluate for examples")
    elif not result.messages:
        result.success("All responses define at least one example")

    return result.messages, result.finalize_score()
