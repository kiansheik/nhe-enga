#!/usr/bin/env python3
"""Validate, import, and export the durable VLB correction ledger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from corrections.ledger import (
    CorrectionContext,
    LedgerError,
    export_feedback,
    import_events,
    load_ledger,
    parse_issue_body,
    parse_submission,
    validate_events,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = ROOT / "vlb/corrections/ledger.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root containing vlb/source and vlb/data",
    )
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Validate every ledger event and its history")
    importer = commands.add_parser(
        "import", help="Validate and append an idempotent submission"
    )
    importer.add_argument("--input", type=Path, required=True)
    importer.add_argument(
        "--issue-body",
        action="store_true",
        help="Extract the fenced submission from a GitHub issue body",
    )
    importer.add_argument("--dry-run", action="store_true")
    exporter = commands.add_parser(
        "export", help="Export approved current decisions for regression or training"
    )
    exporter.add_argument("--kind", choices=["regression", "training"], required=True)
    exporter.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        context = CorrectionContext(args.root)
        if args.command == "validate":
            summary = validate_events(context, load_ledger(args.ledger))
            summary.pop("latest")
        elif args.command == "import":
            raw = args.input.read_text(encoding="utf-8")
            incoming = (
                parse_issue_body(raw)
                if args.issue_body
                else parse_submission(json.loads(raw))
            )
            summary = import_events(
                context, args.ledger, incoming, write=not args.dry_run
            )
            summary["dry_run"] = args.dry_run
        else:
            events = load_ledger(args.ledger)
            validate_events(context, events)
            payload = export_feedback(events, args.kind)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            summary = {
                "kind": args.kind,
                "records": len(payload["records"]),
                "output": str(args.output),
            }
    except (LedgerError, json.JSONDecodeError, OSError) as exc:
        parser.exit(2, f"correction ledger error: {exc}\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
