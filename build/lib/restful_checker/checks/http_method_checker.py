import re
from restful_checker.checks.check_result import CheckResult

VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
ACTIONS_FOR_GET = {"create", "update", "delete", "remove"}
ACTIONS_FOR_POST_DELETE = {"delete", "remove"}
ACTIONS_FOR_PUT_CREATE = {"create"}

# === Individual Checks ===

def check_unusual_method(method, result):
    if method.upper() not in VALID_METHODS:
        result.warning(f"Unusual HTTP method used: {method}")

def check_get_with_action(path, method, result):
    if method == "GET":
        for action in ACTIONS_FOR_GET:
            if action in path.lower():
                result.error(f"GET used for action-like path: `{path}` — consider using POST instead")
                break

def check_post_with_delete(path, method, result):
    if method == "POST":
        for action in ACTIONS_FOR_POST_DELETE:
            if action in path.lower():
                result.error(f"POST used for deletion-like path: `{path}` — consider using DELETE")
                break

def check_put_with_create(path, method, result):
    if method == "PUT":
        for action in ACTIONS_FOR_PUT_CREATE:
            if action in path.lower():
                result.warning(f"PUT used for creation-like path: `{path}` — consider using POST")
                break

def check_get_with_side_effect(path, method, result):
    if method == "GET":
        for verb in ["reset", "execute", "trigger", "start"]:
            if verb in path.lower():
                result.error(f"GET used for side-effect path: `{path}` — should be POST or PUT")
                break

def check_post_on_resource_id(path, method, result):
    if method == "POST":
        if re.search(r"/\{[^}]+}", path):
            result.warning(f"POST used with resource ID in path `{path}` — consider using PUT or PATCH")

def check_delete_without_id(path, method, result):
    if method == "DELETE":
        if not re.search(r"/\{[^}]+}", path):
            result.warning(f"DELETE without ID in path `{path}` — consider confirming if this is intentional")

# === Main Function ===

def check_http_methods(path: str, methods: set):
    result = CheckResult("http_methods")

    for method in methods:
        check_unusual_method(method, result)
        check_get_with_action(path, method, result)
        check_post_with_delete(path, method, result)
        check_put_with_create(path, method, result)
        check_get_with_side_effect(path, method, result)
        check_post_on_resource_id(path, method, result)
        check_delete_without_id(path, method, result)

    if not result.messages:
        result.success("HTTP method usage looks valid")

    return result.messages, result.finalize_score()