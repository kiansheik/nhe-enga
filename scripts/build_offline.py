#!/usr/bin/env python3
"""Prepare the *deployed* website and generate hash-addressed offline packs.

No dictionary/source assets enter the APK. Run after image optimization and
VuePress, never against the source checkout. RSA signatures cover exact payload
bytes (not a client's JSON serialization). Unsigned catalogs are browser/debug
only; release Android builds reject them.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = "/nhe-enga/"
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/"
PYODIDE_LOCAL = BASE + "vendor/pyodide/v0.25.0/"
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
CORE = {
    "index.html",
    "styles.css",
    "manifest.json",
    "favicon.ico",
    "icon.png",
    "ical.png",
    "neologisms.csv",
    "offline/index.html",
    "offline/ui.js",
    "offline/register.js",
    "sw.js",
    "docs/dict-conjugated.json.gz",
    "docs/dooley_2006_mbya_dic.json.gz",
    "docs/extracted_entries_nheengatu.tar.gz",
    "docs/citations.json",
}
REQUIRED = {
    "index.html",
    "styles.css",
    "js/pako.min.js",
    "js/papaparse.min.js",
    "js/index.js",
    "katu/index.html",
    "mbya/index.html",
    "quiz/index.html",
    "docs/dict-conjugated.json.gz",
    "docs/dooley_2006_mbya_dic.json.gz",
    "docs/extracted_entries_nheengatu.tar.gz",
    "docs/primary_sources/index.html",
}
SOURCE_NAMES = {
    "vlb": "Vocabulário na Língua Brasílica (VLB)",
    "ancharte": "Anchieta — Arte",
    "arcat1618": "Araújo — Catecismo (1618)",
    "betcomp": "Bettendorff — Compêndio",
    "lerhist": "Léry — História",
    "cartas_portiguara": "Cartas Potiguaras",
    "evreux1929": "Évreux (1929)",
}
REPLACEMENTS = {
    "https://cdnjs.cloudflare.com/ajax/libs/pako/2.0.3/pako.min.js": BASE
    + "js/pako.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js": BASE
    + "js/papaparse.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.0/jszip.min.js": BASE
    + "vendor/jszip-3.10.0.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js": BASE
    + "vendor/FileSaver-2.0.5.min.js",
    PYODIDE: PYODIDE_LOCAL,
}


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: str) -> str:
    parts = PurePosixPath(value).parts
    if (
        not value
        or value.startswith("/")
        or any(c in value for c in "\\%?#\x00")
        or any(p in (".", "..") for p in value.split("/"))
        or str(PurePosixPath(value)) != value
        or not parts
    ):
        raise ValueError(f"Unsafe artifact path: {value!r}")
    return value


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vendor(url: str, destination: Path, expected: str | None = None) -> None:
    """Versioned HTTPS allowlist; record output hashes in the deployed report.

    Pyodide package wheels additionally use its upstream lockfile SHA-256s.
    Cache bytes are always checked when an upstream hash is available.
    """
    if not (url.startswith(PYODIDE) or url in REPLACEMENTS):
        raise ValueError(f"Unapproved vendor URL: {url}")
    cache = Path(os.environ.get("OFFLINE_VENDOR_CACHE", ROOT / ".cache/offline-vendor"))
    cached = cache / digest(url.encode())
    cache.mkdir(parents=True, exist_ok=True)
    if not cached.exists() or (expected and file_hash(cached) != expected):
        request = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if not response.url.startswith("https://"):
                raise ValueError("Vendor download redirected away from HTTPS")
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as output:
                temporary = Path(output.name)
                shutil.copyfileobj(response, output)
        if expected and file_hash(temporary) != expected:
            temporary.unlink()
            raise ValueError(f"Upstream package hash mismatch: {url}")
        temporary.replace(cached)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, destination)


def prepare(build: Path) -> None:
    # Do not copy source/config/keys from offline/ into the public artifact.
    (build / "offline").mkdir(exist_ok=True)
    for name in ("index.html", "ui.js", "register.js"):
        shutil.copyfile(ROOT / "offline" / name, build / "offline" / name)
    shutil.copyfile(ROOT / "offline/sw.js", build / "sw.js")
    needed: set[str] = set()
    html_files = list(build.rglob("*.html"))
    text_files = html_files + list(build.rglob("*.js")) + list(build.rglob("*.css"))
    for path in text_files:
        if "/vendor/" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for remote, local in REPLACEMENTS.items():
            if remote in text:
                needed.add(remote)
                text = text.replace(remote, local)
        # All same-site references remain on the WebView's local HTTPS origin.
        text = text.replace("https://kiansheik.io/nhe-enga/", BASE)
        if path.suffix == ".html":
            text = re.sub(
                r"loadPyodide\(\s*\)",
                f"loadPyodide({{indexURL: '{PYODIDE_LOCAL}'}})",
                text,
            )
            # Snapshot the remote sheet used by the neologisms page. No runtime
            # Google Sheets dependency is needed to read the published data.
            text = re.sub(
                r"https://docs\.google\.com/spreadsheets/d/[^\s\"'<>]+/export\?[^\s\"'<>]+",
                BASE + "neologisms.csv",
                text,
            )
            if "offline/register.js" not in text:
                tag = f'<script defer src="{BASE}offline/register.js"></script>'
                text = (
                    text.replace("</head>", tag + "\n</head>", 1)
                    if "</head>" in text
                    else text + tag
                )
        # Catch unhandled executable CDN references without mistaking normal
        # scholarly hyperlinks for dependencies. Dynamic URLs get a report too.
        for url in re.findall(r"(?:src|href)\s*=\s*['\"]((?:https?:)?//[^'\"]+)", text):
            if any(
                host in url
                for host in ("cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com")
            ):
                raise ValueError(f"Unmirrored runtime dependency in {path}: {url}")
        if text != original:
            path.write_text(text, encoding="utf-8")
    for remote in sorted(needed):
        local = REPLACEMENTS[remote]
        if remote == PYODIDE or "/vendor/" not in local:
            continue
        vendor(remote, build / local.removeprefix(BASE))
    if PYODIDE in needed:
        target = build / "vendor/pyodide/v0.25.0"
        for name in (
            "pyodide.js",
            "pyodide.asm.js",
            "pyodide.asm.wasm",
            "python_stdlib.zip",
            "pyodide-lock.json",
        ):
            vendor(PYODIDE + name, target / name)
        lock = json.loads((target / "pyodide-lock.json").read_text())
        visited: set[str] = set()

        def package(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            info = lock["packages"][name]
            for dependency in info.get("depends", []):
                package(dependency)
            filename = safe_path(info["file_name"])
            vendor(PYODIDE + filename, target / filename, info["sha256"])

        package("micropip")
    report = [
        dict(
            path=str(p.relative_to(build)), bytes=p.stat().st_size, sha256=file_hash(p)
        )
        for p in sorted((build / "vendor").rglob("*"))
        if p.is_file()
    ]
    (build / "offline/vendor-report.json").write_bytes(canonical(report))


def pack_for(path: str) -> str:
    p = PurePosixPath(path)
    if (
        path.startswith("docs/primary_sources/")
        and len(p.parts) >= 4
        and p.suffix.lower() in IMAGES
    ):
        # Preserve the real edition/folio URLs. Never infer printed pagination.
        return "source-" + p.parts[2]
    if (
        path in CORE
        or path.startswith(("js/", "katu/", "mbya/", "quiz/", "neologisms/"))
        or (
            path.startswith("docs/primary_sources/")
            and p.suffix in {".html", ".css", ".js", ".json", ".txt"}
        )
    ):
        return "core"
    return "tools"


def generate(build: Path, sequence: int, private_key: str | None = None) -> dict:
    if sequence < 1:
        raise ValueError(
            "OFFLINE_SEQUENCE must be a positive, monotonically increasing integer"
        )
    missing = sorted(p for p in REQUIRED if not (build / p).is_file())
    if missing:
        raise ValueError("Missing offline essentials: " + ", ".join(missing))
    packs: dict[str, list[dict]] = {}
    for path in sorted(build.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlink in public artifact: {path}")
        if not path.is_file():
            continue
        rel = str(path.relative_to(build))
        if (
            rel.startswith(("downloads/", "offline/packs/", "translate/"))
            or rel
            in {
                "offline/catalog.json",
                "offline/vendor-report.json",
                "CNAME",
                ".nojekyll",
            }
            or any(part.startswith(".") for part in Path(rel).parts)
        ):
            continue
        safe_path(rel)
        mime = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        if rel.endswith(".gz"):
            mime = "application/gzip"  # NOT Content-Encoding: gzip; callers use pako.
        if rel.endswith(".wasm"):
            mime = "application/wasm"
        packs.setdefault(pack_for(rel), []).append(
            {
                "path": rel,
                "sha256": file_hash(path),
                "bytes": path.stat().st_size,
                "mime": mime,
            }
        )
    output = build / "offline/packs"
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for identifier, files in sorted(packs.items()):
        content = canonical({"id": identifier, "files": files})
        sha = digest(content)
        name = f"{identifier}-{sha}.json"
        (output / name).write_bytes(content)
        title = {
            "core": "Dicionários e citações",
            "tools": "Gramática e ferramentas",
        }.get(identifier)
        if title is None:
            book = identifier.removeprefix("source-")
            title = SOURCE_NAMES.get(book, book)
        entries.append(
            {
                "id": identifier,
                "title": title,
                "url": "offline/packs/" + name,
                "sha256": sha,
                "bytes": len(content),
                "downloadBytes": sum(f["bytes"] for f in files),
                "count": len(files),
                "kind": "source" if identifier.startswith("source-") else identifier,
            }
        )
    payload = canonical(
        {
            "schema": 1,
            "minShell": 1,
            "base": BASE,
            "sequence": sequence,
            "packs": entries,
        }
    )
    signature = b""
    if private_key:
        signature = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", private_key],
            input=payload,
            check=True,
            capture_output=True,
        ).stdout
    envelope = {
        "payload": base64.b64encode(payload).decode(),
        "signature": base64.b64encode(signature).decode(),
    }
    (build / "offline/catalog.json").write_bytes(canonical(envelope))
    return json.loads(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    build = args.build.resolve()
    if build == ROOT or not build.is_dir():
        parser.error(
            "Pass an existing assembled Pages directory, never the repository root"
        )
    if args.prepare:
        prepare(build)
    key = os.environ.get("OFFLINE_SIGNING_KEY")
    catalog = generate(
        build, int(os.environ.get("OFFLINE_SEQUENCE", str(int(time.time())))), key
    )
    print(
        f"Offline catalog: {len(catalog['packs'])} packs; "
        + ("signed" if key else "UNSIGNED (browser/debug only)")
    )


if __name__ == "__main__":
    main()
