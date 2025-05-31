from restful_checker.report.rest_docs import linkify

class CheckResult:
    def __init__(self, category: str):
        self.messages = []
        self.category = category
        self.score = 1.0

    def error(self, msg: str):
        self.messages.append(linkify(f"❌ {msg}", self.category))
        self.score -= 0.4

    def warning(self, msg: str):
        self.messages.append(linkify(f"⚠️ {msg}", self.category))
        self.score -= 0.2

    def success(self, msg: str):
        self.messages.append(linkify(f"✅ {msg}", self.category))

    def finalize_score(self) -> float:
        return max(0.0, round(self.score, 2))