"""Tell a verb used as a word apart from a noun that merely starts with the same letters."""

from __future__ import annotations

import re

# A verb followed only by one of these is a noun or an adjective made from it: `posts`,
# `updates`, `makers`, `deleted`, `postings`.
NOUN_SUFFIXES = ("s", "es", "r", "rs", "er", "ers", "d", "ed", "ing", "ings")

# Short verbs that start many ordinary nouns. A lower-case compound of them (`addtocart`,
# `dologin`) counts as a verb unless the segment starts with one of the noun stems below
# (`documents`, `domains`, `downloads`, `addresses`, `additions`, `addons`).
SHORT_VERBS = frozenset({"do", "add"})
SHORT_VERB_NOUNS = (
    "doc", "dog", "doll", "dolphin", "dom", "donat", "donor", "door", "dorm", "dose",
    "dosage", "dossier", "dot", "doub", "dough", "dove", "down", "doz", "dojo",
    "address", "addition", "additive", "addon", "addend", "addict", "adder",
)  # fmt: skip

# Kebab-case compounds that are nouns: `add-ons`, and `post-` meaning "after"
# (`post-processing`, `post-mortems`).
KEBAB_NOUNS = ("add-on", "add-ons")
KEBAB_NOUN_PREFIXES = ("post-",)


def words(path: str) -> list[str]:
    """Lower-case words of a route: `/users/deleteUser` gives users, delete, user."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", path)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)  # `HTTPReset`
    return [word.lower() for word in re.split(r"[^A-Za-z0-9]+", spaced) if word]


def starts_with_verb(segment: str, verb: str) -> bool:
    """`getUsers`, `get_users`, `get-users`, `get`, `getusers`, `addtocart`; not `posts`,
    `documents` or `add-ons`.

    >>> [starts_with_verb(s, "get") for s in ("getUsers", "get-users", "getusers")]
    [True, True, True]
    >>> [starts_with_verb(s, "add") for s in ("addtocart", "addresses", "add-ons")]
    [True, False, False]
    """
    if not re.fullmatch(rf"{verb}[A-Za-z0-9_-]*", segment, re.IGNORECASE):
        return False
    rest = segment[len(verb) :]
    lowered = segment.lower()
    if rest[:1] == "-":
        return lowered not in KEBAB_NOUNS and not lowered.startswith(KEBAB_NOUN_PREFIXES)
    if not rest or rest[0].isupper() or rest[0].isdigit() or rest[0] == "_":
        return True
    if rest.lower() in NOUN_SUFFIXES:
        return False
    return verb not in SHORT_VERBS or not lowered.startswith(SHORT_VERB_NOUNS)


def contains_verb(word: str, verb: str) -> bool:
    """A route word holding a verb at its start (`deleteuser`) or end (`userdelete`)."""
    word = word.lower()
    return starts_with_verb(word, verb) or (word.endswith(verb) and len(word) > len(verb))
