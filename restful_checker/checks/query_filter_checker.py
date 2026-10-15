from __future__ import annotations

import re
from typing import Any

from restful_checker.checks.check_result import CheckResult


def check_query_filters(path: str, methods: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that GET collection endpoints support meaningful query filters.

    Skips paths that point to a single resource (ending in /{id}).

    Args:
        path (str): The API path to check.
        methods (dict): OpenAPI method definitions for that path.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
    result = CheckResult("query_filters")

    # Skip if it's a single-resource path like /users/{id}
    if re.search(r"/\{[^}]+}/?$", path):
        result.success("Skipped query filter check (single resource)")
        return result.messages, result.finalize_score()

    get_op = methods.get("get")
    if not isinstance(get_op, dict):
        result.success("No GET operation to validate for filters")
        return result.messages, result.finalize_score()

    parameters = get_op.get("parameters") or []
    query_params = [p for p in parameters if isinstance(p, dict) and p.get("in") == "query"]

    if not query_params:
        result.warning(
            f"GET collection endpoint `{path}` has no query filters, consider supporting "
            "`?filter=` or `?status=`"
        )
    else:
        useful_names = {"filter", "status", "type", "sort", "limit"}
        has_meaningful = any(str(p.get("name", "")).lower() in useful_names for p in query_params)

        if not has_meaningful:
            result.warning(
                f"GET {path} has query params but none look like useful filters (e.g., `filter`, "
                "`status`)"
            )

        for param in query_params:
            name = param.get("name", "")
            schema = param.get("schema", {})
            # OpenAPI 2.0 puts `type` on the parameter itself, 3.x inside `schema`.
            param_type = schema.get("type") if isinstance(schema, dict) else None
            param_type = param_type or param.get("type")

            if param_type == "object":
                result.warning(
                    f"Query parameter `{name}` has type `object`, consider using primitives"
                )
            elif not param_type:
                result.warning(f"Query parameter `{name}` has no defined type")

    if not result.messages:
        result.success("Collection endpoints support query filters")

    return result.messages, result.finalize_score()
