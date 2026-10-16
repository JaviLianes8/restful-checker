"""Naming and versioning checks."""

from __future__ import annotations

import pytest
from conftest import problems

from restful_checker.checks.naming_checker import check_naming
from restful_checker.checks.version_checker import check_versioning


@pytest.mark.parametrize(
    "path", ["/v1/posts", "/v1/documents", "/v1/addresses", "/v1/domains", "/v1/makers"]
)
def test_nouns_starting_like_a_verb_are_not_verbs(path: str) -> None:
    messages, score = check_naming(path)
    assert not any("verb" in m for m in messages)
    assert score == 1.0


@pytest.mark.parametrize(
    "segment", ["getUsers", "get_users", "get", "createOrder", "Delete", "fetch2", "doIt"]
)
def test_verb_words_are_errors(segment: str) -> None:
    messages, score = check_naming(f"/v1/{segment}")
    assert any(f"verb-like segment: `{segment}`" in m for m in messages)
    assert score == 0.0


@pytest.mark.parametrize("segment", ["get-users", "create-order", "delete-user", "add-item"])
def test_kebab_verbs_are_errors(segment: str) -> None:
    messages, score = check_naming(f"/v1/{segment}")
    assert any(f"verb-like segment: `{segment}`" in m for m in messages)
    assert score == 0.0


def test_version_segment_is_not_mixed_alphanumeric() -> None:
    messages, score = check_naming("/v1/users")
    assert messages == ["✅ Resource naming looks RESTful"]
    assert score == 1.0
    assert check_naming("/V2/users")[1] == 1.0


def test_mixed_alphanumeric_segment_still_warns() -> None:
    messages, score = check_naming("/v1/users2")
    assert any("users2" in m and "mixed alphanumeric" in m for m in messages)
    assert score == 0.6  # also "might not be plural"


def test_other_naming_rules() -> None:
    assert any("might not be plural" in m for m in check_naming("/v1/user")[0])
    assert check_naming("/v1/users/{id}")[1] == 1.0
    assert any("PascalCase" in m for m in check_naming("/v1/UserAccounts")[0])
    assert any("camelCase" in m for m in check_naming("/v1/userAccounts")[0])
    assert any("too generic" in m for m in check_naming("/v1/data")[0])
    assert any("preposition" in m for m in check_naming("/v1/by")[0])
    assert check_naming("")[0]


def test_messages_are_plain_text() -> None:
    message = problems(check_naming("/v1/<user>")[0])[0]
    assert message == "⚠️ Last segment `<user>` might not be plural (use plural for collections)"


def test_versioning_rules() -> None:
    assert check_versioning("/v1/users/{id}") == (["✅ Versioning detected"], 1.0)
    assert check_versioning("/users")[1] == 0.0
    assert check_versioning("/v1/v2/users")[1] == 0.0
    assert check_versioning("/a/b/c/v1/users")[1] == 0.0
    assert check_versioning("/a/b/v1/users/{id}")[1] == 0.8
    assert check_versioning("/v1")[1] == 0.0
    assert check_versioning("/v1/{id}")[1] == 0.0
    assert check_versioning("/v1/users") == (["✅ Versioning detected"], 1.0)
    assert check_versioning("/a/v1/users/{id}")[1] == 1.0
