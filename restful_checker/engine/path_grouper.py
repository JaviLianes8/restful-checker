import re
from collections import defaultdict

def group_paths(paths):
    """
    Group OpenAPI paths by base resource, distinguishing collection vs item endpoints.

    Example:
        /users           → collection
        /users/{userId}  → item

    Args:
        paths (dict): The OpenAPI "paths" dictionary.

    Returns:
        dict: A dictionary grouped by base path, with:
            - 'collection': set of HTTP methods for collection endpoints
            - 'item': set of HTTP methods for item endpoints
            - 'raw': original raw paths
    """
    resources = defaultdict(lambda: {
        "collection": set(),
        "item": set(),
        "raw": set()
    })

    for path, methods in paths.items():
        raw = path
        # Normalize path by replacing all {param} with {id}
        base = re.sub(r"\{[^}]+}", "{id}", path).rstrip("/")
        is_item = "{" in path

        for method in methods:
            method_upper = method.upper()
            resources[base]["raw"].add(raw)
            if is_item:
                resources[base]["item"].add(method_upper)
            else:
                resources[base]["collection"].add(method_upper)

    return resources