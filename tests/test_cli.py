"""Command line: options, exit codes, remote specs and console safety."""

from __future__ import annotations

import io
import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest
import requests
from conftest import document, write_json

from restful_checker import main as cli
from restful_checker.tools.help_restful_checker import show_help


def args(path: str | None, folder: Path, **extra: Any) -> Namespace:
    values = {"output_format": "html", "open": False, "quiet": False, **extra}
    return Namespace(path=path, output_folder=str(folder), **values)


def test_no_path_shows_help(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run_checker(args(None, tmp_path)) == 0
    assert "RESTFUL-CHECKER CLI" in capsys.readouterr().out


def test_formats_and_quiet(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    spec = str(write_json(tmp_path, document({})))
    assert cli.run_checker(args(spec, tmp_path / "a", output_format="both")) == 0
    out = capsys.readouterr().out
    assert "HTML report generated" in out and "JSON report generated" in out
    report = json.loads((tmp_path / "a" / "rest_report.json").read_text(encoding="utf-8"))
    assert report["score"] == 100
    assert cli.run_checker(args(spec, tmp_path / "b", output_format="json", quiet=True)) == 0
    assert capsys.readouterr().out == ""


def test_open_launches_the_browser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr("restful_checker.main.webbrowser.open", opened.append)
    spec = str(write_json(tmp_path, document({})))
    assert cli.run_checker(args(spec, tmp_path, open=True, quiet=True)) == 0
    assert opened and opened[0].startswith("file:")


def test_invalid_inputs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.run_checker(args(str(tmp_path / "missing.json"), tmp_path))
    assert exit_info.value.code == 1
    not_openapi = str(write_json(tmp_path, {"hello": 1}))
    assert cli.run_checker(args(not_openapi, tmp_path)) == 1
    assert "not a valid OpenAPI document" in capsys.readouterr().out


@pytest.mark.parametrize("content", ["[1, 2]", "", "openapi", "{bad json"])
def test_is_valid_openapi_rejects_non_documents(tmp_path: Path, content: str) -> None:
    path = tmp_path / "x.json"
    path.write_text(content, encoding="utf-8")
    assert not cli.is_valid_openapi(str(path))
    path = tmp_path / "x.yaml"
    path.write_text(content, encoding="utf-8")
    assert not cli.is_valid_openapi(str(path))


def test_extensions_are_case_insensitive_and_bom_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "API.JSON"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(document({})).encode())
    assert cli.is_valid_file(str(path))
    assert cli.is_valid_openapi(str(path))
    assert cli.run_checker(args(str(path), tmp_path, quiet=True)) == 0
    assert not cli.is_valid_file(str(tmp_path / "x.txt"))


def test_analysis_errors_return_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: Any, **__: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "analyze_api", boom)
    spec = str(write_json(tmp_path, document({})))
    assert cli.run_checker(args(spec, tmp_path)) == 1


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.content = body

    def raise_for_status(self) -> None:
        pass


def serve(monkeypatch: pytest.MonkeyPatch, body: bytes) -> list[str]:
    seen: list[str] = []

    def fake_get(url: str, timeout: float) -> FakeResponse:
        seen.append(url)
        return FakeResponse(body)

    monkeypatch.setattr("restful_checker.main.requests.get", fake_get)
    return seen


YAML_SPEC = "openapi: 3.0.3\ninfo: {title: café, version: '1'}\npaths: {}\n".encode()


@pytest.mark.parametrize(
    ("url", "body", "suffix"),
    [
        ("https://a.example/spec?format=yaml", YAML_SPEC, ".yaml"),
        ("https://a.example/openapi", YAML_SPEC, ".yaml"),
        ("https://a.example/openapi.YML", YAML_SPEC, ".yaml"),
        ("https://a.example/openapi", b'{"openapi": "3.0.3"}', ".json"),
        ("https://a.example/openapi.yaml", b'{"openapi": "3.0.3"}', ".yaml"),
        ("https://a.example/x.json?v=2", b'{"openapi": "3.0.3"}', ".json"),
    ],
)
def test_remote_specs_are_saved_with_the_right_suffix(
    monkeypatch: pytest.MonkeyPatch, url: str, body: bytes, suffix: str
) -> None:
    serve(monkeypatch, body)
    local = cli.resolve_openapi_path(url)
    try:
        assert local.endswith(suffix)
        assert Path(local).read_bytes() == body
        assert cli.is_valid_openapi(local)
    finally:
        os.remove(local)


def test_remote_run_removes_its_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(monkeypatch, YAML_SPEC)
    made: list[str] = []
    original = cli.resolve_openapi_path

    def tracking(path: str) -> str:
        made.append(original(path))
        return made[-1]

    monkeypatch.setattr(cli, "resolve_openapi_path", tracking)
    assert cli.run_checker(args("https://a.example/openapi", tmp_path, quiet=True)) == 0
    assert made and not os.path.exists(made[0])


def test_cleanup_failure_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    serve(monkeypatch, YAML_SPEC)
    removed: list[str] = []

    def refuse(path: str) -> None:
        removed.append(path)
        raise PermissionError(path)

    monkeypatch.setattr("restful_checker.main.os.remove", refuse)
    assert cli.run_checker(args("https://a.example/openapi", tmp_path, quiet=True)) == 0
    assert len(removed) == 1
    Path(removed[0]).unlink()


def test_remote_failure_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(url: str, timeout: float) -> Any:
        raise requests.ConnectionError("down")

    monkeypatch.setattr("restful_checker.main.requests.get", failing)
    with pytest.raises(SystemExit) as exit_info:
        cli.resolve_openapi_path("http://a.example/openapi.json")
    assert exit_info.value.code == 1


def ascii_stdout(monkeypatch: pytest.MonkeyPatch) -> io.BytesIO:
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="ascii"))
    return raw


def test_legacy_console_does_not_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = ascii_stdout(monkeypatch)
    spec = str(write_json(tmp_path, document({})))
    assert cli.run_checker(args(spec, tmp_path)) == 0
    cli.print_error("bad")
    show_help()
    sys.stdout.flush()
    text = raw.getvalue().decode("ascii")
    assert "? HTML report generated" in text and "? bad" in text and "Usage:" in text


def test_main_and_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["restful-checker"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 0
    monkeypatch.setattr(sys, "argv", ["restful-checker", "--version"])
    with pytest.raises(SystemExit):
        cli.main()
    assert capsys.readouterr().out.strip().endswith(cli.__version__)
