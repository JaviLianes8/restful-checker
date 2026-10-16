"""The command names itself and its help lists every option."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from restful_checker import main as cli


def test_the_module_names_the_command() -> None:
    import subprocess
    import sys

    done = subprocess.run([sys.executable, "-m", "restful_checker", "--version"],
                          capture_output=True, text=True, check=True)  # fmt: skip
    assert done.stdout.strip() == f"restful-checker {cli.__version__}"


def test_help_lists_every_option(capsys: pytest.CaptureFixture[str]) -> None:
    from restful_checker.tools.help_restful_checker import show_help

    show_help()
    out = capsys.readouterr().out
    for option in ("--output-format", "--output-folder", "--open", "--quiet", "--version"):
        assert option in out


def test_the_json_report_of_the_command_is_written_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path
    spec = folder / "openapi.json"
    spec.write_text(json.dumps({"openapi": "3.1.0", "paths": {}}), encoding="utf-8")
    calls: list[str] = []

    def refuse(source: object, target: object) -> None:
        calls.append(str(target))
        if str(target).endswith(".json") and len(calls) > 2:
            raise OSError("disk full")
        shutil.move(str(source), str(target))

    monkeypatch.setattr("os.replace", refuse)
    args = argparse.Namespace(path=str(spec), output_folder=str(folder / "o"),
                              output_format="json", open=False, quiet=True)  # fmt: skip
    assert cli.run_checker(args) == 1
    assert not list((folder / "o").glob("*.tmp"))
    assert json.loads((folder / "o" / "rest_report.json").read_text(encoding="utf-8"))["sections"]
