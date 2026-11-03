#!/usr/bin/env python3
"""Fetch and normalize Martins's diplomatic/facsimile Teatro pages.

The source manifest maps each stored critical-edition page to one or more
pages in the first, diplomatic part of Martins 1954.  Internet Archive serves
those pages from the higher-resolution searchable upload as JPEG derivatives.
This script validates their dimensions and writes stable, web-sized JPEGs.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageOps


def diplomatic_indices(manifest: dict) -> list[int]:
    mapping = manifest["manuscript_facsimiles"][
        "critical_page_to_diplomatic_pdf_indices"
    ]
    return sorted({index for indices in mapping.values() for index in indices})


def fetch_image(url: str) -> Image.Image:
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "3", url],
        check=True,
        stdout=subprocess.PIPE,
    )
    payload = result.stdout
    with Image.open(BytesIO(payload)) as source:
        source.load()
        return ImageOps.exif_transpose(source).convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/primary_sources/anchteatro1954/source.json"),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    settings = manifest["manuscript_facsimiles"]
    images = settings["images"]
    output_dir = args.output_dir or args.manifest.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    expected_width = images["source_width_px"]
    minimum_height, maximum_height = images["source_height_range_px"]
    target_width = images["target_width_px"]
    quality = images["jpeg_quality"]
    pattern = settings["source_page_image_url_pattern"]
    filename_pattern = images["filename_rule"]
    indices = diplomatic_indices(manifest)

    written = 0
    total_bytes = 0
    for index in indices:
        filename = filename_pattern.replace("{pdf_index}", str(index))
        output_path = output_dir / filename
        if output_path.parent != output_dir or output_path.suffix.lower() != ".jpg":
            parser.error("manuscript image filename must be a plain .jpg filename")
        if output_path.exists() and not args.force:
            total_bytes += output_path.stat().st_size
            continue

        image = fetch_image(pattern.replace("{pdf_index}", str(index)))
        if (
            image.width != expected_width
            or not minimum_height <= image.height <= maximum_height
        ):
            parser.error(
                f"PDF index {index} has dimensions {image.size}, expected width "
                f"{expected_width} and height {minimum_height}-{maximum_height}"
            )
        target_height = round(image.height * target_width / image.width)
        image = image.resize(
            (target_width, target_height), resample=Image.Resampling.LANCZOS
        )
        temporary_path = output_path.with_suffix(".jpg.tmp")
        image.save(
            temporary_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )
        temporary_path.replace(output_path)
        written += 1
        total_bytes += output_path.stat().st_size

    print(
        f"Prepared {len(indices)} diplomatic/facsimile pages in {output_dir} "
        f"({written} downloaded, {total_bytes / 1024 / 1024:.1f} MiB)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
