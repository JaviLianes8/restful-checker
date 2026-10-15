"""Tell a verb used as a word apart from a noun that merely starts with the same letters."""

from __future__ import annotations

import re

# A verb followed only by one of these is a noun or an adjective made from it: `posts`,
# `updates`, `makers`, `deleted`, `postings`.
NOUN_SUFFIXES = ("s", "es", "r", "rs", "er", "ers", "d", "ed", "ing", "ings")

# Short verbs that start too many ordinary nouns (`documents`, `domains`, `addresses`,
# `additions`): they count only as a word of their own (`do`, `doIt`, `add_item`).
SHORT_VERBS = frozenset({"do", "add"})


def words(path: str) -> list[str]:
    """Lower-case words of a route: `/users/deleteUser` gives users, delete, user."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", path)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)  # `HTTPReset`
    return [word.lower() for word in re.split(r"[^A-Za-z0-9]+", spaced) if word]


def starts_with_verb(segment: str, verb: str) -> bool:
    """`getUsers`, `get_users`, `get`, `getusers`, `createorder`; not `posts` or `documents`."""
    if not re.fullmatch(rf"{verb}[A-Za-z0-9_]*", segment, re.IGNORECASE):
        return False
    rest = segment[len(verb) :]
    if not rest or rest[0].isupper() or rest[0].isdigit() or rest[0] == "_":
        return True
    return verb not in SHORT_VERBS and rest.lower() not in NOUN_SUFFIXES


def contains_verb(word: str, verb: str) -> bool:
    """A route word holding a verb at its start (`deleteuser`) or end (`userdelete`)."""
    word = word.lower()
    return starts_with_verb(word, verb) or (word.endswith(verb) and len(word) > len(verb))
