from restful_checker.checks.check_result import CheckResult

def check_pagination(path: str, methods: dict) -> tuple[list[str], float]:
    result = CheckResult("Pagination")
    evaluated = False

    for method_name, operation in methods.items():
        if method_name.lower() != "get" or not isinstance(operation, dict):
            continue

        evaluated = True
        parameters = operation.get("parameters", [])
        param_names = {p.get("name", "") for p in parameters if isinstance(p, dict)}

        if not {"page", "limit"}.intersection(param_names):
            result.warning(
                f"GET {path} does not support pagination parameters (e.g., `page`, `limit`)"
            )

    if evaluated and not result.messages:
        result.success("GET endpoints support pagination parameters")
    elif not evaluated:
        result.success("No GET operations to validate for pagination")

    return result.messages, result.finalize_score()