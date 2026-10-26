#!/usr/bin/env python3
"""Measure a Pages artifact or a complete GitHub Git Trees JSON response.

This is a read-only preflight. The default 900 MB budget is a project buffer
below GitHub Pages' documented 1 GB limit, not a separate GitHub limit.
No network access, image conversion, Git writes, or deployment is performed.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import stat
import sys


DEFAULT_BUDGET_BYTES = 900_000_000
GIT_FILE_LIMIT_BYTES = 100 * 1024 * 1024


def entries_from_directory(root: Path) -> list[tuple[str, int]]:
    if root.is_symlink():
        raise ValueError(f"Resolve symlink before measuring the artifact: {root}")
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    entries = []

    def raise_walk_error(error: OSError) -> None:
        raise error

    for directory, subdirectories, files in os.walk(root, onerror=raise_walk_error):
        subdirectories[:] = [name for name in subdirectories if name != ".git"]
        for name in subdirectories:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(
                    f"Resolve symlink before measuring the artifact: {path.relative_to(root)}"
                )
        for name in files:
            if name == ".git":
                continue
            path = Path(directory) / name
            relative = path.relative_to(root)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Cannot measure non-regular file: {relative}")
            entries.append((relative.as_posix(), info.st_size))
    return entries


def entries_from_tree(path: Path) -> list[tuple[str, int]]:
    tree = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tree, dict):
        raise ValueError("Expected a GitHub Git Trees response object")
    if tree.get("truncated") is not False:
        raise ValueError("Git tree must explicitly report truncated=false")
    if not isinstance(tree.get("tree"), list):
        raise ValueError("Expected a GitHub Git Trees response with a tree list")
    entries = []
    seen = set()
    directories = set()
    for entry in tree["tree"]:
        if not isinstance(entry, dict):
            raise ValueError("Every Git tree entry must be an object")
        name = entry.get("path")
        if (
            not isinstance(name, str)
            or not name
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or name in seen
        ):
            raise ValueError("Git paths must be relative, nonempty and unique")
        seen.add(name)
        if entry.get("type") == "tree":
            directories.add(name)
            continue
        if entry.get("type") != "blob" or entry.get("mode") == "120000":
            raise ValueError(f"Cannot measure non-file entry: {name}")
        size = entry.get("size")
        if type(size) is not int or size < 0:
            raise ValueError(f"Missing or invalid byte count: {name}")
        entries.append((name, size))
    parents = {name.rpartition("/")[0] for name in seen} - {""}
    if parents - directories:
        raise ValueError("Recursive Git tree is missing parent directory entries")
    unexpanded = directories - parents
    if unexpanded:
        raise ValueError(
            f"Git tree has unexpanded directories; request recursive=1: {', '.join(sorted(unexpanded))}"
        )
    return entries


def summarize(
    entries: list[tuple[str, int]], max_bytes: int, max_file_bytes: int
) -> dict:
    groups = defaultdict(lambda: {"files": 0, "bytes": 0})
    for name, size in entries:
        parts = name.split("/")
        group = (
            "/".join(parts[:3])
            if name.startswith("docs/primary_sources/") and len(parts) > 3
            else parts[0]
        )
        groups[group]["files"] += 1
        groups[group]["bytes"] += size
    total = sum(size for _, size in entries)
    oversized = [
        {"path": name, "bytes": size}
        for name, size in sorted(entries)
        if size > max_file_bytes
    ]
    return {
        "files": len(entries),
        "total_bytes": total,
        "budget_bytes": max_bytes,
        "remaining_budget_bytes": max_bytes - total,
        "max_file_bytes": max_file_bytes,
        "oversized_files": oversized,
        "within_budget": total <= max_bytes and not oversized,
        "groups": dict(
            sorted(groups.items(), key=lambda item: (-item[1]["bytes"], item[0]))
        ),
        "measurement": "Sum of file bytes; excludes Git history and filesystem overhead",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path)
    parser.add_argument("--tree-json", type=Path)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_BUDGET_BYTES)
    parser.add_argument("--max-file-bytes", type=int, default=GIT_FILE_LIMIT_BYTES)
    parser.add_argument(
        "--json", action="store_true", help="Print the full JSON report"
    )
    args = parser.parse_args()
    if (args.directory is None) == (args.tree_json is None):
        parser.error("Provide either an artifact directory or --tree-json, exclusively")
    if args.max_bytes < 1 or args.max_file_bytes < 1:
        parser.error("Byte limits must be positive integers")
    try:
        entries = (
            entries_from_tree(args.tree_json)
            if args.tree_json is not None
            else entries_from_directory(args.directory)
        )
        report = summarize(entries, args.max_bytes, args.max_file_bytes)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Cannot establish a complete size measurement: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Files: {report['files']:,}")
        print(
            f"Total: {report['total_bytes']:,} bytes ({report['total_bytes'] / 1e6:.1f} MB)"
        )
        print(f"Project budget: {args.max_bytes:,} bytes")
        print(f"Remaining budget: {report['remaining_budget_bytes']:,} bytes")
        for name, group in list(report["groups"].items())[:12]:
            print(f"  {group['bytes']:>12,} bytes  {group['files']:>5} files  {name}")
        for entry in report["oversized_files"]:
            print(f"Oversized file: {entry['path']} ({entry['bytes']:,} bytes)")
        print("PASS" if report["within_budget"] else "OVER BUDGET")
    return 0 if report["within_budget"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
