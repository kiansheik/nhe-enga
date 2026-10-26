#!/usr/bin/env python3
"""Optimize copied primary-source page images for the GitHub Pages artifact."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_MAX_WIDTH = 1800
DEFAULT_MAX_HEIGHT = 2400
DEFAULT_QUALITY = 82
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def int_from_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer, got {value!r}") from exc


def iter_images(primary_sources_dir: Path, books: set[str] | None = None):
    for path in sorted(primary_sources_dir.iterdir()):
        if not path.is_dir() or (books is not None and path.name not in books):
            continue
        for image_path in sorted(path.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                yield path.name, image_path


def as_rgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        background = Image.new("RGB", image.size, "white")
        background.paste(image.convert("RGBA"), mask=image.convert("RGBA").split()[-1])
        return background
    return image.convert("RGB")


def optimize_image(
    image_path: Path,
    max_size: tuple[int, int],
    quality: int,
    destination: Path | None = None,
) -> tuple[Path, int, int]:
    original_size = image_path.stat().st_size
    output_path = (
        destination if destination is not None else image_path.with_suffix(".jpg")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f"{output_path.name}.tmp")

    with Image.open(image_path) as original:
        image = as_rgb(original)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(
            temp_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )

    if destination is None and output_path != image_path:
        image_path.unlink()
    temp_path.replace(output_path)
    return output_path, original_size, output_path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary_sources_dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--books", nargs="+")
    args = parser.parse_args()

    primary_sources_dir = args.primary_sources_dir
    if not primary_sources_dir.exists():
        raise SystemExit(f"Missing primary-source directory: {primary_sources_dir}")
    output_dir = args.output_dir or primary_sources_dir
    if args.output_dir and output_dir.resolve() == primary_sources_dir.resolve():
        raise SystemExit("Output directory must differ from the source directory")
    if args.books:
        for book in args.books:
            if Path(book).name != book or not (primary_sources_dir / book).is_dir():
                raise SystemExit(f"Missing or invalid source book: {book}")
    output_dir.mkdir(parents=True, exist_ok=True)

    max_width = int_from_env("PAGES_IMAGE_MAX_WIDTH", DEFAULT_MAX_WIDTH)
    max_height = int_from_env("PAGES_IMAGE_MAX_HEIGHT", DEFAULT_MAX_HEIGHT)
    quality = int_from_env("PAGES_IMAGE_QUALITY", DEFAULT_QUALITY)
    if max_width < 1 or max_height < 1:
        raise SystemExit(
            "PAGES_IMAGE_MAX_WIDTH and PAGES_IMAGE_MAX_HEIGHT must be positive"
        )
    if not 1 <= quality <= 95:
        raise SystemExit("PAGES_IMAGE_QUALITY must be between 1 and 95")

    books: dict[str, str] = {}
    total_before = 0
    total_after = 0
    optimized_count = 0

    for book_name, image_path in iter_images(
        primary_sources_dir, set(args.books) if args.books else None
    ):
        destination = (
            output_dir / book_name / image_path.with_suffix(".jpg").name
            if args.output_dir
            else None
        )
        output_path, before, after = optimize_image(
            image_path, (max_width, max_height), quality, destination
        )
        books[book_name] = output_path.suffix
        total_before += before
        total_after += after
        optimized_count += 1

    manifest = {
        "format": "jpg",
        "books": dict(sorted(books.items())),
        "quality": quality,
        "max_width": max_width,
        "max_height": max_height,
        "optimized_count": optimized_count,
        "bytes_before": total_before,
        "bytes_after": total_after,
    }
    (output_dir / "image-formats.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    saved = total_before - total_after
    print(
        "Optimized primary-source images: "
        f"{optimized_count} files, {total_before / 1024 / 1024:.1f} MB -> "
        f"{total_after / 1024 / 1024:.1f} MB "
        f"({saved / 1024 / 1024:.1f} MB saved)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
