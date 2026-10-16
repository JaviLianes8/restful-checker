"""Read an OpenAPI document from a JSON or YAML file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_openapi(path: str | Path) -> Any:
    """
    Load an OpenAPI specification from a JSON or YAML file.

    Args:
        path (str or Path): Path to the OpenAPI file.

    Returns:
        dict: Parsed OpenAPI content as a Python dictionary.

    Raises:
        ValueError: If the file extension is not supported, the text is not valid JSON
            (``json.JSONDecodeError``, a ``ValueError``) or YAML, or the document is
            nested too deeply for the parser.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    # utf-8-sig: RFC 8259 lets a parser ignore a byte order mark, and editors write one.
    with open(path, encoding="utf-8-sig") as f:
        if suffix not in (".json", ".yaml", ".yml"):
            raise ValueError(f"Unsupported file extension: {suffix}")
        try:
            return json.load(f) if suffix == ".json" else yaml.safe_load(f)
        except yaml.YAMLError as error:
            raise ValueError(f"{path.name} is not valid YAML: {_short(error)}") from error
        except RecursionError:
            # Both parsers recurse once per nesting level; no real OpenAPI document is
            # nested anywhere near the interpreter's limit.
            raise ValueError(f"{path.name} is nested too deeply to read") from None


def _short(error: Exception) -> str:
    # PyYAML messages quote the offending lines; keep the message readable and bounded.
    text = " ".join(str(error).split())
    return text if len(text) <= 300 else text[:297] + "..."
