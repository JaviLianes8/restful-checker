"""Build the wheel and sdist, install them in fresh venvs, drive them from an empty folder.

Slow and needs the network (dependencies, and PyPI 3.1.1 for the upgrade): runs only with
RESTFUL_CHECKER_E2E=1.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest
from conftest import document

from restful_checker import __version__

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    os.environ.get("RESTFUL_CHECKER_E2E") != "1", reason="set RESTFUL_CHECKER_E2E=1"
)
SPEC = document({"/v1/users": {"get": {"responses": {}}}, "/v1/files": {
    "post": {"requestBody": {"content": {"multipart/form-data": {}}},
             "responses": {"2XX": {}, "4XX": {}}}}})  # fmt: skip


def run(*command: str | Path, cwd: Path) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("RESTFUL_CHECKER_E2E")  # a suite run from here must not start this one again
    done = subprocess.run(
        [str(part) for part in command], cwd=cwd, capture_output=True, text=True, check=False,
        encoding="utf-8", env=env,
    )  # fmt: skip
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def fresh_venv(folder: Path) -> tuple[Path, Path]:
    venv.create(folder, with_pip=True)
    scripts = folder / ("Scripts" if os.name == "nt" else "bin")
    return scripts, scripts / "python"


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    run(sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", out, ROOT, cwd=out)
    return out


def test_archive_contents(dist: Path) -> None:
    names = zipfile.ZipFile(next(dist.glob("*.whl"))).namelist()
    for needed in ("restful_checker/data/style.css", "restful_checker/py.typed",
                   "restful_checker/report/json_report.py"):  # fmt: skip
        assert needed in names
    assert any(name.endswith("licenses/LICENSE") for name in names)
    assert all(name.startswith(("restful_checker/", "restful_checker-")) for name in names)
    metadata = (
        zipfile.ZipFile(next(dist.glob("*.whl")))
        .read(f"restful_checker-{__version__}.dist-info/METADATA")
        .decode()
    )
    assert "Requires-Python: >=3.8" in metadata and "beautifulsoup4" not in metadata
    sdist = [name.split("/", 1)[1] for name in tarfile.open(next(dist.glob("*.tar.gz"))).getnames()]
    assert "tests/upstream/MANIFEST.json" in sdist and "LICENSE" in sdist
    assert not [
        n for n in sdist if n.startswith("tests/upstream/") and n != "tests/upstream/MANIFEST.json"
    ]
    assert not [
        n
        for n in sdist
        if n.endswith((".pyc", ".coverage")) or "REPORT" in n or "IMPROVEMENTS" in n
    ]


def test_installed_wheel(dist: Path, tmp_path: Path) -> None:
    scripts, python = fresh_venv(tmp_path / "venv")
    run(python, "-m", "pip", "install", "-q", next(dist.glob("*.whl")), cwd=tmp_path)
    work = tmp_path / "empty"
    work.mkdir()
    spec = work / "openapi.json"
    spec.write_text(json.dumps(SPEC), "utf-8")
    out = run(scripts / "restful-checker", spec, "--output-format", "both", "-q", cwd=work)
    assert out == ""
    report = json.loads((work / "html" / "rest_report.json").read_text(encoding="utf-8"))
    assert [s.get("httpMethods") for s in report["sections"][:2]] == [["POST"], ["GET"]]
    run(python, "-m", "restful_checker", spec, "--output-folder", "o", "-q", cwd=work)
    assert (work / "o" / "rest_report.html").is_file()
    code = "import sys, restful_checker as r; print(r.__version__, 'bs4' in sys.modules)"
    assert run(python, "-c", code, cwd=work).split() == [__version__, "False"]


def test_upgrade_from_pypi_3_1_1(dist: Path, tmp_path: Path) -> None:
    scripts, python = fresh_venv(tmp_path / "venv")
    run(python, "-m", "pip", "install", "-q", "restful-checker==3.1.1", cwd=tmp_path)
    spec = tmp_path / "openapi.json"
    spec.write_text(json.dumps(SPEC), "utf-8")
    before = run(scripts / "restful-checker", "--version", cwd=tmp_path)
    assert before.split()[-1] == "3.1.1"
    run(python, "-m", "pip", "install", "-q", next(dist.glob("*.whl")), cwd=tmp_path)
    assert run(scripts / "restful-checker", "--version", cwd=tmp_path).split()[-1] == __version__
    run(scripts / "restful-checker", spec, "--output-format", "json", "-q", cwd=tmp_path)
    report = json.loads((tmp_path / "html" / "rest_report.json").read_text(encoding="utf-8"))
    files = next(s for s in report["sections"] if s.get("path") == "/v1/files")
    content = next(i for i in files["items"] if i["category"] == "Content Types")
    assert content["messages"][0]["level"] == "info"


def test_suite_from_the_sdist(dist: Path, tmp_path: Path) -> None:
    with tarfile.open(next(dist.glob("*.tar.gz"))) as archive:
        if hasattr(tarfile, "data_filter"):
            archive.extractall(tmp_path, filter="data")
        else:
            archive.extractall(tmp_path)  # our own archive, Python before 3.12
    source = next(tmp_path.glob("restful_checker-*"))
    scripts, python = fresh_venv(tmp_path / "venv")
    run(python, "-m", "pip", "install", "-q", source, "pytest", cwd=tmp_path)
    os.rename(source / "restful_checker", source / "_restful_checker")  # use the installed one
    run(python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", tmp_path / "t",
        cwd=source)  # fmt: skip
