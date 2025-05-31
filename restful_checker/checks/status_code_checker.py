from restful_checker.checks.check_result import CheckResult

EXPECTED_CODES = {
    "GET": {"200", "404"},
    "POST": {"201", "400", "409"},
    "PUT": {"200", "204", "400", "404"},
    "DELETE": {"204", "404"},
    "PATCH": {"200", "204", "400", "404"}
}

# === Individual Checks ===

def check_missing_responses(method, path, responses, result):
    if not responses:
        result.error(f"No status codes defined for {method} {path}")

def check_default_used(method, path, responses, result):
    if "default" in responses:
        result.warning(f"Default response used in {method} {path} — be explicit")

def check_missing_expected_codes(method, path, responses, result):
    expected = EXPECTED_CODES.get(method, set())
    missing = expected - responses
    if missing:
        result.warning(f"{method} {path} is missing expected status codes: {', '.join(sorted(missing))}")

def check_post_status_semantics(method, path, responses, result):
    if method == "POST":
        if "200" in responses and "201" not in responses:
            result.error(f"POST {path} returns 200 — should return 201 for creation")
        if "204" in responses:
            result.warning(f"POST {path} includes 204 — consider using 201 instead")

def check_delete_status_semantics(method, path, responses, result):
    if method == "DELETE" and "200" in responses and "204" not in responses:
        result.error(f"DELETE {path} returns 200 — should return 204 if successful")

def check_patch_put_semantics(method, path, responses, result):
    if method in {"PUT", "PATCH"}:
        if "200" not in responses and "204" not in responses:
            result.warning(f"{method} {path} missing 200 or 204 — consider returning success code")

def check_manual_5xx_usage(method, path, responses, result):
    for code in responses:
        if code.startswith("5"):
            result.warning(f"{method} {path} defines {code} manually — server errors should be implicit")

# === Main Function ===

def check_status_codes(path: str, method_map: dict):
    result = CheckResult("status_codes")

    for method, details in method_map.items():
        method_upper = method.upper()
        responses = set(details.get("responses", {}).keys())

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