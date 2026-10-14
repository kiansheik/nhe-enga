#!/usr/bin/env python3
"""Text-only Gradle bootstrap: verify the official pinned distribution before use.

Checksum: https://gradle.org/release-checksums/#v8.11.1
No opaque wrapper JAR is committed. Requires Python 3 and JDK 17+.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

VERSION = "8.11.1"
SHA256 = "f397b287023acdba1e9f6fc5ea72d22dd63669d59ed4a289a29b1a76eee151c6"


def main():
    root = Path(os.environ.get("GRADLE_USER_HOME", Path.home() / ".gradle")) / "nhe-bootstrap"
    executable = root / f"gradle-{VERSION}/bin/gradle"
    if not executable.is_file():
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            archive = Path(tmp) / "gradle.zip"
            with urllib.request.urlopen(f"https://services.gradle.org/distributions/gradle-{VERSION}-bin.zip", timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
            h = hashlib.sha256()
            with archive.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
            if h.hexdigest() != SHA256:
                raise RuntimeError("Gradle distribution checksum mismatch")
            with zipfile.ZipFile(archive) as z:
                z.extractall(tmp)  # Entire archive is pinned to Gradle's published hash.
            extracted = Path(tmp) / f"gradle-{VERSION}"
            (extracted / "bin/gradle").chmod(0o755)
            try:
                extracted.rename(executable.parents[1])
            except FileExistsError:
                pass  # Another concurrent bootstrap completed first.
    return subprocess.call([str(executable), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
