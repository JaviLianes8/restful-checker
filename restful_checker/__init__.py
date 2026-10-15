"""Check RESTful API compliance from OpenAPI definitions and generate HTML reports.

``analyze_api`` is imported on first use, so ``import restful_checker`` stays light.

>>> import json, pathlib, tempfile
>>> from restful_checker import analyze_api
>>> folder = pathlib.Path(tempfile.mkdtemp())
>>> spec = folder / "openapi.json"
>>> doc = {"openapi": "3.1.0", "info": {"title": "t", "version": "1"},
...        "servers": [{"url": "https://api.example.com"}], "paths": {}}
>>> _ = spec.write_text(json.dumps(doc), encoding="utf-8")
>>> analyze_api(spec, output_dir=folder)["json_report"]["score"]
100
"""

from __future__ import annotations

import typing as _typing

__version__ = "3.2.0"
__all__ = ["analyze_api"]

if _typing.TYPE_CHECKING:
    from restful_checker.engine.analyzer import analyze_api


def __getattr__(name: str) -> _typing.Any:
    if name == "analyze_api":
        from restful_checker.engine.analyzer import analyze_api

        return analyze_api
    raise AttributeError(f"module 'restful_checker' has no attribute {name!r}")


def __dir__() -> list[str]:
    names = [name for name in globals() if name.startswith("__") or name in __all__]
    return sorted({*names, *__all__})
