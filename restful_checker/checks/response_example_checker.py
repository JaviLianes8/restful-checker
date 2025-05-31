from restful_checker.checks.check_result import CheckResult

def check_response_examples(path: str, methods: dict) -> tuple[list[str], float]:
    result = CheckResult("ResponseExamples")
    evaluated = False
    seen = set()

    for method_name, operation in methods.items():
        if not isinstance(operation, dict):
            continue

        responses = operation.get("responses", {})
        for status, response in responses.items():
            content = response.get("content", {})
            if not content:
                continue

            evaluated = True
            has_example = any(
                "example" in media or "examples" in media
                for media in content.values()
            )

            if not has_example:
                key = (method_name.upper(), path, status)
                if key not in seen:
                    seen.add(key)
                    result.warning(
                        f"{method_name.upper()} {path} response {status} is missing example or examples"
                    )

    if not evaluated:
        result.success("No response bodies to evaluate for examples")
    elif not result.messages:
        result.success("All responses define at least one example")

    return result.messages, result.finalize_score()