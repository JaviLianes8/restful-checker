"""Server lists given below the document: on Path Items and Operations."""

from __future__ import annotations

from typing import Any

from restful_checker.engine.normalizer import OPERATION_KEYS, resolve


def _operations(item: dict[str, Any], root: Any) -> list[Any]:
    # Field names are read ignoring case, as the normalizer reads them (`GET` counts).
    found = [value for key, value in item.items() if str(key).lower() in OPERATION_KEYS]
    extra = item.get("additionalOperations")
    if isinstance(extra, dict):
        found.extend(extra.values())
    return [resolve(operation, root) for operation in found]


def nested_lists(document: Any, field: str) -> list[list[Any]]:
    """Every list held in ``field`` by a Path Item or an Operation of the document.

    OpenAPI 3 Path Items and Operations may override the document's ``servers``, and
    Swagger 2.0 Operations its ``schemes``; each override is a list of its own.

    >>> doc = {"paths": {"/a": {"servers": [{"url": "/x"}],
    ...                         "get": {"servers": [{"url": "http://y"}]}}}}
    >>> nested_lists(doc, "servers")
    [[{'url': '/x'}], [{'url': 'http://y'}]]
    """
    paths = document.get("paths") if isinstance(document, dict) else None
    if not isinstance(paths, dict):
        return []
    lists: list[list[Any]] = []
    for path, item in paths.items():
        item = resolve(item, document)
        if not isinstance(path, str) or not path.startswith("/") or not isinstance(item, dict):
            continue
        for node in [item, *_operations(item, document)]:
            value = node.get(field) if isinstance(node, dict) else None
            if isinstance(value, list) and value:
                lists.append(value)
    return lists
