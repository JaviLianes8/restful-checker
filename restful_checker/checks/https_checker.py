"""Whether the API is served over HTTPS: OpenAPI 3 servers or Swagger 2.0 schemes."""

from __future__ import annotations

import itertools
import re
from typing import Any

from restful_checker.checks.check_result import CheckResult

SECURE_SCHEMES = frozenset({"https", "wss"})
# A server URL with more combinations of variable values than this is read with the
# defaults only; real documents have a handful.
MAX_COMBINATIONS = 256
_VARIABLE = re.compile(r"\{([^{}]*)}")
_SCHEME = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*):")


def _values(variables: Any, name: str) -> list[str] | None:
    variable = variables.get(name) if isinstance(variables, dict) else None
    if not isinstance(variable, dict):
        return None
    enum = variable.get("enum")
    if isinstance(enum, list) and enum and all(isinstance(v, str) for v in enum):
        return list(dict.fromkeys(enum))
    default = variable.get("default")
    return [default] if isinstance(default, str) else None


def _expansions(url: str, variables: Any) -> list[str] | None:
    """Every URL the server can stand for, or None when a variable has no value."""
    names = list(dict.fromkeys(_VARIABLE.findall(url)))
    choices = [_values(variables, name) for name in names]
    if any(values is None for values in choices):
        return None
    lists = [values for values in choices if values is not None]
    total = 1
    for values in lists:
        total *= len(values)
    if total > MAX_COMBINATIONS:
        defaults = [variables[name].get("default") for name in names]
        lists = [[d] if isinstance(d, str) else v[:1] for d, v in zip(defaults, lists)]
    return [_fill(url, dict(zip(names, chosen))) for chosen in itertools.product(*lists)]


def _fill(url: str, chosen: dict[str, str]) -> str:
    return _VARIABLE.sub(lambda match: chosen[match.group(1)], url)


def server_kind(server: Any) -> str:
    """Classify an OpenAPI 3 Server Object: ``secure``, ``insecure``, ``relative`` or
    ``unresolved`` (a template variable without a ``default`` or ``enum``).

    Variables are replaced by every value of their ``enum`` (or their ``default``); one
    plain-HTTP outcome makes the server insecure. A URL without a scheme (``/api``,
    ``//host/api``) is relative to the document and served with its scheme.

    >>> server_kind({"url": "{scheme}://api.example.com",
    ...              "variables": {"scheme": {"default": "https"}}})
    'secure'
    >>> server_kind({"url": "/api"}), server_kind({"url": "http://api.example.com"})
    ('relative', 'insecure')
    """
    url = server.get("url") if isinstance(server, dict) else None
    if not isinstance(url, str) or not url:
        return "insecure"  # nothing to serve from: reported as before
    head = url.split("{", 1)[0]
    if "{" not in url or head.startswith("/") or (_SCHEME.match(head) and "//" in head):
        return _kind(url)  # the scheme does not depend on a variable
    urls = _expansions(url, server.get("variables"))
    if urls is None:
        return "unresolved"
    kinds = {_kind(expanded) for expanded in urls}
    for kind in ("insecure", "relative"):
        if kind in kinds:
            return kind
    return "secure"


def _kind(url: str) -> str:
    match = _SCHEME.match(url)
    if match is None:
        return "relative"
    if match.group(1).lower() in SECURE_SCHEMES and url[match.end() :][:2] == "//":
        return "secure"
    return "insecure"


def _swagger2(openapi_data: dict[str, Any], result: CheckResult) -> None:
    # Swagger 2.0 has `schemes` (and `host`), never `servers`. Without schemes the API uses
    # the scheme the document itself is served with.
    schemes = openapi_data.get("schemes")
    if not isinstance(schemes, list) or not schemes:
        result.success("No schemes listed: the API uses the scheme of the document")
    elif all(isinstance(s, str) and s.lower() in SECURE_SCHEMES for s in schemes):
        result.success("All servers use HTTPS")
    else:
        result.error("Not all servers use HTTPS")


def check_https_usage(openapi_data: dict[str, Any]) -> tuple[list[str], float]:
    """
    Check that all server URLs in the OpenAPI spec use HTTPS.

    OpenAPI 3 ``servers`` are read with their variables; relative URLs are served with the
    scheme of the document. A Swagger 2.0 document is judged by its ``schemes``.

    >>> check_https_usage({"openapi": "3.1.0", "servers": [{"url": "https://api.example.com"}]})
    (['✅ All servers use HTTPS'], 1.0)
    >>> check_https_usage({"swagger": "2.0", "schemes": ["http"]})
    (['❌ Not all servers use HTTPS'], 0.0)

    Args:
        openapi_data (dict): Parsed OpenAPI document.

    Returns:
        tuple[list[str], float]: List of messages and the computed score.
    """
    result = CheckResult("SSL")
    servers = openapi_data.get("servers", [])

    if "servers" not in openapi_data and "swagger" in openapi_data:
        _swagger2(openapi_data, result)
    elif not servers or not isinstance(servers, list):
        result.warning("No servers defined in OpenAPI spec")
    else:
        kinds = [server_kind(server) for server in servers]
        if "insecure" in kinds:
            result.error("Not all servers use HTTPS")
        elif "unresolved" in kinds:
            result.warning("A server URL uses a variable without a default or enum")
        elif "relative" in kinds:
            result.success("All servers use HTTPS or a URL relative to the document")
        else:
            result.success("All servers use HTTPS")

    return result.messages, result.finalize_score()
