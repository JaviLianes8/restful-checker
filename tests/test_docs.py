"""The README's examples and option table match the code."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import document, write_json

README = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")


def test_programmatic_example_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    block = re.search(r"```python\n(.*?)```", README, re.S)
    assert block
    write_json(tmp_path, document({}))
    monkeypatch.chdir(tmp_path)
    exec(block.group(1).replace("path/to/openapi.json", "openapi.json"), {})
    out = capsys.readouterr().out
    assert "HTML:" in out and "JSON:" in out and "Score: 100" in out
    assert (tmp_path / "output" / "rest_report.json").is_file()


def test_option_table_lists_every_option() -> None:
    documented = set(re.findall(r"^\| `(-[^`]*)`", README, re.M))
    documented = {name.split(",")[0] for name in documented}
    parser_options = {"--output-format", "--output-folder", "--open", "-q", "--version"}
    assert documented == parser_options
    assert "| `--output-folder` | Destination folder | `./html` |" in README


def test_check_example_prints_what_it_says() -> None:
    blocks = re.findall(r"```python\n(.*?)```", README, re.S)
    code, expected = blocks[1].rsplit("# ", 1)
    namespace: dict[str, object] = {}
    exec(code.replace("print(", "result = ("), namespace)
    assert repr(namespace["result"]) == expected.strip()


def test_links_are_absolute() -> None:
    for target in re.findall(r"\]\(([^)]+)\)", README):
        assert target.startswith(("https://", "#")), target


def test_the_guide_is_linked_and_shipped() -> None:
    root = Path(__file__).resolve().parents[1]
    assert "https://github.com/JaviLianes8/restful-checker/blob/main/GUIDE.md" in README
    assert '"GUIDE.md"' in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "## The checks" in (root / "GUIDE.md").read_text(encoding="utf-8")
