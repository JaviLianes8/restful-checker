from restful_checker.checks.check_result import CheckResult

def check_error_format(path: str, methods: dict) -> tuple[list[str], float]:
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
                        result.warning(f"{method_name.upper()} {path} error {status_code} has no structured error schema")
                    else:
                        properties = schema["properties"]
                        if not all(key in properties for key in ("code", "message")):
                            result.warning(
                                f"{method_name.upper()} {path} error {status_code} response should include 'code' and 'message' fields"
                            )

    if evaluated and not result.messages:
        result.success("Error responses follow a consistent schema with 'code' and 'message'")
    elif not evaluated:
        result.success("No error responses to validate")

    return result.messages, result.finalize_score()