import re
from restful_checker.checks.check_result import CheckResult

class ResourceNestingChecker:
    """
    Validates the nesting structure of RESTful API routes.

    Looks for:
    - Missing parent IDs between plural resource segments
    - Multiple consecutive path parameters (e.g., /{userId}/{postId})
    """

    def __init__(self, path: str, methods: dict):
        self.path = path
        self.methods = methods
        self.result = CheckResult("resource_nesting")

    def validate(self) -> tuple[list[str], float]:
        """
        Perform the nesting analysis and return messages and score.

        Returns:
            tuple[list[str], float]: List of messages and final score.
        """
        segments = self.path.strip("/").split("/")

        # Too shallow to be nested (/users or /status)
        if len(segments) < 2:
            self.result.success("Path too shallow to check nesting.")
            return self.result.messages, self.result.finalize_score()

        for i in range(len(segments) - 1):
            current = segments[i]
            next_segment = segments[i + 1]

            is_current_id = re.fullmatch(r"\{[^{}]+}", current)
            is_next_id = re.fullmatch(r"\{[^{}]+}", next_segment)

            # Case: /users/posts → maybe missing /users/{id}/posts
            if not is_current_id and not next_segment.startswith("{"):
                if current.endswith("s") and next_segment.endswith("s"):
                    self.result.error(
                        f"Route '{self.path}' may be missing parent ID in nesting (e.g., /{current}/{{id}}/{next_segment})"
                    )

            # Case: /{userId}/{postId} — potentially unclear structure
            if is_current_id and is_next_id:
                self.result.warning(
                    f"Route '{self.path}' contains multiple consecutive IDs — ensure nesting is intentional"
                )

        if not self.result.messages:
            self.result.success("Route nesting appears valid")

        return self.result.messages, self.result.finalize_score()


def check_resource_nesting(path: str, methods: dict) -> tuple[list[str], float]:
    """
    Convenience wrapper to call ResourceNestingChecker on a path.

    Args:
        path (str): API path being analyzed.
        methods (dict): OpenAPI method definitions.

    Returns:
        tuple[list[str], float]: List of messages and final score.
    """
    checker = ResourceNestingChecker(path, methods)
    return checker.validate()
