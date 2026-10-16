"""Contracts found missing by a blind mutation round: command line, downloads, engine."""

from __future__ import annotations

import json
import sys
import types
from argparse import Namespace
from pathlib import Path
from typing import Any, cast

import pytest
import requests
from conftest import document, write_json

from restful_checker import cli_remote
from restful_checker import main as cli
from restful_checker.cli_io import is_valid_file, print_error
from restful_checker.engine.analyzer import analyze_api
from restful_checker.engine.normalizer import normalize_paths
from restful_checker.engine.path_grouper import group_paths


def _args(path: str, folder: Path, **extra: Any) -> Namespace:
    values = {"output_format": "html", "open": False, "quiet": True, **extra}
    return Namespace(path=path, output_folder=str(folder), **values)


# --- command line -------------------------------------------------------------------------


def test_a_yml_file_is_a_valid_local_spec(tmp_path: Path) -> None:
    spec = tmp_path / "openapi.yml"
    spec.write_text(json.dumps(document({})), encoding="utf-8")
    assert is_valid_file(str(spec))
    assert cli.run_checker(_args(str(spec), tmp_path / "out")) == 0


def test_a_swagger_2_document_is_accepted_by_the_command(tmp_path: Path) -> None:
    doc = {"swagger": "2.0", "info": {"title": "t", "version": "1"}, "paths": {}}
    spec = write_json(tmp_path, doc)
    assert cli.run_checker(_args(str(spec), tmp_path / "out")) == 0


def test_the_json_file_of_the_command_keeps_non_ascii_text(tmp_path: Path) -> None:
    spec = write_json(tmp_path, document({"/v1/cafés": {"get": {"responses": {}}}}))
    folder = tmp_path / "out"
    assert cli.run_checker(_args(str(spec), folder, output_format="json")) == 0
    text = (folder / "rest_report.json").read_text(encoding="utf-8")
    assert "/v1/cafés" in text and "\\u00e9" not in text


def test_printing_without_a_usable_stdout_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", object())  # no write(): AttributeError inside print
    print_error("nothing to tell")


# --- remote documents ---------------------------------------------------------------------


class _Streamed:
    def __init__(self, chunks: list[bytes], status: int = 200, reason: str = "OK") -> None:
        self.chunks = chunks
        self.status_code = status
        self.reason = reason
        self.headers: dict[str, str] = {}
        self.closed = False

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} for url", response=cast(Any, self))

    def iter_content(self, chunk_size: int | None = None) -> Any:
        return iter(self.chunks)

    def close(self) -> None:
        self.closed = True


def _serve(monkeypatch: pytest.MonkeyPatch, response: _Streamed) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **k: response)


def test_the_size_limit_is_exactly_50_mb(monkeypatch: pytest.MonkeyPatch) -> None:
    block = b"x" * 2**20
    _serve(monkeypatch, _Streamed([block] * 50))
    assert len(cli_remote.fetch("https://h.example/spec")) == 50 * 2**20
    _serve(monkeypatch, _Streamed([block] * 50 + [b"x"]))
    with pytest.raises(cli_remote.FetchError, match=r"larger than 50 MB"):
        cli_remote.fetch("https://h.example/spec")


def test_the_deadline_is_60_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    waited: list[float] = []

    class Stuck:
        def __init__(self, **_: Any) -> None:
            pass

        def start(self) -> None:
            pass

        def join(self, timeout: float) -> None:
            waited.append(timeout)

        def is_alive(self) -> bool:
            return True

    monkeypatch.setattr(cli_remote, "threading", types.SimpleNamespace(Thread=Stuck))
    with pytest.raises(cli_remote.FetchError) as error:
        cli_remote.fetch("https://h.example/spec")
    assert waited == [60.0]
    assert str(error.value) == "the download took longer than 60 s"


def test_an_http_error_status_is_a_failed_download(monkeypatch: pytest.MonkeyPatch) -> None:
    _serve(monkeypatch, _Streamed([b"<html>not here</html>"], 404, "Not Found"))
    with pytest.raises(requests.HTTPError) as error:
        cli_remote.fetch("https://h.example/spec")
    assert cli_remote.describe(error.value) == "HTTP 404 Not Found"


def test_describe_names_status_and_reason() -> None:
    response = _Streamed([], 503, "Service Unavailable")
    error = requests.HTTPError("x", response=cast(Any, response))
    assert cli_remote.describe(error) == "HTTP 503 Service Unavailable"


def test_the_response_is_closed_after_the_download(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _Streamed([b"{}"])
    _serve(monkeypatch, response)
    assert cli_remote.fetch("https://h.example/spec") == b"{}"
    assert response.closed


def test_a_malformed_url_is_never_echoed() -> None:
    shown = cli_remote.safe_url("https://alice:secret@api.example.com:99999/spec")
    assert shown == "<the given URL>"


def test_the_suffix_from_the_url_ignores_case() -> None:
    assert cli_remote.remote_suffix("/SPEC.YAML", b'{"openapi": "3.0.3"}') == ".yaml"
    assert cli_remote.remote_suffix("/spec.YML", b'{"openapi": "3.0.3"}') == ".yaml"


def test_a_json_body_with_a_byte_order_mark_is_json() -> None:
    assert cli_remote.remote_suffix("/openapi", b'\xef\xbb\xbf{"openapi": "3.0.3"}') == ".json"


# --- engine -------------------------------------------------------------------------------


def test_scores_are_rounded_not_truncated(tmp_path: Path) -> None:
    media: dict[str, Any] = {"application/json": {"example": {}}}
    problem: dict[str, Any] = {"application/problem+json": {"example": {}}}
    get = {"responses": {"200": {"description": "ok", "content": media},
                         "404": {"description": "no", "content": problem}}}  # fmt: skip
    spec = write_json(tmp_path, document({"/v1/users": {"get": get}}))
    report = analyze_api(spec, output_dir=tmp_path / "out")["json_report"]
    assert report["sections"][0]["score"] == 96  # block mean 0.9583 kept to two decimals
    assert report["score"] == 99  # (0.96 + 1 + 1) / 3 = 98.67 rounds up


def test_the_reference_budget_allows_exactly_50000_units() -> None:
    def doc(responses: int) -> dict[str, Any]:
        codes = {str(i): {"description": "d"} for i in range(responses)}
        return {"openapi": "3.0.3", "paths": {"/a": {"get": {"responses": codes}}}}

    assert len(normalize_paths(doc(49_999))["/a"]["get"]["responses"]) == 49_999  # 50,000 units
    with pytest.raises(ValueError, match="more than 50000"):
        normalize_paths(doc(50_000))


def test_a_schema_built_from_itself_keeps_its_reference() -> None:
    ref = {"$ref": "#/components/schemas/Node"}
    node = {"type": "object", "allOf": [ref, {"properties": {"name": {}}}]}
    media = {"application/json": {"schema": ref}}
    doc = {"openapi": "3.0.3", "components": {"schemas": {"Node": node}},
           "paths": {"/a": {"get": {"responses": {"200": {"content": media}}}}}}  # fmt: skip
    schema = normalize_paths(doc)["/a"]["get"]["responses"]["200"]["content"]["application/json"]
    assert schema["schema"]["allOf"][0] == ref


def test_any_route_with_a_parameter_is_an_item() -> None:
    groups = group_paths({"/v1/users/{id}/orders": {"get": {}}})
    assert groups["/v1/users/{id}/orders"]["item"] == {"GET"}
    assert groups["/v1/users/{id}/orders"]["collection"] == set()
