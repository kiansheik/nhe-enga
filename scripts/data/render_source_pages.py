#!/usr/bin/env python3
"""Render verified source PDF pages as numbered JPEG images.

Requires PyMuPDF and Pillow. Run from the repository root; see the source's
README for the download URL, checksum, printed-page mapping, and whether the
manifest selects a cited-page subset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image


def manifest_value(manifest: dict, path: str):
    value = manifest
    for part in path.split("."):
        value = value[part]
    return value


def render_image(page, settings: dict, crop_box=None) -> Image.Image:
    clip = fitz.Rect(crop_box) if crop_box is not None else page.rect
    if not page.rect.contains(clip) or clip.is_empty:
        raise ValueError(f"crop box {tuple(clip)} is outside page {tuple(page.rect)}")

    target_width = settings.get("target_width_px")
    if target_width is not None:
        if type(target_width) is not int or target_width < 1:
            raise ValueError("render.target_width_px must be a positive integer")
        scale = target_width / clip.width
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            clip=clip,
            colorspace=fitz.csRGB,
            alpha=False,
        )
    else:
        dpi = settings.get("dpi")
        if type(dpi) is not int or dpi < 1:
            raise ValueError("render.dpi must be a positive integer")
        pixmap = page.get_pixmap(
            dpi=dpi,
            clip=clip,
            colorspace=fitz.csRGB,
            alpha=False,
        )
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    if target_width is not None and image.width != target_width:
        target_height = round(image.height * target_width / image.width)
        image = image.resize(
            (target_width, target_height), resample=Image.Resampling.LANCZOS
        )
    return image


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
        if args.page is not None:
            selected_pages = sorted(set(args.page))
        elif selection := manifest.get("selection"):
            pagination = manifest["pagination"]
            offset = pagination["printed_page_to_image_offset"]
            first_printed = pagination["first_printed_page"]
            last_printed = pagination["last_printed_page"]
            context = selection["context_pages_each_side"]
            printed_pages = manifest["verification"]["all_cited_pages"]
            selected_pages = sorted(
                {
                    printed_page + offset + delta
                    for printed_page in printed_pages
                    for delta in range(-context, context + 1)
                    if first_printed <= printed_page + delta <= last_printed
                    and 0 <= printed_page + offset + delta < len(document)
                }
            )
        else:
            selected_pages = None
        if selected_pages is not None and any(
            page < 0 or page >= len(document) for page in selected_pages
        ):
            parser.error("--page must be a valid zero-based PDF index")

        target_path = settings.get("targets_path")
        if target_path:
            raw_targets = manifest_value(manifest, target_path)
            targets = [
                {
                    "pdf_index": target["pdf_index"],
                    "output": target["image"],
                    "crop_box": target.get("crop_box_pdf_points"),
                }
                for target in raw_targets
                if selected_pages is None or target["pdf_index"] in selected_pages
            ]
        else:
            pages = (
                selected_pages if selected_pages is not None else range(len(document))
            )
            targets = [
                {"pdf_index": index, "output": f"{index}.jpg", "crop_box": None}
                for index in pages
            ]
        if len({target["output"] for target in targets}) != len(targets):
            parser.error("render targets must have unique image filenames")

        output_dir.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        for target in targets:
            index = target["pdf_index"]
            if type(index) is not int or index < 0 or index >= len(document):
                parser.error("render target has an invalid zero-based PDF index")
            # Render the composed PDF page or its manifest-defined crop, rather
            # than extracting an embedded scan and losing visible PDF layers.
            try:
                image = render_image(document[index], settings, target["crop_box"])
            except (TypeError, ValueError) as exc:
                parser.error(f"cannot render PDF index {index}: {exc}")
            output_path = output_dir / target["output"]
            if output_path.parent != output_dir or output_path.suffix.lower() != ".jpg":
                parser.error("render target image must be a plain .jpg filename")
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
            f"Rendered {len(targets)} images to {output_dir} "
            f"({total_bytes / 1024 / 1024:.1f} MiB); PDF SHA-256 verified."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
