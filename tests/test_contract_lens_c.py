"""Contracts for the robustness review: amplification, remote limits, secrets, partial output."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest
import requests
from conftest import FakeResponse, document, write_json

from restful_checker import analyze_api, cli_remote
from restful_checker import main as cli
from restful_checker.checks.http_method_checker import check_http_methods
from restful_checker.checks.pagination_checker import check_pagination
from restful_checker.checks.param_consistency_checker import check_param_consistency
from restful_checker.checks.status_code_checker import check_status_codes

ROOT = Path(__file__).resolve().parents[1]


def amplified(k: int) -> dict[str, Any]:
    doc = document({f"/p{i}": {"$ref": "#/x/item"} for i in range(k)})
    doc["x"] = {"item": {"additionalOperations": {f"M{i}": {"$ref": "#/x/op"} for i in range(k)}},
                "op": {"responses": {str(200 + i): {"$ref": "#/x/resp"} for i in range(k)}},
                "resp": {"content": {"application/xml": {}}}}  # fmt: skip
    return doc


def test_references_cannot_amplify_without_bound(tmp_path: Path) -> None:
    assert analyze_api(write_json(tmp_path, amplified(15)), tmp_path / "o")["json_report"]
    started = time.perf_counter()
    with pytest.raises(ValueError, match="expands to more than 50000 operations"):
        analyze_api(write_json(tmp_path, amplified(300)), tmp_path / "o")
    assert time.perf_counter() - started < 10


def test_remote_bodies_that_used_to_crash() -> None:
    assert cli_remote.remote_suffix("/deep", b"[" * 200_000 + b"]" * 200_000) == ".json"
    assert cli_remote.remote_suffix("/spec", b"{a: 1}") == ".yaml"
    idna = {"content-type": "text/plain; charset=idna"}
    body = b"x" * 80 + b".example"
    assert cli_remote.utf8_body(body, idna) == body
    latin = {"content-type": "text/yaml; charset=latin-1"}
    assert cli_remote.utf8_body("é".encode("latin-1"), latin) == "é".encode()


class Chunks(FakeResponse):
    def __init__(self, chunks: list[bytes]) -> None:
        super().__init__(b"")
        self.chunks = chunks

    def iter_content(self, chunk_size: int | None = None) -> list[bytes]:
        return self.chunks


def test_downloads_are_bounded_in_size(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_remote, "MAX_BYTES", 10)
    monkeypatch.setattr(requests, "get", lambda url, **_: Chunks([b"12345", b"678901"]))
    with pytest.raises(cli_remote.FetchError, match="larger than"):
        cli_remote.fetch("http://a.example/spec")
    monkeypatch.setattr(requests, "get", lambda url, **_: Chunks([b"12345", b"67890"]))
    assert cli_remote.fetch("http://a.example/spec") == b"1234567890"


@pytest.fixture
def drip() -> Iterator[str]:
    class Slow(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.end_headers()
            for _ in range(40):
                self.wfile.write(b" ")
                self.wfile.flush()
                time.sleep(0.25)

        def log_message(self, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/spec"
    server.shutdown()
    server.server_close()


def test_a_slow_server_hits_the_deadline(monkeypatch: pytest.MonkeyPatch, drip: str) -> None:
    monkeypatch.setattr(cli_remote, "DEADLINE", 1.0)
    started = time.perf_counter()
    with pytest.raises(cli_remote.FetchError, match="longer than 1 s"):
        cli_remote.fetch(drip)
    assert time.perf_counter() - started < 5


def test_messages_never_show_credentials_or_queries(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    url = "http://alice:SECRET@a.example:8080/spec?api_key=KEY"

    def failing(url: str, **_: object) -> Any:
        raise requests.ConnectionError(f"cannot reach {url}")

    monkeypatch.setattr(requests, "get", failing)
    with pytest.raises(SystemExit):
        cli.resolve_openapi_path(url)
    out = capsys.readouterr().out
    assert "Failed to fetch http://a.example:8080/spec: ConnectionError" in out
    assert "SECRET" not in out and "KEY" not in out
    monkeypatch.setattr(requests, "get", lambda url, **_: FakeResponse(b"[]"))
    assert cli.run_checker(argparse.Namespace(path=url, output_folder="o", quiet=True)) == 1
    out = capsys.readouterr().out
    assert "'http://a.example:8080/spec' is not a valid OpenAPI document" in out
    assert "SECRET" not in out and "KEY" not in out


def test_a_lone_surrogate_never_leaves_a_broken_report(tmp_path: Path) -> None:
    analyze_api(write_json(tmp_path, document({"/v1/users": {"get": {}}})), tmp_path / "o")
    spec = tmp_path / "s.json"
    spec.write_text('{"openapi": "3.1.0", "paths": {"/v1/\\ud800": {"get": {}}}}', "utf-8")
    result = analyze_api(spec, tmp_path / "o")
    page = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "/v1/\\ud800" in page
    assert (
        json.loads(Path(result["json_path"]).read_text(encoding="utf-8")) == result["json_report"]
    )
    assert not list((tmp_path / "o").glob("*.tmp"))


def test_a_closed_stdout_keeps_the_exit_code(tmp_path: Path) -> None:
    spec = write_json(tmp_path, document({"/v1/users": {"get": {}}}))
    code = ("import os, sys; os.close(1); "
            "sys.argv = ['restful-checker', sys.argv[1], '--output-folder', sys.argv[2]]; "
            "from restful_checker.main import main; main()")  # fmt: skip
    done = subprocess.run([sys.executable, "-c", code, str(spec), str(tmp_path / "o")],
                          cwd=ROOT, capture_output=True, text=True, check=False)  # fmt: skip
    assert (done.returncode, done.stderr) == (0, "")
    assert (tmp_path / "o" / "rest_report.html").is_file()


def test_checks_accept_keys_of_any_type() -> None:
    keys: dict[Any, Any] = {None: {}, 3: {}}
    assert check_pagination("/v1/x", keys)[1] == 1.0
    odd: dict[Any, Any] = {None: {"responses": {200: {}}}}
    assert check_status_codes("/v1/x", odd)[1] == 1.0
    paths: dict[Any, Any] = {None: {}, 3: {}, "/v1/{userId}": {}}
    assert check_param_consistency(paths)[1] == 1.0
    assert check_http_methods("/v1/x", {None, 3})[1] == pytest.approx(0.6)  # type: ignore[arg-type]


def test_operation_parameters_and_request_bodies_count_toward_the_limit(tmp_path: Path) -> None:
    doc = document({f"/p{i}": {"$ref": "#/x/item"} for i in range(250)})
    params = [{"name": f"q{i}", "in": "query"} for i in range(250)]
    body: dict[str, Any] = {"content": {f"application/x{i}+json": {} for i in range(250)}}
    doc["x"] = {"item": {"get": {"parameters": params, "requestBody": body}}}
    with pytest.raises(ValueError, match="expands to more than"):
        analyze_api(write_json(tmp_path, doc), tmp_path / "o")


def test_shared_server_lists_are_read_once() -> None:
    from restful_checker.checks.server_levels import nested_lists

    servers = [{"url": "http://a"}]
    doc = {"paths": {f"/p{i}": {"get": {"$ref": "#/x/op"}} for i in range(1000)},
           "x": {"op": {"servers": servers}}}  # fmt: skip
    assert nested_lists(doc, "servers") == [servers]


def test_safe_url_keeps_ipv6_brackets_and_drops_path_parameters() -> None:
    assert cli_remote.safe_url("http://[::1]:8080/x;jsessionid=S") == "http://[::1]:8080/x"


def test_a_failed_write_leaves_no_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from restful_checker.report import html_report

    def broken(source: object, target: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("os.replace", broken)
    with pytest.raises(OSError, match="disk full"):
        html_report.generate_html([], 100, output=tmp_path / "r.html")
    assert list(tmp_path.iterdir()) == []
