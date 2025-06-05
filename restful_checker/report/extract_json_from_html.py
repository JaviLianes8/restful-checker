import re
from bs4 import BeautifulSoup

def classify_message_level_from_emoji(text):
    if "❌" in text:
        return "error"
    elif "⚠️" in text:
        return "warn"
    elif "✅" in text:
        return "info"
    return "info"

def extract_json_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result = {
        "title": "RESTful API JSON Report",
        "score": None,
        "generated": None,
        "sections": []
    }

    try:
        result["title"] = soup.find("h1").text.strip()
    except Exception:
        result["title"] = "RESTful API JSON Report"

    for p in soup.find_all("p"):
        if "Generated" in p.text:
            try:
                result["generated"] = p.text.split("Generated:")[-1].strip()
                break
            except Exception:
                continue

    score_tag = soup.select_one("div.score")
    if score_tag:
        match = re.match(r"(\d+)%", score_tag.text.strip())
        if match:
            result["score"] = int(match.group(1))

    for section in soup.select("div.section"):
        h2 = section.find("h2")
        if not h2:
            continue

        full_title = h2.text.strip()
        path_clean = re.sub(r"^[🔴🟡🟢]+\s*", "", full_title)
        score_match = re.search(r"\((\d+)%\)", full_title)
        section_score = int(score_match.group(1)) if score_match else 100
        path_clean = re.sub(r"\s*\(.*?\)", "", path_clean).strip()

        raw_text = section.get_text()
        methods = []
        http_match = re.search(r"HTTP methods:\s*([A-Z,\s]+)", raw_text)
        if http_match:
            methods = [re.sub(r"V$", "", m.strip()) for m in http_match.group(1).split(",")]

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
                    msg_clean = (
                        raw_msg.replace("✅", "")
                        .replace("❌", "")
                        .replace("⚠️", "")
                        .replace("More info", "")
                        .strip()
                    )
                    current_section["messages"].append({
                        "message": msg_clean,
                        "level": classify_message_level_from_emoji(raw_msg)
                    })

        if current_section:
            items.append(current_section)

        if path_clean in ["SSL", "Global Parameter Consistency"]:
            section_obj = {
                "section": path_clean,
                "score": section_score
            }
        else:
            section_obj = {
                "path": path_clean,
                "score": section_score
            }

        if methods:
            section_obj["httpMethods"] = methods
        section_obj["items"] = items

        result["sections"].append(section_obj)

    return result