from restful_checker.checks.check_result import CheckResult

def check_error_format(path: str, methods: dict) -> tuple[list[str], float]:
    """
    Check that 4xx/5xx responses use a structured error format
    including at least 'code' and 'message' fields.

    Args:
        path (str): API path being evaluated.
        methods (dict): Dictionary of HTTP methods and their OpenAPI definitions.

    Returns:
        tuple[list[str], float]: A list of result messages and the associated score.
    """
    result = CheckResult("error_format")
    evaluated = False

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            if status_code == "default" or str(status_code).startswith(("4", "5")):
                content = response.get("content", {})
                for media_type, media_info in content.items():
                    evaluated = True
                    schema = media_info.get("schema", {})

                    if "properties" not in schema:
                        result.warning(
                            f"{method_name.upper()} {path} error {status_code} has no structured schema"
                        )
                    else:
                        properties = schema["properties"]
                        required_keys = ("code", "message")
                        if not all(key in properties for key in required_keys):
                            result.warning(
                                f"{method_name.upper()} {path} error {status_code} should include 'code' and 'message' fields"
                            )

    if evaluated and not result.messages:
        result.success("All error responses include 'code' and 'message'")
    elif not evaluated:
        result.success("No 4xx or 5xx responses to validate")

    return result.messages, result.finalize_score()