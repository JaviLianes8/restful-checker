import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Literal

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

def extract_json_from_html(html_path: str | Path) -> dict:
    """
    Parse an HTML report and extract structured JSON data.

    Args:
        html_path (str or Path): Path to the HTML report file.

    Returns:
        dict: Structured JSON report including sections, score, and metadata.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result = {
        "title": "RESTful API JSON Report",
        "score": None,
        "generated": None,
        "sections": []
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

        full_title = h2.text.strip()
        path_clean = re.sub(r"^[🔴🟡🟢]+\s*", "", full_title)
        score_match = re.search(r"\((\d+)%\)", full_title)
        section_score = int(score_match.group(1)) if score_match else 100
        path_clean = re.sub(r"\s*\(.*?\)", "", path_clean).strip()

        # Extract HTTP methods
        raw_text = section.get_text()
        http_match = re.search(r"HTTP methods:\s*([A-Z,\s]+)", raw_text)
        methods = [m.strip() for m in http_match.group(1).split(",")] if http_match else []

        # Parse message items by category
        items = []
        current_section = None

        for tag in section.find_all(["h3", "ul"]):
            if tag.name == "h3":
                if current_section:
                    items.append(current_section)
                current_section = {
                    "category": tag.text.strip(),
                    "messages": []
                }
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
                    current_section["messages"].append({
                        "message": clean_msg,
                        "level": classify_message_level_from_emoji(raw_msg)
                    })

        if current_section:
            items.append(current_section)

        # Section JSON block
        section_obj = {
            "score": section_score,
            "items": items
        }

        if path_clean in ["SSL", "Global Parameter Consistency"]:
            section_obj["section"] = path_clean
        else:
            section_obj["path"] = path_clean

        if methods:
            section_obj["httpMethods"] = methods

        result["sections"].append(section_obj)

    return result