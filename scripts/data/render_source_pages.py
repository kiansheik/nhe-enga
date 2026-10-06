#!/usr/bin/env python3
"""Render a verified source PDF as complete, numbered JPEG page images.

Requires PyMuPDF and Pillow. Run from the repository root; see the source's
README for the download URL, checksum, and printed-page mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--page", type=int, action="append", help="Zero-based PDF index; repeatable."
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    with args.pdf.open("rb") as pdf_file:
        digest = hashlib.file_digest(pdf_file, "sha256").hexdigest()
    if digest != manifest["pdf"]["sha256"]:
        parser.error("PDF SHA-256 does not match the verified source manifest")

    settings = manifest["render"]
    output_dir = args.output_dir or args.manifest.parent
    with fitz.open(args.pdf) as document:
        if len(document) != manifest["pdf"]["page_count"]:
            parser.error("PDF page count does not match the source manifest")
        pages = sorted(set(args.page)) if args.page is not None else range(len(document))
        if any(page < 0 or page >= len(document) for page in pages):
            parser.error("--page must be a valid zero-based PDF index")
        output_dir.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        for index in pages:
            # Render the whole page, not just its embedded scan: some pages
            # carry the digitizing library's credit as a visible PDF text layer.
            pixmap = document[index].get_pixmap(
                dpi=settings["dpi"], colorspace=fitz.csRGB, alpha=False
            )
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            output_path = output_dir / f"{index}.jpg"
            temporary_path = output_path.with_suffix(".jpg.tmp")
            image.save(
                temporary_path,
                "JPEG",
                quality=settings["jpeg_quality"],
                optimize=True,
                progressive=True,
            )
            temporary_path.replace(output_path)
            total_bytes += output_path.stat().st_size
        print(
            f"Rendered {len(pages)} pages to {output_dir} "
            f"({total_bytes / 1024 / 1024:.1f} MiB); PDF SHA-256 verified."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
