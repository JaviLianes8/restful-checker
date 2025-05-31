from restful_checker.checks.check_result import CheckResult
import re

class ResourceNestingChecker:
    """Validates the nesting structure of RESTful API routes."""

    def __init__(self, path: str, methods: dict):
        self.path = path
        self.methods = methods
        self.result = CheckResult("resource_nesting")

    def validate(self) -> tuple[list[str], float]:
        segments = self.path.strip("/").split("/")

        # Early return if path is too shallow for nesting checks
        if len(segments) < 2:
            self.result.success("Path too shallow to check nesting.")
            return self.result.messages, self.result.finalize_score()

        for i in range(len(segments) - 1):
            current = segments[i]
            next_segment = segments[i + 1]

            is_current_id = re.fullmatch(r"\{[^{}]+}", current)
            is_next_id = re.fullmatch(r"\{[^{}]+}", next_segment)

            # Check for missing ID between plural resources
            if not is_current_id and not next_segment.startswith("{"):
                if next_segment.endswith("s") and current.endswith("s"):
                    self.result.error(
                        f"Route '{self.path}' may be missing parent ID in nesting (e.g., /{current}/{{id}}/{next_segment})"
                    )

            # Check for consecutive IDs (potentially problematic)
            if is_current_id and is_next_id:
                self.result.warning(
                    f"Route '{self.path}' contains multiple consecutive IDs — ensure nesting is intentional"
                )

        if not self.result.messages:
            self.result.success("Route nesting appears valid")

        return self.result.messages, self.result.finalize_score()


def check_resource_nesting(path: str, methods: dict) -> tuple[list[str], float]:
    """Convenience function to use the ResourceNestingChecker class directly."""
    checker = ResourceNestingChecker(path, methods)
    return checker.validate()