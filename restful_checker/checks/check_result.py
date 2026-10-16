"""Messages and score of one check category."""

from __future__ import annotations

from restful_checker.report.rest_docs import linkify as linkify  # importable here in 3.1


class CheckResult:
    """
    Collects the messages of a single check category and computes its score.

    Messages are plain text with a leading status symbol; the HTML report escapes them
    and adds the "More info" link of the category.

    >>> result = CheckResult("naming")
    >>> result.warning("Segment `<x>` is too generic")
    >>> result.messages
    ['⚠️ Segment `<x>` is too generic']
    >>> result.finalize_score()
    0.8
    """

    def __init__(self, category: str) -> None:
        """
        Initialize the result object for a given check category.

        Args:
            category (str): Identifier used to link messages to documentation.
        """
        self.messages: list[str] = []
        self.category: str = category
        self.score: float = 1.0
        self.has_error: bool = False

    def error(self, msg: str) -> None:
        """
        Register an error message and force score to zero.

        Args:
            msg (str): Description of the error.
        """
        self.messages.append(f"❌ {msg}")
        self.has_error = True

    def warning(self, msg: str) -> None:
        """
        Register a warning message and reduce score slightly (unless already errored).

        Args:
            msg (str): Description of the warning.
        """
        self.messages.append(f"⚠️ {msg}")
        if not self.has_error:
            self.score -= 0.2

    def success(self, msg: str) -> None:
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
