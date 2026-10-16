"""Read the Paths Object the way the OpenAPI specification defines it.

The checks receive plain dictionaries: only real operations, every local ``$ref`` they need
followed (parameter and media schemas and their ``allOf``, ``oneOf`` and ``anyOf`` members
included), path-level parameters merged in and status codes as strings. References to other
files or URLs are left as they are. The document passed in is never modified.
"""

from __future__ import annotations

from typing import Any

from restful_checker.engine.references import COMPOSITION_KEYS as COMPOSITION_KEYS
from restful_checker.engine.references import _pointer as _pointer
from restful_checker.engine.references import _schema
from restful_checker.engine.references import resolve as resolve

# References let a few bytes stand for many operations and responses (each one a check, a
# report line): past this many the document is refused instead of growing without bound.
MAX_UNITS = 50_000  # GitHub's 13 MB REST description uses about 5,000

# Path Item fields holding an Operation Object (OpenAPI 2.0 to 3.2; `query` is new in 3.2).
OPERATION_KEYS = ("get", "put", "post", "delete", "options", "head", "patch", "trace", "query")


def _parameter(param: Any, root: Any) -> Any:
    param = resolve(param, root)
    if isinstance(param, dict) and "schema" in param:
        param = {**param, "schema": _schema(param["schema"], root)}
    if isinstance(param, dict) and "content" in param:
        param = {**param, "content": _media(param["content"], root)}
    return param


def _parameters(raw: Any, root: Any) -> list[Any]:
    if not isinstance(raw, list):
        return []
    return [_parameter(param, root) for param in raw]


def _merge_parameters(shared: list[Any], own: list[Any]) -> list[Any]:
    # Operation parameters override path-level ones with the same name and location.
    def key(param: Any) -> tuple[Any, Any] | None:
        return (param.get("name"), param.get("in")) if isinstance(param, dict) else None

    own_keys = {key(param) for param in own} - {None}
    return [param for param in shared if key(param) not in own_keys] + own


def _media(content: Any, root: Any) -> dict[Any, Any]:
    if not isinstance(content, dict):
        return {}  # malformed content reads as no content
    result: dict[Any, Any] = {}
    for media_type, media in content.items():
        media = resolve(media, root)
        for key in ("schema", "itemSchema"):  # `itemSchema`: sequential media types (3.2)
            if isinstance(media, dict) and key in media:
                media = {**media, key: _schema(media[key], root)}
        result[media_type] = media
    return result


def _with_content(node: Any, root: Any) -> Any:
    node = resolve(node, root)
    if isinstance(node, dict) and "content" in node:
        return {**node, "content": _media(node["content"], root)}
    return node


def _spend(budget: list[int], units: int) -> None:
    budget[0] -= units
    if budget[0] < 0:
        raise ValueError(
            f"the document expands to more than {MAX_UNITS} operations, responses and media "
            "types through its references"
        )


def _operation(
    operation: dict[str, Any], shared: list[Any], root: Any, budget: list[int]
) -> dict[str, Any]:
    result = dict(operation)
    own = _parameters(operation.get("parameters"), root)
    if shared or "parameters" in operation:
        result["parameters"] = _merge_parameters(shared, own)
    if "requestBody" in operation:
        result["requestBody"] = _with_content(operation["requestBody"], root)
    responses = resolve(operation.get("responses"), root)
    body = result.get("requestBody")
    content = body.get("content") if isinstance(body, dict) else None
    counted = len(responses) if isinstance(responses, dict) else 0
    counted += len(content) if isinstance(content, dict) else 0
    _spend(budget, 1 + len(result.get("parameters") or []) + counted)
    if isinstance(responses, dict):
        result["responses"] = {
            str(code): _with_content(response, root) for code, response in responses.items()
        }
        bodies = [r.get("content") for r in result["responses"].values() if isinstance(r, dict)]
        _spend(budget, sum(len(c) for c in bodies if isinstance(c, dict)))
    elif "responses" in operation:
        result["responses"] = {}  # malformed responses read as none declared
    return result


def _operations(item: dict[str, Any], root: Any, budget: list[int]) -> dict[str, dict[str, Any]]:
    shared = _parameters(item.get("parameters"), root)
    found: dict[str, Any] = {}
    for name, value in item.items():
        # Field names are case-sensitive; `GET` is read as `get` for tolerance, and the
        # exact lower-case field wins when both are present.
        method = str(name).lower()
        if method in OPERATION_KEYS and (method not in found or name == method):
            found[method] = value
    extra = item.get("additionalOperations")
    if isinstance(extra, dict):
        for name, value in extra.items():
            if str(name).lower() not in found:  # may not repeat a fixed field (`POST`)
                found[str(name)] = value
    result: dict[str, dict[str, Any]] = {}
    for name, value in found.items():
        operation = resolve(value, root)
        if isinstance(operation, dict):
            result[str(name)] = _operation(operation, shared, root, budget)
    return result


def normalize_paths(document: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """Return ``{path: {method: operation}}`` for every path of an OpenAPI document."""
    paths = document.get("paths") if isinstance(document, dict) else None
    if not isinstance(paths, dict):
        return {}
    result: dict[str, dict[str, dict[str, Any]]] = {}
    budget = [MAX_UNITS]
    for path, item in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            continue  # `x-` extensions are not paths
        item = resolve(item, document)
        result[path] = _operations(item, document, budget) if isinstance(item, dict) else {}
    return result
