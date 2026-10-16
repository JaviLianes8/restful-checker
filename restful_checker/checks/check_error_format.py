"""Structure of the error responses of one route."""

from __future__ import annotations

from typing import Any

from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.schema_tools import merged_properties

# The members RFC 9457 defines for a problem details object.
PROBLEM_MEMBERS = frozenset({"type", "title", "status", "detail", "instance"})
PROBLEM_MEDIA_TYPE = "application/problem+json"
PROBLEM_MEDIA_TYPES = frozenset({PROBLEM_MEDIA_TYPE, "application/problem+xml"})


def is_structured_error(media_type: object, schema: Any) -> bool:
    """Tell whether an error body has a structured format.

    It does when it is served as ``application/problem+json`` or ``application/problem+xml``
    (RFC 9457 defines their members), when its schema has both ``code`` and ``message``, or
    when its schema has at least two problem details members. Properties given through
    ``allOf`` count.

    >>> is_structured_error("application/json", {"properties": {"title": {}, "status": {}}})
    True
    >>> is_structured_error("application/json", {"properties": {"error": {}}})
    False
    """
    if isinstance(media_type, str):
        essence = media_type.split(";", 1)[0].strip().lower()
        if essence in PROBLEM_MEDIA_TYPES:
            return True
    properties = merged_properties(schema) or {}
    if "code" in properties and "message" in properties:
        return True
    return len(PROBLEM_MEMBERS.intersection(properties)) >= 2


def check_error_format(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that 4xx/5xx responses use a structured error format: 'code' and 'message'
    fields, or RFC 9457 problem details.

    >>> problem = {"content": {"application/problem+json": {}}}
    >>> check_error_format("/v1/users", {"get": {"responses": {"404": problem}}})[1]
    1.0
    >>> bare = {"content": {"application/json": {"schema": {"type": "string"}}}}
    >>> check_error_format("/v1/users", {"get": {"responses": {"404": bare}}})[0]
    ['⚠️ GET /v1/users error 404 has no structured schema']

    Args:
        path (str): API path being evaluated.
        methods (dict): Dictionary of HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: A list of result messages and the associated score.
    """
    result = CheckResult("error_format")
    evaluated = False

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for status_code, response in responses.items():
            if not isinstance(response, dict):
                continue
            if status_code == "default" or str(status_code).startswith(("4", "5")):
                content = response.get("content")
                if not isinstance(content, dict):
                    continue
                for media_type, media_info in content.items():
                    evaluated = True
                    schema = media_info.get("schema", {}) if isinstance(media_info, dict) else {}
                    if is_structured_error(media_type, schema):
                        continue
                    label = f"{str(method_name).upper()} {path} error {status_code}"
                    if merged_properties(schema) is None:
                        result.warning(f"{label} has no structured schema")
                    else:
                        result.warning(
                            f"{label} should include 'code' and 'message' fields "
                            "or RFC 9457 problem details members"
                        )

    if evaluated and not result.messages:
        result.success("All error responses use 'code' and 'message' or problem details")
    elif not evaluated:
        result.success("No 4xx or 5xx responses to validate")

    return result.messages, result.finalize_score()
