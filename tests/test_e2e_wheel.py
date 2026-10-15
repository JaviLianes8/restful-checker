"""Build the wheel and sdist, install the wheel in a fresh venv, drive it from an empty folder.

Slow and needs the network for the dependencies: runs only with RESTFUL_CHECKER_E2E=1.
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


def run(*command: str | Path, cwd: Path) -> str:
    done = subprocess.run(
        [str(part) for part in command], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def test_installed_wheel(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    run(sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", dist, ROOT, cwd=tmp_path)
    wheel = next(dist.glob("*.whl"))
    names = zipfile.ZipFile(wheel).namelist()
    assert "restful_checker/data/style.css" in names
    assert "restful_checker/py.typed" in names
    assert "restful_checker/engine/normalizer.py" in names
    assert not any(name.startswith("tests/") for name in names)
    sdist = tarfile.open(next(dist.glob("*.tar.gz"))).getnames()
    assert not any("IMPROVEMENTS" in name or "/tests/upstream/oas" in name for name in sdist)

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    scripts = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / "python"
    run(python, "-m", "pip", "install", "-q", wheel, cwd=tmp_path)

    work = tmp_path / "empty"
    work.mkdir()
    spec = work / "openapi.json"
    spec.write_text(json.dumps(document({"/v1/users": {"get": {"responses": {}}}})), "utf-8")
    out = run(scripts / "restful-checker", spec, "--output-format", "both", "-q", cwd=work)
    assert out == ""
    report = json.loads((work / "html" / "rest_report.json").read_text(encoding="utf-8"))
    assert report["sections"][0]["httpMethods"] == ["GET"]
    run(python, "-m", "restful_checker", spec, "--output-folder", "o", "-q", cwd=work)
    assert (work / "o" / "rest_report.html").is_file()
    code = "import restful_checker as r; print(r.__version__, r.analyze_api.__name__)"
    assert run(python, "-c", code, cwd=work).split() == [__version__, "analyze_api"]
