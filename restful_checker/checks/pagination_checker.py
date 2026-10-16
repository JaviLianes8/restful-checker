"""Pagination parameters of collection GET operations."""

from __future__ import annotations

import re
from typing import Any

from restful_checker.checks.check_result import CheckResult

# Page-number, offset and cursor styles, in snake and camel case; JSON:API uses `page[...]`.
PAGINATION_PARAMETERS = frozenset(
    {"page", "limit", "offset", "cursor", "per_page", "perpage", "page_size", "pagesize",
     "page_token", "pagetoken"}
)  # fmt: skip


def is_pagination_parameter(name: object) -> bool:
    """Tell whether a parameter name pages through a collection (compared case-insensitively).

    >>> [is_pagination_parameter(n) for n in ("offset", "perPage", "page[size]", "sort")]
    [True, True, True, False]
    """
    if not isinstance(name, str):
        return False
    lowered = name.lower()
    return lowered in PAGINATION_PARAMETERS or (
        lowered.startswith("page[") and lowered.endswith("]")
    )


def check_pagination(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that GET operations on the given path support pagination parameters.

    Looks for a pagination parameter: ``page``, ``limit``, ``offset``, ``cursor``,
    ``per_page``, ``page_size``, ``page_token`` (or their camel-case forms) or a JSON:API
    ``page[...]`` parameter. Single resources such as ``/users/{id}`` are skipped.

    >>> get = {"get": {"parameters": [{"name": "cursor", "in": "query"}]}}
    >>> check_pagination("/v1/users", get)
    (['✅ GET endpoints support pagination parameters'], 1.0)
    >>> check_pagination("/v1/users", {"get": {}})[1]
    0.8

    Args:
        path (str): The API path being analyzed.
        methods (dict): Dictionary of HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: A list of messages and the computed score.
    """
    result = CheckResult("Pagination")
    evaluated = False

    # A single resource such as /users/{id} is not a collection: nothing to page through.
    if re.search(r"/\{[^{}]+}/?$", path):
        result.success("Skipped pagination check (single resource)")
        return result.messages, result.finalize_score()

    for method_name, operation in methods.items():
        if str(method_name).lower() != "get" or not isinstance(operation, dict):
            continue

        evaluated = True
        parameters = operation.get("parameters") or []
        names = [p.get("name") for p in parameters if isinstance(p, dict)]

        if not any(is_pagination_parameter(name) for name in names):
            result.warning(
                f"GET {path} does not support pagination parameters (e.g., `page`, `limit`)"
            )

    if evaluated and not result.messages:
        result.success("GET endpoints support pagination parameters")
    elif not evaluated:
        result.success("No GET operations to validate for pagination")

    return result.messages, result.finalize_score()
