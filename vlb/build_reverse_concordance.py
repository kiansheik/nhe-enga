#!/usr/bin/env python3
"""Rebuild the compact VLB source-to-dictionary review inventory."""
from __future__ import annotations

import argparse
from pathlib import Path

from mining.reverse_concordance import write_reverse_concordance


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "vlb/mining/reverse-output",
        help="Output directory (must not be a frozen V1/V2 experiment directory).",
    )
    args = parser.parse_args()
    summary = write_reverse_concordance(root, args.output)
    print(summary["counts"])
    print(f"artifact_sha256={summary['artifact_sha256']}")


if __name__ == "__main__":
    main()
