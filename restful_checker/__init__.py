"""Check RESTful API compliance from OpenAPI definitions and generate HTML reports.

``analyze_api`` is imported on first use, so ``import restful_checker`` stays light.

>>> import restful_checker
>>> restful_checker.__all__
['analyze_api']
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "3.2.0"
__all__ = ["analyze_api"]

if TYPE_CHECKING:
    from restful_checker.engine.analyzer import analyze_api


def __getattr__(name: str) -> Any:
    if name == "analyze_api":
        from restful_checker.engine.analyzer import analyze_api

        return analyze_api
    raise AttributeError(f"module 'restful_checker' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), "analyze_api"])
