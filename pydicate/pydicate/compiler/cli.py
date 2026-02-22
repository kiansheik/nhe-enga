from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import (
    build_registry,
    decompile,
    parse_annotated,
    token_from_raw,
)


_HELP = """Commands:
  :help                  Show this help
  :quit / :q             Exit
  :mode annotated|tokens Input mode (default: annotated)
  :emit ir|pydicate       Output rendering (default: pydicate)
  :beam N                Beam size (default: 32)
  :seq on|off            Allow SEQ rendering (default: on)
  :seqop OP              Operator for SEQ when emitting pydicate (default: +)
  :registry              Show discovered Predicate subclasses

Input modes:
  annotated  -> a single annotated string: "na[NEGATION_PARTICLE:NA] ab[VERB]"
  tokens     -> JSON list of tokens, e.g.:
                [{"m":"na","t":"NEGATION_PARTICLE"},{"m":"ab","t":"VERB"}]
"""


def _parse_tokens_payload(payload: str) -> List[Any]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("Token JSON must be a list")
    return [token_from_raw(x) for x in data]


def _print_registry() -> None:
    registry = build_registry()
    names = sorted(registry.predicates.keys())
    print("Predicates:")
    for name in names:
        info = registry.predicates[name]
        ops = ", ".join(info.operators) if info.operators else "-"
        methods = ", ".join(info.methods) if info.methods else "-"
        print(f"  {name}  ops=[{ops}]  methods=[{methods}]")


def run_once(
    payload: str,
    *,
    mode: str,
    emit: str,
    beam: int,
    allow_seq: bool,
    seq_op: str,
) -> None:
    if mode == "annotated":
        tokens = parse_annotated(payload)
    elif mode == "tokens":
        tokens = _parse_tokens_payload(payload)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    result = decompile(
        tokens,
        beam_size=beam,
        emit=emit,
        allow_seq=allow_seq,
        seq_op=seq_op,
    )
    print(result.code)
    print(f"cost={result.cost:.2f}")


def repl(
    *,
    mode: str = "annotated",
    emit: str = "pydicate",
    beam: int = 32,
    allow_seq: bool = True,
    seq_op: str = "+",
) -> None:
    history_path = os.path.expanduser("~/.pydicate_compiler_history")
    try:
        import readline  # type: ignore
    except Exception:
        readline = None

    if readline:
        try:
            readline.read_history_file(history_path)
        except FileNotFoundError:
            pass
        except Exception:
            pass

    print("pydicate.compiler REPL (:help for commands)")
    try:
        while True:
            try:
                line = input("compiler> ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue

            if line.startswith(":"):
                parts = line.split()
                cmd = parts[0][1:]
                args = parts[1:]

                if cmd in {"quit", "q"}:
                    break
                if cmd == "help":
                    print(_HELP)
                    continue
                if cmd == "mode" and args:
                    mode = args[0]
                    print(f"mode={mode}")
                    continue
                if cmd == "emit" and args:
                    emit = args[0]
                    print(f"emit={emit}")
                    continue
                if cmd == "beam" and args:
                    beam = int(args[0])
                    print(f"beam={beam}")
                    continue
                if cmd == "seq" and args:
                    allow_seq = args[0].lower() in {"on", "true", "1", "yes"}
                    print(f"seq={allow_seq}")
                    continue
                if cmd == "seqop" and args:
                    seq_op = args[0]
                    print(f"seqop={seq_op}")
                    continue
                if cmd == "registry":
                    _print_registry()
                    continue

                print("Unknown command. :help for options.")
                continue

            try:
                run_once(
                    line,
                    mode=mode,
                    emit=emit,
                    beam=beam,
                    allow_seq=allow_seq,
                    seq_op=seq_op,
                )
            except Exception as exc:
                print(f"error: {exc}")
    finally:
        if readline:
            try:
                readline.write_history_file(history_path)
            except Exception:
                pass


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="pydicate compiler REPL")
    parser.add_argument(
        "payload",
        nargs="?",
        help="Single input payload (annotated string or token JSON). If omitted, starts REPL.",
    )
    parser.add_argument("--mode", default="annotated", choices=["annotated", "tokens"])
    parser.add_argument("--emit", default="pydicate", choices=["ir", "pydicate"])
    parser.add_argument("--beam", type=int, default=32)
    parser.add_argument("--seq", dest="allow_seq", action="store_true", default=True)
    parser.add_argument("--no-seq", dest="allow_seq", action="store_false")
    parser.add_argument("--seqop", default="+")

    args = parser.parse_args(argv)

    if args.payload:
        run_once(
            args.payload,
            mode=args.mode,
            emit=args.emit,
            beam=args.beam,
            allow_seq=args.allow_seq,
            seq_op=args.seqop,
        )
    else:
        repl(
            mode=args.mode,
            emit=args.emit,
            beam=args.beam,
            allow_seq=args.allow_seq,
            seq_op=args.seqop,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
