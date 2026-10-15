from __future__ import annotations

from typing import Any

from restful_checker.checks.check_result import CheckResult

def check_https_usage(openapi_data: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that all server URLs in the OpenAPI spec use HTTPS.

    Args:
        openapi_data (dict): Parsed OpenAPI document.

    Returns:
        tuple[list[str], float]: List of messages and the computed score.
    """
    result = CheckResult("SSL")
    servers = openapi_data.get("servers", [])

    if not servers or not isinstance(servers, list):
        result.warning("No servers defined in OpenAPI spec")
    else:
        all_https = all(
            isinstance(s, dict) and str(s.get("url", "")).startswith("https://") for s in servers
        )
        if all_https:
            result.success("All servers use HTTPS")
        else:
            result.error("Not all servers use HTTPS")

    return result.messages, result.finalize_score()
