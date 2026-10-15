from __future__ import annotations

from typing import Any

from restful_checker.checks.check_result import CheckResult


def is_json_media_type(media_type: object) -> bool:
    """Tell whether a media type is JSON: application/json, with or without parameters,
    or any type with the +json structured syntax suffix (RFC 6839), such as
    application/problem+json (RFC 9457)."""
    if not isinstance(media_type, str):
        return False
    essence = media_type.split(";", 1)[0].strip().lower()
    return essence == "application/json" or ("/" in essence and essence.endswith("+json"))


def check_content_type(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that all request and response bodies use 'application/json'.

    Args:
        path (str): The API path being checked.
        methods (dict): HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: A list of result messages and the computed score.
    """
    result = CheckResult("ContentType")
    evaluated = False

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        method_upper = method_name.upper()

        # Check request body
        request = operation.get("requestBody") or {}
        if isinstance(request, dict) and isinstance(request.get("content"), dict):
            evaluated = True
            content_types = request["content"].keys()
            if not any(is_json_media_type(media) for media in content_types):
                result.error(f"{method_upper} {path} requestBody does not use application/json")

        # Check responses
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for status_code, response in responses.items():
            content = response.get("content") if isinstance(response, dict) else None
            if content and isinstance(content, dict):
                evaluated = True
                if not any(is_json_media_type(media) for media in content):
                    result.error(
                        f"{method_upper} {path} response {status_code} does not use "
                        "application/json"
                    )

    if evaluated and not result.messages:
        result.success("All request and response bodies use application/json")
    elif not evaluated:
        result.success("No request or response bodies to validate")

    return result.messages, result.finalize_score()
