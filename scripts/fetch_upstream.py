"""Fetch the third-party reference files listed in tests/upstream/MANIFEST.json.

The files are not part of the repository. Their tests skip until this script has fetched
them; each download is checked against the size and sha256 in the manifest (taken after
decoding, for sources served as base64). Entries marked "living" change over time: a new
version is saved with a notice, and the tests that read it skip until the manifest is updated
after a review.

    python scripts/fetch_upstream.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "tests" / "upstream"


def main() -> int:
    manifest = json.loads((FOLDER / "MANIFEST.json").read_text(encoding="utf-8"))
    failed = 0
    for name, entry in manifest.items():
        with urllib.request.urlopen(entry["url"], timeout=60) as response:
            body = response.read()
        if entry.get("encoding") == "base64":
            body = base64.b64decode(body)
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != entry["size"] or digest != entry["sha256"]:
            print(f"{name}: got {len(body)} bytes, sha256 {digest}; manifest differs")
            if entry.get("living"):
                (FOLDER / name).write_bytes(body)  # its tests skip until it is reviewed
            else:
                failed += 1
            continue
        (FOLDER / name).write_bytes(body)
        print(f"{name}: ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
