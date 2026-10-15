"""Every public name documents a runnable example, and every example in the package passes."""

from __future__ import annotations

import doctest
import importlib
import pkgutil
from types import ModuleType
from typing import Any

import pytest

import restful_checker
from restful_checker.checks.check_error_format import check_error_format
from restful_checker.checks.content_type_checker import check_content_type
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.https_checker import check_https_usage
from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.query_filter_checker import check_query_filters
from restful_checker.checks.resource_nesting_checker import check_resource_nesting
from restful_checker.checks.response_example_checker import check_response_examples
from restful_checker.checks.status_code_checker import check_status_codes
from restful_checker.checks.version_checker import check_versioning

# The documented public API: the package names and the twelve checks, each returning
# (messages, score).
PUBLIC: list[Any] = [
    restful_checker,
    restful_checker.analyze_api,
    check_error_format,
    check_content_type,
    check_http_methods,
    check_https_usage,
    check_naming,
    check_pagination,
    check_param_consistency,
    check_query_filters,
    check_resource_nesting,
    check_response_examples,
    check_status_codes,
    check_versioning,
]


def modules() -> list[ModuleType]:
    names = [restful_checker.__name__]
    prefix = restful_checker.__name__ + "."
    names += [info.name for info in pkgutil.walk_packages(restful_checker.__path__, prefix)]
    return [importlib.import_module(name) for name in sorted(names)]


@pytest.mark.parametrize("item", PUBLIC, ids=lambda item: item.__name__)
def test_public_names_have_runnable_examples(item: Any) -> None:
    assert ">>> " in (item.__doc__ or "")


@pytest.mark.parametrize("module", modules(), ids=lambda module: module.__name__)
def test_module_examples_pass(module: ModuleType) -> None:
    failed, _ = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
    assert failed == 0
