import re
from restful_checker.checks.check_result import CheckResult

# === Main Function ===

def check_query_filters(path: str, methods: dict):
    result = CheckResult("query_filters")

    if re.search(r"/\{[^}]+}$", path):
        result.success("Skipped query filter check (single resource)")
        return result.messages, result.finalize_score()

    if "get" in methods:
        get_op = methods.get("get", {})
        parameters = get_op.get("parameters", [])
        query_params = [p for p in parameters if p.get("in") == "query"]

        if not query_params:
            result.warning(
                f"GET collection endpoint `{path}` has no query filters — consider supporting `?filter=` or `?status=`"
            )
        else:
            useful_names = {"filter", "status", "type", "sort", "limit"}
            meaningful = any(p.get("name", "").lower() in useful_names for p in query_params)
            if not meaningful:
                result.warning(
                    f"GET {path} has query params but none look like useful filters (e.g., `filter`, `status`)"
                )

            for p in query_params:
                schema = p.get("schema", {})
                if "type" in schema:
                    if schema["type"] == "object":
                        result.warning(f"Query parameter `{p.get('name')}` has type `object` — consider using primitives")
                else:
                    result.warning(f"Query parameter `{p.get('name')}` has no defined type")

    if not result.messages:
        result.success("Collection endpoints support query filters")

    return result.messages, result.finalize_score()