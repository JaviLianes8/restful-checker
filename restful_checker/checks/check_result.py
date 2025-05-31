from restful_checker.report.rest_docs import linkify

class CheckResult:
    def __init__(self, category: str):
        self.messages = []
        self.category = category
        self.score = 1.0
        self.has_error = False

    def error(self, msg: str):
        self.messages.append(linkify(f"❌ {msg}", self.category))
        self.has_error = True

    def warning(self, msg: str):
        self.messages.append(linkify(f"⚠️ {msg}", self.category))
        if not self.has_error:
            self.score -= 0.2

    def success(self, msg: str):
        self.messages.append(f"✅ {msg}")

    def finalize_score(self) -> float:
        if self.has_error:
            return 0.0
        return max(0.0, round(self.score, 2))