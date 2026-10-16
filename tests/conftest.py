"""Shared helpers: small OpenAPI documents, report readers and the pinned sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

UPSTREAM = Path(__file__).parent / "upstream"


def upstream(name: str) -> str:
    """Return a pinned source fetched by scripts/fetch_upstream.py, or skip the test."""
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run python scripts/fetch_upstream.py")
    return path.read_text(encoding="utf-8")


def ok_operation(*codes: str, example: bool = True) -> dict[str, Any]:
    """An operation whose responses carry JSON content with an example."""
    media: dict[str, Any] = {"schema": {"type": "object"}}
    if example:
        media["example"] = {}
    return {
        "responses": {
            code: {"description": code, "content": {"application/json": media}} for code in codes
        }
    }


def document(paths: dict[str, Any], **extra: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": paths,
    }
    doc.update(extra)
    return doc


def write_json(folder: Path, doc: Any, name: str = "openapi.json") -> Path:
    path = folder / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def all_messages(report: dict[str, Any], category: str | None = None) -> list[dict[str, Any]]:
    """Every message of a JSON report, optionally only from one check category."""
    found = []
    for section in report["sections"]:
        for item in section["items"]:
            if category is None or item["category"] == category:
                found.extend(item["messages"])
    return found


class FakeResponse:
    """What resolve_openapi_path reads from a `requests` response."""

    def __init__(self, body: bytes, content_type: str = "") -> None:
        self.content = body
        self.headers = {"content-type": content_type} if content_type else {}

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int | None = None) -> list[bytes]:
        return [self.content]

    def close(self) -> None:
        pass


def problems(messages: list[str]) -> list[str]:
    """Messages of a checker that are errors or warnings."""
    return [m for m in messages if m.startswith(("❌", "⚠️"))]
