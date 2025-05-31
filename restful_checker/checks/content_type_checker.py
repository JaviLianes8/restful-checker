from restful_checker.checks.check_result import CheckResult

def check_content_type(path: str, methods: dict) -> tuple[list[str], float]:
    result = CheckResult("ContentType")
    evaluated = False

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        request = operation.get("requestBody", {})
        if "content" in request:
            evaluated = True
            content_types = request["content"].keys()
            if "application/json" not in content_types:
                result.error(f"{method_name.upper()} {path} requestBody does not use application/json")

        responses = operation.get("responses", {})
        for status, response in responses.items():
            content = response.get("content", {})
            if content:
                evaluated = True
                if "application/json" not in content:
                    result.error(f"{method_name.upper()} {path} response {status} does not use application/json")

    if evaluated and not result.messages:
        result.success("All request and response bodies use application/json")
    elif not evaluated:
        result.success("No request or response bodies to validate")

    return result.messages, result.finalize_score()