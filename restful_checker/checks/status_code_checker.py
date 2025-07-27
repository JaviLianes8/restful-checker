from restful_checker.checks.check_result import CheckResult

# Expected standard status codes per HTTP method
EXPECTED_CODES = {
    "GET": {"200", "404"},
    "POST": {"201", "400", "409"},
    "PUT": {"200", "204", "400", "404"},
    "DELETE": {"204", "404"},
    "PATCH": {"200", "204", "400", "404"},
}

# === Individual Checks ===

def check_missing_responses(method: str, path: str, responses: set[str], result: CheckResult):
    if not responses:
        result.error(f"No status codes defined for {method} {path}")

def check_default_used(method: str, path: str, responses: set[str], result: CheckResult):
    if "default" in responses:
        result.warning(f"Default response used in {method} {path} — be explicit")

def check_missing_expected_codes(method: str, path: str, responses: set[str], result: CheckResult):
    expected = EXPECTED_CODES.get(method, set())
    missing = expected - responses
    if missing:
        result.warning(f"{method} {path} is missing expected status codes: {', '.join(sorted(missing))}")

def check_post_status_semantics(method: str, path: str, responses: set[str], result: CheckResult):
    if method == "POST":
        if "200" in responses and "201" not in responses:
            result.error(f"POST {path} returns 200 — should return 201 for creation")
        if "204" in responses:
            result.warning(f"POST {path} includes 204 — consider using 201 instead")

def check_delete_status_semantics(method: str, path: str, responses: set[str], result: CheckResult):
    if method == "DELETE" and "200" in responses and "204" not in responses:
        result.error(f"DELETE {path} returns 200 — should return 204 if successful")

def check_patch_put_semantics(method: str, path: str, responses: set[str], result: CheckResult):
    if method in {"PUT", "PATCH"}:
        if not {"200", "204"} & responses:
            result.warning(f"{method} {path} missing 200 or 204 — consider returning success code")

def check_manual_5xx_usage(method: str, path: str, responses: set[str], result: CheckResult):
    for code in responses:
        if code.startswith("5"):
            result.warning(f"{method} {path} defines {code} manually — server errors should be implicit")

# === Main Function ===

def check_status_codes(path: str, method_map: dict) -> tuple[list[str], float]:
    """
    Check status code usage for all HTTP methods in a given path.

    Args:
        path (str): The API path to evaluate.
        method_map (dict): HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
    result = CheckResult("status_codes")

    for method, details in method_map.items():
        method_upper = method.upper()
        response_keys = details.get("responses", {}).keys()
        responses = set(response_keys)

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
