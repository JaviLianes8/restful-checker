from restful_checker.report.rest_docs import linkify

class CheckResult:
    """
    Collects and formats result messages for a single check category,
    and computes a final score based on errors and warnings.
    """

    def __init__(self, category: str):
        """
        Initialize the result object for a given check category.

        Args:
            category (str): Identifier used to link messages to documentation.
        """
        self.messages: list[str] = []
        self.category: str = category
        self.score: float = 1.0
        self.has_error: bool = False

    def error(self, msg: str):
        """
        Register an error message and force score to zero.

        Args:
            msg (str): Description of the error.
        """
        self.messages.append(linkify(f"❌ {msg}", self.category))
        self.has_error = True

    def warning(self, msg: str):
        """
        Register a warning message and reduce score slightly (unless already errored).

        Args:
            msg (str): Description of the warning.
        """
        self.messages.append(linkify(f"⚠️ {msg}", self.category))
        if not self.has_error:
            self.score -= 0.2

    def success(self, msg: str):
        """
        Register a success message without modifying the score.

        Args:
            msg (str): Description of the success.
        """
        self.messages.append(f"✅ {msg}")

    def finalize_score(self) -> float:
        """
        Finalize and return the computed score.

        Returns:
            float: Final score between 0.0 and 1.0.
        """
        if self.has_error:
            return 0.0
        return max(0.0, round(self.score, 2))