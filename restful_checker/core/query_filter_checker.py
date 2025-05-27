import re
from .rest_docs import linkify

class QueryFilterCheckResult:
    def __init__(self):
        self.messages = []
        self.has_error = False
        self.has_warning = False

    def error(self, msg):
        self.messages.append(linkify(f"❌ {msg}", "query_filters"))
        self.has_error = True

    def warning(self, msg):
        self.messages.append(linkify(f"⚠️ {msg}", "query_filters"))
        self.has_warning = True

    def finalize_score(self):
        if self.has_error:
            return -2
        if self.has_warning:
            return -1
        return 0

# === Main Function ===

def check_query_filters(path: str, methods: dict):
    result = QueryFilterCheckResult()

    if re.search(r"/\{[^}]+\}$", path):
        return result.messages or ["✅ Skipped query filter check (single resource)"], result.finalize_score()

    if "get" in methods:
        get_op = methods.get("get", {})
        parameters = get_op.get("parameters", [])
        query_params = [p for p in parameters if p.get("in") == "query"]

        if not query_params:
            result.warning(
                f"GET collection endpoint `{path}` has no query filters — consider supporting `?filter=` or `?status=`"
            )
        else:
            # Check if the query param names are meaningful
            useful_names = {"filter", "status", "type", "sort", "limit"}
            meaningful = any(p.get("name", "").lower() in useful_names for p in query_params)
            if not meaningful:
                result.warning(
                    f"GET {path} has query params but none look like useful filters (e.g., `filter`, `status`)"
                )

            # Optional: check for undefined or badly typed filters
            for p in query_params:
                if "type" in p.get("schema", {}):
                    if p["schema"]["type"] == "object":
                        result.warning(f"Query parameter `{p.get('name')}` has type `object` — consider using primitives")
                else:
                    result.warning(f"Query parameter `{p.get('name')}` has no defined type")

    if not result.messages:
        result.messages.append("✅ Collection endpoints support query filters")

    return result.messages, result.finalize_score()