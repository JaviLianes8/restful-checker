from restful_checker.checks.check_result import CheckResult

def check_content_type(path: str, methods: dict) -> tuple[list[str], float]:
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
        request = operation.get("requestBody", {})
        if "content" in request:
            evaluated = True
            content_types = request["content"].keys()
            if "application/json" not in content_types:
                result.error(f"{method_upper} {path} requestBody does not use application/json")

        # Check responses
        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            content = response.get("content", {})
            if content:
                evaluated = True
                if "application/json" not in content:
                    result.error(f"{method_upper} {path} response {status_code} does not use application/json")

    if evaluated and not result.messages:
        result.success("All request and response bodies use application/json")
    elif not evaluated:
        result.success("No request or response bodies to validate")

    return result.messages, result.finalize_score()