"""Media types of the request and response bodies of one route."""

from __future__ import annotations

from typing import Any

from restful_checker.checks.check_result import CheckResult


def is_json_media_type(media_type: object) -> bool:
    """Tell whether a media type is JSON: application/json, with or without parameters,
    or any type with the +json structured syntax suffix (RFC 6839), such as
    application/problem+json (RFC 9457).

    >>> is_json_media_type("application/json; charset=utf-8"), is_json_media_type("text/xml")
    (True, False)
    """
    if not isinstance(media_type, str):
        return False
    essence = media_type.split(";", 1)[0].strip().lower()
    return essence == "application/json" or ("/" in essence and essence.endswith("+json"))


# Bodies that have no JSON form: files and multipart uploads.
BINARY_MEDIA_TYPES = frozenset(
    {"application/octet-stream", "application/pdf", "application/zip", "application/gzip"}
)
BINARY_TOP_LEVEL = ("image/", "audio/", "video/", "font/", "multipart/")


def is_binary_media_type(media_type: object, media: object = None) -> bool:
    """Tell whether a body is binary or multipart, so JSON is not expected of it.

    That is ``application/octet-stream``, ``application/pdf``, ``application/zip``,
    ``application/gzip``, any ``image``, ``audio``, ``video``, ``font`` or ``multipart``
    type, or any media type whose schema is ``type: string`` with ``format: binary``
    (the OpenAPI 3.0 way of describing file contents).

    >>> is_binary_media_type("multipart/form-data"), is_binary_media_type("text/csv")
    (True, False)
    >>> is_binary_media_type("text/plain", {"schema": {"type": "string", "format": "binary"}})
    True
    """
    if not isinstance(media_type, str):
        return False
    essence = media_type.split(";", 1)[0].strip().lower()
    if essence in BINARY_MEDIA_TYPES or essence.startswith(BINARY_TOP_LEVEL):
        return True
    schema = media.get("schema") if isinstance(media, dict) else None
    return isinstance(schema, dict) and (schema.get("type"), schema.get("format")) == (
        "string",
        "binary",
    )


def _accepted(content: dict[Any, Any]) -> tuple[bool, bool]:
    # (accepted, accepted only because it is binary or multipart)
    if any(is_json_media_type(media_type) for media_type in content):
        return True, False
    binary = any(is_binary_media_type(name, media) for name, media in content.items())
    return binary, binary


def check_content_type(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that all request and response bodies use 'application/json'.

    A JSON media type with parameters or a ``+json`` suffix counts, and so does a binary or
    multipart body (see ``is_binary_media_type``), which has no JSON form.

    >>> upload = {"requestBody": {"content": {"multipart/form-data": {}}}}
    >>> check_content_type("/v1/files", {"post": upload})[1]
    1.0
    >>> xml = {"responses": {"200": {"content": {"application/xml": {}}}}}
    >>> check_content_type("/v1/users", {"get": xml})
    (['❌ GET /v1/users response 200 does not use application/json'], 0.0)

    Args:
        path (str): The API path being checked.
        methods (dict): HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: A list of result messages and the computed score.
    """
    result = CheckResult("ContentType")
    evaluated = False
    binary_seen = False

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        method_upper = method_name.upper()

        # Check request body
        request = operation.get("requestBody") or {}
        if isinstance(request, dict) and isinstance(request.get("content"), dict):
            evaluated = True
            accepted, binary = _accepted(request["content"])
            binary_seen = binary_seen or binary
            if not accepted:
                result.error(f"{method_upper} {path} requestBody does not use application/json")

        # Check responses
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for status_code, response in responses.items():
            content = response.get("content") if isinstance(response, dict) else None
            if content and isinstance(content, dict):
                evaluated = True
                accepted, binary = _accepted(content)
                binary_seen = binary_seen or binary
                if not accepted:
                    result.error(
                        f"{method_upper} {path} response {status_code} does not use "
                        "application/json"
                    )

    if evaluated and not result.messages and binary_seen:
        result.success(
            "All request and response bodies use application/json, binary or multipart types"
        )
    elif evaluated and not result.messages:
        result.success("All request and response bodies use application/json")
    elif not evaluated:
        result.success("No request or response bodies to validate")

    return result.messages, result.finalize_score()
