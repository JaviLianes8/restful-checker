"""Build the JSON report from the report data, in the layout of the 3.1 JSON report."""

from __future__ import annotations

from typing import Any

# Messages start with one of these; they set the level and are not part of the text.
LEVELS = (("❌", "error"), ("⚠️", "warn"), ("✅", "info"))
GLOBAL_SECTIONS = ("SSL", "Global Parameter Consistency")
METHODS_LABEL = "HTTP methods:"


def message_level(message: str) -> str:
    """Return ``error``, ``warn`` or ``info`` from the symbol a message starts with.

    >>> message_level("⚠️ Segment `data` is too generic")
    'warn'
    """
    for symbol, level in LEVELS:
        if message.startswith(symbol):
            return level
    return "info"


def message_text(message: str) -> str:
    """Return a message without its leading status symbol.

    >>> message_text("❌ No version segment found in route.")
    'No version segment found in route.'
    """
    for symbol, _ in LEVELS:
        if message.startswith(symbol):
            return message[len(symbol) :].strip()
    return message.strip()


def ordered(messages: list[str]) -> list[str]:
    """Errors first, then warnings, then the rest, as the HTML report lists them."""
    errors = [m for m in messages if m.startswith("❌")]
    warnings = [m for m in messages if m.startswith("⚠️")]
    others = [m for m in messages if not m.startswith(("❌", "⚠️"))]
    return errors + warnings + others


def _section(block: dict[str, Any]) -> dict[str, Any]:
    methods: list[str] = []
    items: list[dict[str, Any]] = []
    messages: list[str] = []
    for item in block["items"]:
        if item.startswith("### "):
            messages = []
            items.append({"category": item[4:].strip(), "messages": messages})
        elif items:
            messages.append(item)
        elif item.startswith(METHODS_LABEL):
            names = (name.strip() for name in item[len(METHODS_LABEL) :].split(","))
            methods = [name for name in names if name and name != "none"]
    for entry in items:
        entry["messages"] = [
            {"message": message_text(m), "level": message_level(m)}
            for m in ordered(entry["messages"])
        ]
    section: dict[str, Any] = {"score": round(block.get("score", 1.0) * 100), "items": items}
    title = str(block["title"])
    section["section" if title in GLOBAL_SECTIONS else "path"] = title
    if methods:
        section["httpMethods"] = methods
    return section


def build_json_report(report: list[dict[str, Any]], score: int, generated: str) -> dict[str, Any]:
    """Return the JSON report of the report blocks the analyzer produced.

    >>> block = {"title": "/v1/users", "score": 0.8,
    ...          "items": ["HTTP methods: GET", "### Naming", "⚠️ Segment `x` is too generic"]}
    >>> data = build_json_report([block], 80, "2026-10-15 12:00:00")
    >>> data["sections"][0]["items"][0]["messages"]
    [{'message': 'Segment `x` is too generic', 'level': 'warn'}]
    """
    return {
        "title": "RESTful API Report",
        "score": score,
        "generated": generated,
        "sections": [_section(block) for block in report],
    }
