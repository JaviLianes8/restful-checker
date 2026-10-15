"""Read the JSON report back from an HTML report (kept for reports written by 3.1).

``analyze_api`` builds its JSON report from the data itself; this reader only serves callers
that hold an HTML report and no JSON. It uses the standard library parser.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

from restful_checker.report.json_report import GLOBAL_SECTIONS, METHODS_LABEL

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source"}
_DOTS = r"^[🔴🟡🟢]+\s*"


class _Node:
    def __init__(self, tag: str, classes: list[str]) -> None:
        self.tag = tag
        self.classes = classes
        self.children: list[_Node | str] = []

    def _descendants(self) -> list[_Node | str]:
        # Iterative, in document order: a page nested thousands deep must not recurse.
        found: list[_Node | str] = []
        pending: list[_Node | str] = list(reversed(self.children))
        while pending:
            child = pending.pop()
            found.append(child)
            if isinstance(child, _Node):
                pending.extend(reversed(child.children))
        return found

    def text(self) -> str:
        return "".join(c for c in self._descendants() if isinstance(c, str))

    def walk(self, *tags: str) -> list[_Node]:
        """Descendants with one of the tags, in document order."""
        return [c for c in self._descendants() if isinstance(c, _Node) and c.tag in tags]


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack = [_Node("#root", [])]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = next((value or "" for name, value in attrs if name == "class"), "").split()
        node = _Node(tag, classes)
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                del self.stack[depth:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def classify_message_level_from_emoji(text: str) -> Literal["error", "warn", "info"]:
    """
    Determine the message level based on its emoji.

    >>> classify_message_level_from_emoji("⚠️ Segment `data` is too generic")
    'warn'
    """
    if "❌" in text:
        return "error"
    elif "⚠️" in text:
        return "warn"
    return "info"


def _http_methods(section: _Node) -> list[str]:
    for li in section.walk("li"):
        text = li.text().strip()
        if text.startswith(METHODS_LABEL):
            names = (name.strip() for name in text[len(METHODS_LABEL) :].split(","))
            return [name for name in names if name and name != "none"]
    return []


def _section_title(h2: _Node) -> tuple[str, int]:
    full_title = h2.text().strip()
    span = next((s for s in h2.walk("span") if "score-inline" in s.classes), None)
    if span is not None:
        score_match = re.search(r"\((\d+)%\)", span.text())
        title = full_title[: len(full_title) - len(span.text().strip())]
        return re.sub(_DOTS, "", title).strip(), int(score_match.group(1)) if score_match else 100
    score_match = re.search(r"\((\d+)%\)", full_title)
    title = re.sub(_DOTS, "", full_title)
    return re.sub(r"\s*\(.*?\)", "", title).strip(), int(
        score_match.group(1)
    ) if score_match else 100


def _items(section: _Node) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for tag in section.walk("h3", "ul"):
        if tag.tag == "h3":
            items.append({"category": tag.text().strip(), "messages": []})
        elif items:
            for li in tag.walk("li"):
                raw = li.text().strip()
                clean = raw
                for noise in ("✅", "❌", "⚠️", "More info"):
                    clean = clean.replace(noise, "")
                level = classify_message_level_from_emoji(raw)
                items[-1]["messages"].append({"message": clean.strip(), "level": level})
    return items


def extract_json_from_html(html_path: str | Path) -> dict[str, Any]:
    """
    Parse an HTML report and extract structured JSON data.

    Args:
        html_path (str or Path): Path to the HTML report file.

    Returns:
        dict: Structured JSON report including sections, score, and metadata.
    """
    builder = _TreeBuilder()
    builder.feed(Path(html_path).read_text(encoding="utf-8"))
    builder.close()
    root = builder.stack[0]
    result: dict[str, Any] = {"title": "RESTful API JSON Report", "score": None}
    result.update(generated=None, sections=[])
    h1 = root.walk("h1")
    if h1:
        result["title"] = h1[0].text().strip()
    for p in root.walk("p"):
        if "Generated" in p.text():
            result["generated"] = p.text().split("Generated:")[-1].strip()
            break
    divs = root.walk("div")
    score_tag = next((div for div in divs if "score" in div.classes), None)
    match = re.match(r"(\d+)%", score_tag.text().strip()) if score_tag else None
    if match:
        result["score"] = int(match.group(1))
    for section in (div for div in divs if "section" in div.classes):
        h2 = section.walk("h2")
        if not h2:
            continue
        title, score = _section_title(h2[0])
        section_obj: dict[str, Any] = {"score": score, "items": _items(section)}
        section_obj["section" if title in GLOBAL_SECTIONS else "path"] = title
        methods = _http_methods(section)
        if methods:
            section_obj["httpMethods"] = methods
        result["sections"].append(section_obj)
    return result
