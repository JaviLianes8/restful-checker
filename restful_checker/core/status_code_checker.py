from .rest_docs import linkify

EXPECTED_CODES = {
    "GET": {"200", "404"},
    "POST": {"201", "400", "409"},
    "PUT": {"200", "204", "400", "404"},
    "DELETE": {"204", "404"},
    "PATCH": {"200", "204", "400", "404"}
}

def check_status_codes(path: str, method_map: dict):
    issues = []
    penalty = 0

    for method, details in method_map.items():
        method_upper = method.upper()
        expected = EXPECTED_CODES.get(method_upper, set())
        responses = set(details.get("responses", {}).keys())

        if not responses:
            issues.append(linkify(f"❌ No status codes defined for {method_upper} {path}", "status_codes"))
            penalty -= 5
            continue

        if "default" in responses:
            issues.append(linkify(f"⚠️ Default response used in {method_upper} {path} — be explicit", "status_codes"))
            penalty -= 1

        missing = expected - responses
        if missing:
            issues.append(linkify(f"⚠️ {method_upper} {path} is missing expected status codes: {', '.join(sorted(missing))}", "status_codes"))
            penalty -= len(missing)

    if not issues:
        issues.append("✅ Status code definitions look valid")

    return issues, penalty