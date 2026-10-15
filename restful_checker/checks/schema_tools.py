"""Read what a schema promises, including what its ``allOf`` members add."""

from __future__ import annotations

from typing import Any

# A schema with more members than this, counted through nested `allOf`, is read only this
# far: real documents stay far below it and a hostile one cannot make the walk explode.
MAX_SCHEMAS = 256


def _schemas(schema: Any) -> list[dict[str, Any]]:
    # The schema and every schema its `allOf` members hold, each object read once.
    found: list[dict[str, Any]] = []
    seen: set[int] = set()
    pending = [schema]
    while pending and len(found) < MAX_SCHEMAS:
        node = pending.pop()
        if not isinstance(node, dict) or id(node) in seen:
            continue
        seen.add(id(node))
        found.append(node)
        members = node.get("allOf")
        if isinstance(members, list):
            pending.extend(reversed(members))
    return found


def merged_properties(schema: Any) -> dict[str, Any] | None:
    """Return the properties a schema declares itself or through ``allOf``.

    ``None`` means no ``properties`` object anywhere: the schema is not structured.

    >>> base = {"properties": {"code": {}}}
    >>> sorted(merged_properties({"allOf": [base, {"properties": {"message": {}}}]}))
    ['code', 'message']
    >>> merged_properties({"type": "string"}) is None
    True
    """
    merged: dict[str, Any] = {}
    structured = False
    for node in _schemas(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            structured = True
            for name, value in properties.items():
                merged.setdefault(name, value)
    return merged if structured else None


def has_example(schema: Any) -> bool:
    """Tell whether a schema, or one of its ``allOf`` members, gives an example.

    >>> has_example({"type": "object", "example": {"id": 1}})
    True
    >>> has_example({"allOf": [{"examples": [{"id": 1}]}]})
    True
    """
    return any("example" in node or "examples" in node for node in _schemas(schema))
