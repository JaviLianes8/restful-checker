"""Status codes declared for the operations of one route."""

from __future__ import annotations

import re
from typing import Any

from restful_checker.checks.check_result import CheckResult

# Expected standard status codes per HTTP method
EXPECTED_CODES = {
    "GET": {"200", "404"},
    "POST": {"201", "400", "409"},
    "PUT": {"200", "204", "400", "404"},
    "DELETE": {"204", "404"},
    "PATCH": {"200", "204", "400", "404"},
}

RANGE_REGEX = re.compile(r"[1-5]XX", re.IGNORECASE)


def covers(responses: set[str], code: str) -> bool:
    """Tell whether the responses describe a status code, itself or by its range (`2XX`).

    >>> covers({"2XX", "404"}, "201"), covers({"200"}, "201")
    (True, False)
    """
    return code in responses or f"{code[0]}XX" in responses


# === Individual Checks ===


def check_missing_responses(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    if not responses:
        result.error(f"No status codes defined for {method} {path}")


def check_default_used(method: str, path: str, responses: set[str], result: CheckResult) -> None:
    if "default" in responses:
        result.warning(f"Default response used in {method} {path}, be explicit")


def check_missing_expected_codes(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    expected = EXPECTED_CODES.get(method, set())
    missing = {code for code in expected if not covers(responses, code)}
    if missing:
        result.warning(
            f"{method} {path} is missing expected status codes: {', '.join(sorted(missing))}"
        )


def check_post_status_semantics(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    if method == "POST":
        if "200" in responses and not covers(responses, "201"):
            result.error(f"POST {path} returns 200, should return 201 for creation")
        if "204" in responses:
            result.warning(f"POST {path} includes 204, consider using 201 instead")


def check_delete_status_semantics(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    if method == "DELETE" and "200" in responses and not covers(responses, "204"):
        result.error(f"DELETE {path} returns 200, should return 204 if successful")


def check_patch_put_semantics(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    if method in {"PUT", "PATCH"}:
        if not (covers(responses, "200") or covers(responses, "204")):
            result.warning(f"{method} {path} missing 200 or 204, consider returning success code")


def check_manual_5xx_usage(
    method: str, path: str, responses: set[str], result: CheckResult
) -> None:
    for code in responses:
        if code.startswith("5"):
            result.warning(
                f"{method} {path} defines {code} manually, server errors should be implicit"
            )


def _key(code: object) -> str:
    text = str(code)
    return text.upper() if RANGE_REGEX.fullmatch(text) else text


# === Main Function ===


def check_status_codes(path: str, method_map: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check status code usage for all HTTP methods in a given path.

    A range key such as ``2XX`` (OpenAPI 3) stands for every code of its class.

    >>> check_status_codes("/v1/users", {"get": {"responses": {"2XX": {}, "404": {}}}})
    (['✅ Status code definitions look valid'], 1.0)
    >>> check_status_codes("/v1/users", {"get": {"responses": {"200": {}}}})
    (['⚠️ GET /v1/users is missing expected status codes: 404'], 0.8)

    Args:
        path (str): The API path to evaluate.
        method_map (dict): HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
    result = CheckResult("status_codes")

    for method, details in method_map.items():
        if not isinstance(details, dict):
            continue  # not an Operation Object (path-level `parameters`, `summary`, ...)
        method_upper = str(method).upper()
        raw_responses = details.get("responses")
        # YAML reads an unquoted `200:` as an integer; ranges are read as `2XX`.
        responses = (
            {_key(code) for code in raw_responses} if isinstance(raw_responses, dict) else set()
        )

        check_missing_responses(method_upper, path, responses, result)

        if responses:
            check_default_used(method_upper, path, responses, result)
            check_missing_expected_codes(method_upper, path, responses, result)
            check_post_status_semantics(method_upper, path, responses, result)
            check_delete_status_semantics(method_upper, path, responses, result)
            check_patch_put_semantics(method_upper, path, responses, result)
            check_manual_5xx_usage(method_upper, path, responses, result)

    if not result.messages:
        result.success("Status code definitions look valid")

    return result.messages, result.finalize_score()
