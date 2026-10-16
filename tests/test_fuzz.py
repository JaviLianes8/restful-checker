"""Seeded fuzzing: random and hostile documents never crash and never blow up in time."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml
from conftest import document, write_json

from restful_checker import analyze_api
from restful_checker.report.extract_json_from_html import extract_json_from_html

WORDS = ["users", "{id}", "getUsers", "v1", "v1beta1", "add-ons", "<b>", "&", "(x)", "", "é",
         "page[size]", "2XX", "{", "}", "/", "HTTPReset", "addtocart", "posts"]  # fmt: skip
KEYS = ["get", "post", "put", "delete", "patch", "head", "options", "trace", "query", "GET",
        "parameters", "responses", "requestBody", "content", "schema", "allOf", "$ref",
        "properties", "example", "examples", "servers", "url", "variables", "default", "enum",
        "name", "in", "type", "format", "additionalOperations", "x-a"]  # fmt: skip
REFS = ["#/components/schemas/A", "#/paths", "#", "#/x~1y", "other.yaml#/a", "#/components"]


def value(rng: random.Random, depth: int) -> Any:
    kind = rng.randrange(9 if depth < 5 else 4)
    if kind == 0:
        return rng.choice(WORDS)
    if kind == 1:
        return rng.choice([None, True, 0, 200, -1, 1.5, "200", "https://a", "{s}://a"])
    if kind == 2:
        return {"$ref": rng.choice(REFS)}
    if kind == 3:
        return rng.choice(["application/json", "multipart/form-data", "image/png", "text/csv"])
    if kind < 6:
        return [value(rng, depth + 1) for _ in range(rng.randrange(4))]
    keys = [rng.choice(KEYS + WORDS) for _ in range(rng.randrange(6))]
    return {key: value(rng, depth + 1) for key in keys}


def random_document(rng: random.Random) -> dict[str, Any]:
    paths = {
        "/" + "/".join(rng.choice(WORDS) for _ in range(rng.randrange(4))): value(rng, 1)
        for _ in range(rng.randrange(6))
    }
    doc = document(paths, components={"schemas": {"A": value(rng, 2)}})
    for key in ("servers", "schemes", "swagger"):
        if rng.random() < 0.3:
            doc[key] = value(rng, 3)
    return doc


@pytest.mark.parametrize("seed", range(8))
def test_random_documents_never_crash(tmp_path: Path, seed: int) -> None:
    rng = random.Random(seed)
    for case in range(60):
        doc = random_document(rng)
        name = "spec.yaml" if case % 2 else "spec.json"
        path = tmp_path / name
        if name.endswith(".json"):
            write_json(tmp_path, doc, name)
        else:
            path.write_text(yaml.safe_dump(doc), encoding="utf-8")
        result = analyze_api(path, output_dir=tmp_path / "out")
        assert 0 <= result["json_report"]["score"] <= 100
        assert extract_json_from_html(result["html_path"]) == result["json_report"]
        json.dumps(result["json_report"])


def seconds(action: Callable[[], object]) -> float:
    started = time.perf_counter()
    action()
    return time.perf_counter() - started


def grows_linearly(make: Callable[[int], dict[str, Any]], tmp_path: Path, size: int) -> None:
    small = write_json(tmp_path, make(size), "small.json")
    large = write_json(tmp_path, make(size * 8), "large.json")
    small_time = min(seconds(lambda: analyze_api(small, tmp_path / "o")) for _ in range(2))
    large_time = min(seconds(lambda: analyze_api(large, tmp_path / "o")) for _ in range(2))
    assert large_time < small_time * 24 + 0.5  # linear is 8; quadratic would be 64


@pytest.mark.parametrize(
    "make",
    [
        lambda n: document({f"/v1/r{i}/{{id{i}}}": {"get": {}} for i in range(n // 10)}),
        lambda n: document({"/v1/" + "A" * n + "a": {"get": {}}}),
        lambda n: document({"/" + "{" * n: {"get": {}, "post": {}, "delete": {}}}),
        lambda n: document({"/v1/" + "a" * n: {"get": {}}}),
        lambda n: document({"/v1/a": {}}, servers=[{"url": "{" * n}, {"url": " " * n}]),
    ],
    ids=["many-paths", "capitals", "braces", "letters", "server-url"],
)
def test_time_grows_linearly(tmp_path: Path, make: Callable[[int], dict[str, Any]]) -> None:
    grows_linearly(make, tmp_path, 3000)


@pytest.mark.parametrize(
    "page",
    ["<div>" * 100 + "</div>" * 100, "<div class='section'><h2>" + "(" * 50_000 + "</h2></div>",
     "<div class='section'><h2>" + " " * 50_000 + "(x</h2></div>"],
    ids=["deep", "parentheses", "blanks"],
)  # fmt: skip
def test_hostile_report_pages(tmp_path: Path, page: str) -> None:
    path = tmp_path / "page.html"
    path.write_text(page, encoding="utf-8")
    started = time.perf_counter()
    try:
        extract_json_from_html(path)
    except ValueError as error:
        assert str(error) == "the page is nested too deeply to be a report"
    assert time.perf_counter() - started < 5
