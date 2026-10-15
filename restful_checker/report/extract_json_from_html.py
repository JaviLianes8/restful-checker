from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from bs4 import BeautifulSoup, Tag


def classify_message_level_from_emoji(text: str) -> Literal["error", "warn", "info"]:
    """
    Determine the message level based on its emoji.

    Args:
        text (str): The message text.

    Returns:
        str: "error", "warn", or "info"
    """
    if "❌" in text:
        return "error"
    elif "⚠️" in text:
        return "warn"
    elif "✅" in text:
        return "info"
    return "info"


def _http_methods(section: Tag) -> list[str]:
    # Read the methods from their own list item; a regex over the whole section text ran
    # into the next heading and kept its first capital letter.
    for li in section.find_all("li"):
        text = li.get_text().strip()
        if text.startswith("HTTP methods:"):
            names = text[len("HTTP methods:") :].split(",")
            return [name.strip() for name in names if name.strip() and name.strip() != "none"]
    return []


def _section_title(h2: Tag) -> tuple[str, int]:
    full_title = h2.text.strip()
    span = h2.find("span", class_="score-inline")
    if isinstance(span, Tag):
        score_match = re.search(r"\((\d+)%\)", span.text)
        title = full_title[: len(full_title) - len(span.text.strip())]
        title = re.sub(r"^[🔴🟡🟢]+\s*", "", title).strip()
        return title, int(score_match.group(1)) if score_match else 100
    score_match = re.search(r"\((\d+)%\)", full_title)
    title = re.sub(r"^[🔴🟡🟢]+\s*", "", full_title)
    return re.sub(r"\s*\(.*?\)", "", title).strip(), int(
        score_match.group(1)
    ) if score_match else 100


def extract_json_from_html(html_path: str | Path) -> dict[str, Any]:
    """
    Parse an HTML report and extract structured JSON data.

    Args:
        html_path (str or Path): Path to the HTML report file.

    Returns:
        dict: Structured JSON report including sections, score, and metadata.
    """
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result: dict[str, Any] = {
        "title": "RESTful API JSON Report",
        "score": None,
        "generated": None,
        "sections": [],
    }

    # Extract title
    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.text.strip()

    # Extract generation time
    for p in soup.find_all("p"):
        if "Generated" in p.text:
            result["generated"] = p.text.split("Generated:")[-1].strip()
            break

    # Extract global score
    score_tag = soup.select_one("div.score")
    if score_tag:
        match = re.match(r"(\d+)%", score_tag.text.strip())
        if match:
            result["score"] = int(match.group(1))

    # Extract section blocks
    for section in soup.select("div.section"):
        h2 = section.find("h2")
        if not h2:
            continue

        path_clean, section_score = _section_title(h2)
        methods = _http_methods(section)

        # Parse message items by category
        items: list[dict[str, Any]] = []
        current_section: dict[str, Any] | None = None

        for tag in section.find_all(["h3", "ul"]):
            if tag.name == "h3":
                if current_section:
                    items.append(current_section)
                current_section = {"category": tag.text.strip(), "messages": []}
            elif tag.name == "ul" and current_section:
                for li in tag.find_all("li"):
                    raw_msg = li.text.strip()
                    clean_msg = (
                        raw_msg.replace("✅", "")
                        .replace("❌", "")
                        .replace("⚠️", "")
                        .replace("More info", "")
                        .strip()
                    )
                    current_section["messages"].append(
                        {"message": clean_msg, "level": classify_message_level_from_emoji(raw_msg)}
                    )

        if current_section:
            items.append(current_section)

        # Section JSON block
        section_obj: dict[str, Any] = {"score": section_score, "items": items}

        if path_clean in ["SSL", "Global Parameter Consistency"]:
            section_obj["section"] = path_clean
        else:
            section_obj["path"] = path_clean

        if methods:
            section_obj["httpMethods"] = methods

        result["sections"].append(section_obj)

    return result
