"""Check RESTful API compliance from OpenAPI definitions and generate HTML reports."""

from __future__ import annotations

__version__ = "3.1.1"

from restful_checker.engine.analyzer import analyze_api  # noqa: E402  (needs __version__ first)

__all__ = ["analyze_api"]
