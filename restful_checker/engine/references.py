"""Local references of an OpenAPI document: JSON pointers, ``$ref`` chains and schemas."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

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
    siblings = {key: value for key, value in schema.items() if key != "$ref"}
    if not siblings:
        return target
    return {"allOf": [target, siblings]}  # both apply: neither replaces the other


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
