"""HTTP method semantics of the operations of one route."""

from __future__ import annotations

import re

from restful_checker.checks.check_result import CheckResult
from restful_checker.checks.verb_words import contains_verb, words

# The methods RFC 9110 registers that OpenAPI has a field for, PATCH (RFC 5789) and the
# QUERY operation of OpenAPI 3.2. CONNECT has no Path Item field.
VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "QUERY"}
ACTIONS_FOR_GET = {"create", "update", "delete", "remove"}
ACTIONS_FOR_POST_DELETE = {"delete", "remove"}
ACTIONS_FOR_PUT_CREATE = {"create"}


def _has_word(path: str, verb: str) -> bool:
    # Words, not substrings: matching substrings flagged `presets` (reset) and `restarts`
    # (start); compounds such as `deleteUser`, `resetpassword` or `userdelete` still count.
    return any(contains_verb(word, verb) for word in words(path))


# === Individual Checks ===


def check_unusual_method(method: str, result: CheckResult) -> None:
    if method.upper() not in VALID_METHODS:
        result.warning(f"Unusual HTTP method used: {method}")


def check_get_with_action(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "GET":
        for action in ACTIONS_FOR_GET:
            if _has_word(path, action):
                result.error(
                    f"GET used for action-like path: `{path}`, consider using POST instead"
                )
                break


def check_post_with_delete(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "POST":
        for action in ACTIONS_FOR_POST_DELETE:
            if _has_word(path, action):
                result.error(f"POST used for deletion-like path: `{path}`, consider using DELETE")
                break


def check_put_with_create(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "PUT":
        for action in ACTIONS_FOR_PUT_CREATE:
            if _has_word(path, action):
                result.warning(f"PUT used for creation-like path: `{path}`, consider using POST")
                break


def check_get_with_side_effect(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "GET":
        for verb in ["reset", "execute", "trigger", "start"]:
            if _has_word(path, verb):
                result.error(f"GET used for side-effect path: `{path}`, should be POST or PUT")
                break


def check_post_on_resource_id(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "POST":
        if re.search(r"/\{[^}]+}", path):
            result.warning(
                f"POST used with resource ID in path `{path}`, consider using PUT or PATCH"
            )


def check_delete_without_id(path: str, method: str, result: CheckResult) -> None:
    if method.upper() == "DELETE":
        if not re.search(r"/\{[^}]+}", path):
            result.warning(
                f"DELETE without ID in path `{path}`, consider confirming if this is intentional"
            )


# === Main Function ===


def check_http_methods(path: str, methods: set[str]) -> tuple[list[str], float]:
    """
    Analyze a set of HTTP methods for RESTful convention violations.

    >>> check_http_methods("/v1/users", {"GET", "HEAD", "OPTIONS"})
    (['✅ HTTP method usage looks valid'], 1.0)
    >>> check_http_methods("/v1/resetPassword", {"GET"})[0]
    ['❌ GET used for side-effect path: `/v1/resetPassword`, should be POST or PUT']

    Args:
        path (str): API path to analyze.
        methods (set[str]): HTTP methods used in that path.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
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
