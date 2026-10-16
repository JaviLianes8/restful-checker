"""The public surface of 3.1.1 stays where users find it."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import restful_checker
from restful_checker import main as cli
from restful_checker.checks import (
    check_error_format,
    content_type_checker,
    http_method_checker,
    https_checker,
    naming_checker,
    pagination_checker,
    param_consistency_checker,
    query_filter_checker,
    resource_nesting_checker,
    response_example_checker,
    status_code_checker,
    version_checker,
)
from restful_checker.engine import analyzer

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_package_exports_and_version() -> None:
    assert restful_checker.__all__ == ["analyze_api"]
    assert restful_checker.analyze_api is analyzer.analyze_api
    assert restful_checker.__version__ == "3.2.0"
    assert cli.__version__ == restful_checker.__version__
    assert re.search(rf'^version = "{re.escape(restful_checker.__version__)}"$', PYPROJECT, re.M)
    assert not (ROOT / "setup.py").exists()


def test_typed_marker_ships() -> None:
    assert (Path(restful_checker.__file__).parent / "py.typed").is_file()
    assert 'packages = ["restful_checker"]' in PYPROJECT


def test_metadata() -> None:
    assert 'requires-python = ">=3.8"' in PYPROJECT
    assert '"Development Status :: 5 - Production/Stable"' in PYPROJECT
    assert 'dependencies = ["pyyaml", "requests"]' in PYPROJECT
    minors = set(re.findall(r'"Programming Language :: Python :: 3\.(\d+)"', PYPROJECT))
    assert minors == {str(minor) for minor in range(8, 15)}
    for name in ("Homepage", "Source", "Issues", "Changelog"):
        assert re.search(rf"^{name} = \"https://github.com/JaviLianes8/", PYPROJECT, re.M)
    assert 'license = "MIT"' in PYPROJECT and "keywords = [" in PYPROJECT


def test_analyze_api_signature() -> None:
    params = inspect.signature(analyzer.analyze_api).parameters
    assert list(params) == ["path", "output_dir", "output_format"]
    assert params["output_dir"].default == "html"
    assert params["output_format"].default == "html"


def test_checker_functions_keep_their_signatures() -> None:
    two = {
        check_error_format: "check_error_format",
        content_type_checker: "check_content_type",
        http_method_checker: "check_http_methods",
        pagination_checker: "check_pagination",
        query_filter_checker: "check_query_filters",
        resource_nesting_checker: "check_resource_nesting",
        response_example_checker: "check_response_examples",
        status_code_checker: "check_status_codes",
    }
    for module, name in two.items():
        assert len(inspect.signature(getattr(module, name)).parameters) == 2, name
    one = {
        https_checker: "check_https_usage",
        naming_checker: "check_naming",
        param_consistency_checker: "check_param_consistency",
        version_checker: "check_versioning",
    }
    for module, name in one.items():
        assert len(inspect.signature(getattr(module, name)).parameters) == 1, name


def test_cli_options_are_unchanged() -> None:
    import sys

    argv = sys.argv
    try:
        sys.argv = ["restful-checker", "spec.json"]
        defaults = cli.parse_arguments()
        sys.argv = ["restful-checker", "s.yaml", "--output-format", "both", "--output-folder",
                    "r", "--open", "-q"]  # fmt: skip
        given = cli.parse_arguments()
    finally:
        sys.argv = argv
    assert vars(defaults) == {
        "path": "spec.json",
        "output_format": "html",
        "output_folder": "html",
        "open": False,
        "quiet": False,
    }
    assert (given.output_format, given.output_folder, given.open, given.quiet) == (
        "both",
        "r",
        True,
        True,
    )


def test_console_script_entry_point() -> None:
    assert 'restful-checker = "restful_checker.main:main"' in PYPROJECT


def test_changelog_has_a_dated_section_for_this_version() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{restful_checker.__version__}] - 2026-10-15" in changelog
