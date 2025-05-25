from .rest_docs import linkify

def check_query_filters(path: str, methods: dict):
    issues = []
    penalty = 0

    if not path.endswith("}") and "get" in methods:
        get_op = methods.get("get", {})
        parameters = get_op.get("parameters", [])

        query_params = [p for p in parameters if p.get("in") == "query"]

        if not query_params:
            issues.append(linkify(
                f"⚠️ GET collection endpoint `{path}` has no query filters — consider supporting `?filter=` or `?status=`",
                "query_filters"
            ))
            penalty -= 1

    if not issues:
        issues.append("✅ Collection endpoints support query filters")

    return issues, penalty