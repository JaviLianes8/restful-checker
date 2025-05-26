from .rest_docs import linkify

def check_http_methods(path: str, methods: set):
    issues = []
    penalty = 0

    for method in methods:
        m_lower = method.lower()
        p_lower = path.lower()

        if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            issues.append(linkify(f"⚠️ Unusual HTTP method used: {method}", "http_methods"))
            penalty -= 1

        if method == "GET" and any(action in p_lower for action in ["create", "update", "delete", "remove"]):
            issues.append(linkify(
                f"❌ GET used for action-like path: `{path}` — consider using POST instead",
                "http_methods"
            ))
            penalty -= 4

        if method == "POST" and any(action in p_lower for action in ["delete", "remove"]):
            issues.append(linkify(
                f"❌ POST used for deletion-like path: `{path}` — consider using DELETE",
                "http_methods"
            ))
            penalty -= 4

        if method == "PUT" and "create" in p_lower:
            issues.append(linkify(
                f"⚠️ PUT used for creation-like path: `{path}` — consider using POST",
                "http_methods"
            ))
            penalty -= 2

    if not issues:
        issues.append("✅ HTTP method usage looks valid")

    return issues, penalty