import re
from bs4 import BeautifulSoup

def extract_json_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result = {
        "title": "RESTful API JSON Report",
        "score": None,
        "generated": None,
        "sections": []
    }

    score_tag = soup.select_one("div.score")
    if score_tag:
        score_text = score_tag.text.strip()
        match = re.match(r"(\d+)%", score_text)
        if match:
            result["score"] = int(match.group(1))

    p_tags = soup.find_all("p")
    for p in p_tags:
        if "Generated:" in p.text:
            result["generated"] = p.text.replace("Generated:", "").strip()
            break

    for section in soup.select("div.section"):
        h2 = section.find("h2")
        if not h2:
            continue

        full_title = h2.text.strip()
        title_clean = re.sub(r"^[🔴🟡🟢]+\s*", "", full_title)
        score_match = re.search(r"\((\d+)%\)", full_title)
        section_score = float(score_match.group(1)) / 100 if score_match else 1.0
        title_clean = re.sub(r"\s*\(.*?\)", "", title_clean).strip()

        items = []
        current_section = None

        for tag in section.find_all(["h3", "ul"]):
            if tag.name == "h3":
                if current_section:
                    items.append(current_section)
                current_section = {
                    "type": "section",
                    "title": tag.text.strip(),
                    "messages": []
                }
            elif tag.name == "ul":
                if current_section:
                    for li in tag.find_all("li"):
                        msg = li.text.strip().replace("✅", "").replace("❌", "").replace("⚠️", "")
                        current_section["messages"].append(msg)

        if current_section:
            items.append(current_section)

        result["sections"].append({
            "title": title_clean,
            "score": round(section_score, 2),
            "items": items
        })

    return result