"""Tiny synthetic site for offline tests; never uploads real dictionaries/media."""

import argparse
import base64
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "build_offline", ROOT / "scripts/build_offline.py"
)
build_offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_offline)
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII="
)


def fixture(build: Path, version="v1", sequence=1):
    build.mkdir(parents=True, exist_ok=True)
    for name in build_offline.REQUIRED:
        p = build / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(
                "<!doctype html><html><head></head><body>Fixture</body></html>"
                if p.suffix == ".html"
                else "/* synthetic fixture */"
            )
    (build / "index.html").write_text(
        f'<!doctype html><html><head></head><body><main id="version">{version}</main><script src="/nhe-enga/js/index.js"></script></body></html>'
    )
    (build / "docs/primary_sources/index.html").write_text(
        """<!doctype html><html><head></head><body><img id="scan"><script>
const p=new URLSearchParams(location.search);document.getElementById('scan').src='/nhe-enga/docs/primary_sources/'+(p.get('book_name')||'vlb')+'/'+(p.get('page_number')||'1')+'.png';</script></body></html>"""
    )
    for book in ("vlb", "lerhist", "cartas_portiguara"):
        path = build / f"docs/primary_sources/{book}/1.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(PNG)
    (build / "docs/primary_sources/lerhist/2.png").write_bytes(
        PNG + b"not-the-same-file"
    )
    (build / "manifest.json").write_text((ROOT / "manifest.json").read_text())
    build_offline.prepare(build)
    return build_offline.generate(build, sequence)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--version", default="v1")
    p.add_argument("--sequence", type=int, default=1)
    args = p.parse_args()
    fixture(args.directory, args.version, args.sequence)
    print(f"Fixture ready: {args.directory}. Serve its parent on port 8000.")
