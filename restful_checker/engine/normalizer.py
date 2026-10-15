"""Read the Paths Object the way the OpenAPI specification defines it.

The checks receive plain dictionaries: only real operations, every local ``$ref`` they need
followed (parameter and media schemas and their ``allOf``, ``oneOf`` and ``anyOf`` members
included), path-level parameters merged
in and status codes as strings. References to other files or URLs are left as they are. The
document passed in is never modified.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

# Path Item fields holding an Operation Object (OpenAPI 2.0 to 3.2; `query` is new in 3.2).
OPERATION_KEYS = ("get", "put", "post", "delete", "options", "head", "patch", "trace", "query")

_MAX_HOPS = 32
# `allOf` members expanded per schema: enough for real documents, bounded for hostile ones
# (a member list repeating one reference at every level would otherwise grow exponentially).
_MAX_EXPANSIONS = 256
COMPOSITION_KEYS = ("allOf", "oneOf", "anyOf")
_INDEX = re.compile(r"0|[1-9][0-9]*")


def _siblings_apply(root: Any) -> bool:
    # From OpenAPI 3.1 a Schema Object is JSON Schema 2020-12, where keywords next to a
    # `$ref` apply too; 2.0 and 3.0 ignore them.
    version = root.get("openapi") if isinstance(root, dict) else None
    return isinstance(version, str) and version.startswith("3.") and not version.startswith("3.0")


def _target(schema: Any, root: Any) -> Any:
    target = resolve(schema, root)
    if target is schema or not isinstance(target, dict) or not _siblings_apply(root):
        return target
    return {**target, **{key: value for key, value in schema.items() if key != "$ref"}}


def _pointer(root: Any, ref: str) -> Any:
    """Return the node a local reference such as ``#/components/schemas/User`` names."""
    node = root
    # RFC 6901 section 6: the fragment is percent-decoded first, then split and unescaped.
    pointer = unquote(ref[1:])
    for token in pointer[1:].split("/") if pointer else []:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and _INDEX.fullmatch(token) and int(token) < len(node):
            node = node[int(token)]
        else:
            return None
    return node


def resolve(node: Any, root: Any) -> Any:
    """Follow a chain of local ``$ref`` objects; anything else is returned unchanged."""
    seen: set[str] = set()
    while isinstance(node, dict) and isinstance(node.get("$ref"), str):
        ref = node["$ref"]
        if not (ref == "#" or ref.startswith("#/")) or ref in seen or len(seen) >= _MAX_HOPS:
            return node
        seen.add(ref)
        target = _pointer(root, ref)
        if target is None:
            return node
        node = target
    return node


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


def _expand(node: Any, root: Any, budget: list[int], refs: tuple[str, ...]) -> Any:
    if not isinstance(node, dict):
        return node
    result = node
    for key in COMPOSITION_KEYS:
        members = node.get(key)
        if not isinstance(members, list) or budget[0] <= 0:
            continue
        budget[0] -= 1
        expanded = []
        for member in members:
            ref = member.get("$ref") if isinstance(member, dict) else None
            if isinstance(ref, str) and ref in refs:
                expanded.append(member)  # a schema built from itself: leave the cycle closed
                continue
            chain = (*refs, ref) if isinstance(ref, str) else refs
            expanded.append(_expand(_target(member, root), root, budget, chain))
        result = {**result, key: expanded}
    return result


def _schema(schema: Any, root: Any) -> Any:
    """Resolve a schema and the local references of its ``allOf``, ``oneOf`` and ``anyOf``
    members."""
    ref = schema.get("$ref") if isinstance(schema, dict) else None
    refs = (ref,) if isinstance(ref, str) else ()
    return _expand(_target(schema, root), root, [_MAX_EXPANSIONS], refs)


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


def _operation(operation: dict[str, Any], shared: list[Any], root: Any) -> dict[str, Any]:
    result = dict(operation)
    own = _parameters(operation.get("parameters"), root)
    if shared or "parameters" in operation:
        result["parameters"] = _merge_parameters(shared, own)
    if "requestBody" in operation:
        result["requestBody"] = _with_content(operation["requestBody"], root)
    responses = resolve(operation.get("responses"), root)
    if isinstance(responses, dict):
        result["responses"] = {
            str(code): _with_content(response, root) for code, response in responses.items()
        }
    elif "responses" in operation:
        result["responses"] = {}  # malformed responses read as none declared
    return result


def _operations(item: dict[str, Any], root: Any) -> dict[str, dict[str, Any]]:
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
            result[str(name)] = _operation(operation, shared, root)
    return result


def normalize_paths(document: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """Return ``{path: {method: operation}}`` for every path of an OpenAPI document."""
    paths = document.get("paths") if isinstance(document, dict) else None
    if not isinstance(paths, dict):
        return {}
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for path, item in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            continue  # `x-` extensions are not paths
        item = resolve(item, document)
        result[path] = _operations(item, document) if isinstance(item, dict) else {}
    return result
