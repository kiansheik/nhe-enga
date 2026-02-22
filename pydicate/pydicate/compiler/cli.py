from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

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
  :color on|off          Enable ANSI coloring in :exec (default: auto)
  :corpus                Show corpus status (if loaded)
  :show                  Show current corpus entry
  :run                   Run current corpus entry
  :go                    :show + :run + :exec + (auto-next on success)
  :next / :prev          Move to next/previous corpus entry
  :goto N                Jump to corpus entry index (0-based)
  :mark STATUS           Mark current entry (good|done|bad|skip|clear)
  :registry              Show discovered Predicate subclasses
  :exec                  Eval last output and compare annotated tags (pydicate only)

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
    rerank_k: int,
    rerank_weight: float,
    rewrite_variants: int,
    finalize_top_k: int,
    use_lexicon: bool,
    lexicon_modules: Optional[List[str]],
    color: str = "auto",
) -> Dict[str, Any]:
    if mode == "annotated":
        tokens = parse_annotated(payload)
    elif mode == "tokens":
        tokens = _parse_tokens_payload(payload)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    if not tokens:
        raise ValueError("No tokens parsed from input")

    rerank_fn = None
    if rerank_k > 0:
        eval_env = _build_eval_env()

        def _rerank_eval(code: str) -> str:
            ast = eval(code, eval_env)
            if hasattr(ast, "eval"):
                return ast.eval(annotated=True)
            return str(ast)

        rerank_fn = _rerank_eval

    result = decompile(
        tokens,
        beam_size=beam,
        emit=emit,
        allow_seq=allow_seq,
        seq_op=seq_op,
        rerank_top_k=rerank_k,
        rerank_weight=rerank_weight,
        rerank_fn=rerank_fn,
        rewrite_max_variants=rewrite_variants,
        finalize_top_k=finalize_top_k,
        use_lexicon=use_lexicon,
        lexicon_modules=lexicon_modules,
    )
    color_enabled = _supports_color() if color == "auto" else color == "on"
    if color_enabled:
        print(_colorize_surface(result.code))
    else:
        print(result.code)
    print(f"cost={result.cost:.2f}")
    return {"result": result, "tokens": tokens, "payload": payload}


def _build_eval_env() -> Dict[str, Any]:
    env: Dict[str, Any] = {"__builtins__": __builtins__}
    exec("from pydicate.lang.tupilang.pos import *", env)
    exec("from pydicate import Predicate", env)
    return env


def _diff_annotated(expected: str, actual: str) -> List[str]:
    expected_tokens = parse_annotated(expected)
    actual_tokens = parse_annotated(actual)
    diffs: List[str] = []
    if len(expected_tokens) != len(actual_tokens):
        diffs.append(
            f"token count differs: expected {len(expected_tokens)}, got {len(actual_tokens)}"
        )
    limit = min(len(expected_tokens), len(actual_tokens))
    for idx in range(limit):
        exp = expected_tokens[idx]
        act = actual_tokens[idx]
        if exp.m != act.m:
            diffs.append(
                f"token {idx + 1} morph differs: expected {exp.m!r}, got {act.m!r}"
            )
        exp_tags = set(exp.tags)
        act_tags = set(act.tags)
        missing = sorted(exp_tags - act_tags)
        extra = sorted(act_tags - exp_tags)
        if missing or extra:
            if missing:
                diffs.append(f"token {idx + 1} missing tags: {', '.join(missing)}")
            if extra:
                diffs.append(f"token {idx + 1} extra tags: {', '.join(extra)}")
    return diffs


def _strip_tags(text: str) -> str:
    return re.sub(r"\[[^\]]+\]", "", text)


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


_COLOR_RESET = "\x1b[0m"
_COLOR_DIM = "\x1b[2m"
_PALETTE = (
    "\x1b[36m",  # cyan
    "\x1b[33m",  # yellow
    "\x1b[35m",  # magenta
    "\x1b[32m",  # green
    "\x1b[34m",  # blue
    "\x1b[31m",  # red
)


def _colorize_annotated(text: str) -> str:
    try:
        tokens = parse_annotated(text)
    except Exception:
        return text
    parts: List[str] = []
    for idx, token in enumerate(tokens):
        color = _PALETTE[idx % len(_PALETTE)]
        surface = token.surface
        if not surface:
            tags = "".join(f"[{tag}]" for tag in token.tags if tag)
            surface = f"{token.m}{tags}"
        tagged = re.sub(
            r"(\[[^\]]+\])",
            lambda m: f"{_COLOR_DIM}{m.group(1)}{color}",
            surface,
        )
        parts.append(f"{color}{tagged}{_COLOR_RESET}")
    return " ".join(parts)


def _colorize_surface(text: str) -> str:
    parts = []
    for idx, part in enumerate(text.split()):
        color = _PALETTE[idx % len(_PALETTE)]
        parts.append(f"{color}{part}{_COLOR_RESET}")
    return " ".join(parts)


_PROGRESS_PATH = os.path.expanduser("~/.pydicate_compiler_progress.json")


def _load_progress() -> Dict[str, Any]:
    try:
        with open(_PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _save_progress(data: Dict[str, Any]) -> None:
    tmp = f"{_PROGRESS_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, _PROGRESS_PATH)


def _entry_text(entry: Dict[str, Any]) -> str:
    return entry.get("anotated") or entry.get("annotated") or ""


def _entry_label(entry: Dict[str, Any]) -> str:
    return entry.get("label") or ""


def _entry_index(entry: Dict[str, Any], fallback: int) -> int:
    idx = entry.get("index")
    if isinstance(idx, int):
        return idx
    try:
        return int(idx)
    except Exception:
        return fallback


def _load_corpus(path: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entry["_line"] = raw_idx
            entries.append(entry)
    return entries


def _surface_match(expected: str, actual: str) -> bool:
    return _normalize_space(expected) == _normalize_space(actual)


def _find_entry_pos(entries: List[Dict[str, Any]], entry_idx: int) -> Optional[int]:
    for pos, entry in enumerate(entries):
        if _entry_index(entry, pos) == entry_idx:
            return pos
    return None


def _update_progress(
    data: Dict[str, Any],
    corpus_path: str,
    *,
    cursor_idx: int,
    statuses: Dict[str, str],
) -> None:
    data[corpus_path] = {
        "cursor": cursor_idx,
        "statuses": statuses,
        "updated": time.time(),
    }
    _save_progress(data)


def _run_regression_until_fail(
    entries: List[Dict[str, Any]],
    statuses: Dict[str, str],
    *,
    beam: int,
    allow_seq: bool,
    seq_op: str,
    rerank_k: int,
    rerank_weight: float,
    rewrite_variants: int,
    finalize_top_k: int,
    use_lexicon: bool,
    lexicon_modules: Optional[List[str]],
) -> Tuple[Optional[int], List[int]]:
    eval_env = _build_eval_env()
    rerank_fn = None
    if rerank_k > 0:

        def _rerank_eval(code: str) -> str:
            ast = eval(code, eval_env)
            if hasattr(ast, "eval"):
                return ast.eval(annotated=True)
            return str(ast)

        rerank_fn = _rerank_eval
    checked: List[int] = []
    seen_checked: set[int] = set()
    order = sorted(
        ((_entry_index(entry, pos), pos) for pos, entry in enumerate(entries)),
        key=lambda x: x[0],
    )
    for entry_idx, pos in order:
        entry = entries[pos]
        entry_id = str(entry_idx)
        status = statuses.get(entry_id)
        if status not in {"good", "done"}:
            continue
        payload = _entry_text(entry)
        if not payload:
            continue
        tokens = parse_annotated(payload)
        if not tokens:
            continue
        result = decompile(
            tokens,
            beam_size=beam,
            emit="pydicate",
            allow_seq=allow_seq,
            seq_op=seq_op,
            rerank_top_k=rerank_k,
            rerank_weight=rerank_weight,
            rerank_fn=rerank_fn,
            rewrite_max_variants=rewrite_variants,
            finalize_top_k=finalize_top_k,
            use_lexicon=use_lexicon,
            lexicon_modules=lexicon_modules,
        )
        try:
            ast = eval(result.code, eval_env)
            if hasattr(ast, "eval"):
                surface = ast.eval(annotated=False)
            else:
                surface = str(ast)
        except Exception:
            statuses[entry_id] = "bad"
            return entry_idx, checked
        label = _entry_label(entry)
        if label and not _surface_match(label, surface):
            statuses[entry_id] = "bad"
            return entry_idx, checked
        if entry_idx not in seen_checked:
            checked.append(entry_idx)
            seen_checked.add(entry_idx)
    return None, checked


def repl(
    *,
    mode: str = "annotated",
    emit: str = "pydicate",
    beam: int = 32,
    allow_seq: bool = True,
    seq_op: str = "+",
    rerank_k: int = 0,
    rerank_weight: float = 1.0,
    rewrite_variants: int = 4,
    finalize_top_k: int = 8,
    use_lexicon: bool = True,
    lexicon_modules: Optional[List[str]] = None,
    corpus_path: Optional[str] = None,
    color: str = "auto",
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
    last_payload: Optional[str] = None
    last_mode: Optional[str] = None
    last_code: Optional[str] = None
    last_result: Optional[Any] = None
    last_corpus_entry_idx: Optional[int] = None
    eval_env: Optional[Dict[str, Any]] = None
    color_enabled = _supports_color() if color == "auto" else color == "on"
    progress_data = _load_progress()
    corpus_entries: Optional[List[Dict[str, Any]]] = None
    corpus_abs: Optional[str] = None
    corpus_statuses: Dict[str, str] = {}
    corpus_pos = 0

    if corpus_path:
        corpus_abs = os.path.abspath(corpus_path)
        if not os.path.exists(corpus_abs):
            print(f"error: corpus file not found: {corpus_abs}")
            corpus_abs = None
        else:
            corpus_entries = _load_corpus(corpus_abs)
            state = (
                progress_data.get(corpus_abs, {})
                if isinstance(progress_data, dict)
                else {}
            )
            if isinstance(state, dict):
                corpus_statuses = dict(state.get("statuses", {}) or {})
                saved_cursor = state.get("cursor")
                if isinstance(saved_cursor, int):
                    pos = _find_entry_pos(corpus_entries, saved_cursor)
                    if pos is not None:
                        corpus_pos = pos
            if corpus_entries:
                fail_idx, checked = _run_regression_until_fail(
                    corpus_entries,
                    corpus_statuses,
                    beam=beam,
                    allow_seq=allow_seq,
                    seq_op=seq_op,
                    rerank_k=rerank_k,
                    rerank_weight=rerank_weight,
                    rewrite_variants=rewrite_variants,
                    finalize_top_k=finalize_top_k,
                    use_lexicon=use_lexicon,
                    lexicon_modules=lexicon_modules,
                )
                if checked:
                    if len(checked) <= 20:
                        checked_str = ", ".join(str(x) for x in checked)
                        print(f"regression: surface ok for indices: {checked_str}")
                    else:
                        print(
                            "regression: surface ok for "
                            f"{len(checked)} entries (first={checked[0]} last={checked[-1]})"
                        )
                if fail_idx is not None:
                    pos = _find_entry_pos(corpus_entries, fail_idx)
                    if pos is not None:
                        corpus_pos = pos
                        _update_progress(
                            progress_data,
                            corpus_abs,
                            cursor_idx=fail_idx,
                            statuses=corpus_statuses,
                        )
                    print(
                        f"regression: surface mismatch at index {fail_idx} (automarked bad)"
                    )
            if corpus_entries is not None:
                print(f"corpus loaded: {corpus_abs} ({len(corpus_entries)} entries)")
    try:

        def _advance_cursor(step: int) -> None:
            nonlocal corpus_pos
            if not corpus_entries:
                return
            corpus_pos = max(0, min(len(corpus_entries) - 1, corpus_pos + step))
            entry = corpus_entries[corpus_pos]
            entry_idx = _entry_index(entry, corpus_pos)
            _update_progress(
                progress_data,
                corpus_abs,
                cursor_idx=entry_idx,
                statuses=corpus_statuses,
            )
            status = corpus_statuses.get(str(entry_idx))
            print(f"cursor={entry_idx} status={status or '-'}")

        def _do_exec() -> Tuple[bool, bool]:
            nonlocal eval_env
            if not last_code:
                print("error: no previous output to exec")
                return False, False
            if emit != "pydicate":
                print("error: :exec requires emit=pydicate")
                return False, False
            if eval_env is None:
                eval_env = _build_eval_env()
            try:
                ast = eval(last_code, eval_env)
            except Exception as exc:
                print(f"error: failed to eval output: {exc}")
                return False, False
            if hasattr(ast, "eval"):
                surface = ast.eval(annotated=False)
                annotated = ast.eval(annotated=True)
            else:
                surface = str(ast)
                annotated = str(ast)
            print(surface)
            print(annotated)
            if color_enabled:
                print(_colorize_surface(surface))
                print(_colorize_annotated(annotated))
            surface_ok = False
            annotated_ok = False
            if last_mode == "annotated" and last_payload:
                expected_surface = _normalize_space(_strip_tags(last_payload))
                if corpus_entries and last_corpus_entry_idx is not None:
                    pos = _find_entry_pos(corpus_entries, last_corpus_entry_idx)
                    if pos is not None:
                        label = _entry_label(corpus_entries[pos])
                        if label:
                            expected_surface = _normalize_space(label)
                actual_surface = _normalize_space(surface)
                surface_ok = expected_surface == actual_surface
                if surface_ok:
                    print("surface match: yes")
                else:
                    print("surface match: no")
                    print(f"- expected: {expected_surface}")
                    print(f"- actual:   {actual_surface}")
                diffs = _diff_annotated(last_payload, annotated)
                annotated_ok = not diffs
                if annotated_ok:
                    print("annotated match: yes")
                else:
                    print("annotated match: no")
                    for diff in diffs:
                        print(f"- {diff}")
                if (
                    surface_ok
                    and annotated_ok
                    and corpus_entries
                    and last_corpus_entry_idx is not None
                ):
                    entry_id = str(last_corpus_entry_idx)
                    corpus_statuses[entry_id] = "good"
                    _update_progress(
                        progress_data,
                        corpus_abs,
                        cursor_idx=last_corpus_entry_idx,
                        statuses=corpus_statuses,
                    )
                    print(f"automarked good: index={last_corpus_entry_idx}")
            return surface_ok, annotated_ok

        while True:
            try:
                line = input("compiler> ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue

            if not line.startswith(":"):
                head = line.split()[0]
                if head in {
                    "help",
                    "quit",
                    "q",
                    "mode",
                    "emit",
                    "beam",
                    "seq",
                    "seqop",
                    "color",
                    "corpus",
                    "show",
                    "run",
                    "go",
                    "next",
                    "prev",
                    "goto",
                    "mark",
                    "registry",
                    "exec",
                }:
                    line = f":{line}"

            if line == "exec":
                line = ":exec"

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
                if cmd == "color" and args:
                    val = args[0].lower()
                    if val in {"on", "off"}:
                        color_enabled = val == "on"
                        print(f"color={val}")
                    else:
                        print("error: :color on|off")
                    continue
                if cmd in {
                    "corpus",
                    "show",
                    "run",
                    "go",
                    "next",
                    "prev",
                    "goto",
                    "mark",
                }:
                    if not corpus_entries:
                        print("error: no corpus loaded (use --corpus PATH)")
                        continue
                    entry = corpus_entries[corpus_pos]
                    entry_idx = _entry_index(entry, corpus_pos)
                    entry_id = str(entry_idx)
                    status = corpus_statuses.get(entry_id)

                    if cmd == "corpus":
                        total = len(corpus_entries)
                        counts: Dict[str, int] = {}
                        for st in corpus_statuses.values():
                            counts[st] = counts.get(st, 0) + 1
                        print(f"corpus={corpus_abs}")
                        print(f"entries={total} cursor={entry_idx}")
                        if counts:
                            for key in sorted(counts):
                                print(f"{key}={counts[key]}")
                        continue

                    if cmd == "show":
                        print(f"index={entry_idx} status={status or '-'}")
                        label = _entry_label(entry)
                        if label:
                            print(f"label: {label}")
                        annotated = _entry_text(entry)
                        if annotated:
                            if color_enabled:
                                print(_colorize_annotated(annotated))
                            else:
                                print(annotated)
                        continue

                    if cmd == "run":
                        payload = _entry_text(entry)
                        if not payload:
                            print("error: entry missing annotated text")
                            continue
                        try:
                            result_info = run_once(
                                payload,
                                mode="annotated",
                                emit=emit,
                                beam=beam,
                                allow_seq=allow_seq,
                                seq_op=seq_op,
                                rerank_k=rerank_k,
                                rerank_weight=rerank_weight,
                                rewrite_variants=rewrite_variants,
                                finalize_top_k=finalize_top_k,
                                use_lexicon=use_lexicon,
                                lexicon_modules=lexicon_modules,
                                color="on" if color_enabled else "off",
                            )
                            last_payload = result_info["payload"]
                            last_mode = "annotated"
                            last_result = result_info["result"]
                            last_code = last_result.code if last_result else None
                            last_corpus_entry_idx = entry_idx
                        except Exception as exc:
                            print(f"error: {exc}")
                        continue

                    if cmd == "go":
                        print(f"index={entry_idx} status={status or '-'}")
                        label = _entry_label(entry)
                        if label:
                            print(f"label: {label}")
                        annotated = _entry_text(entry)
                        if annotated:
                            if color_enabled:
                                print(_colorize_annotated(annotated))
                            else:
                                print(annotated)
                        payload = _entry_text(entry)
                        if not payload:
                            print("error: entry missing annotated text")
                            continue
                        try:
                            result_info = run_once(
                                payload,
                                mode="annotated",
                                emit=emit,
                                beam=beam,
                                allow_seq=allow_seq,
                                seq_op=seq_op,
                                rerank_k=rerank_k,
                                rerank_weight=rerank_weight,
                                rewrite_variants=rewrite_variants,
                                finalize_top_k=finalize_top_k,
                                use_lexicon=use_lexicon,
                                lexicon_modules=lexicon_modules,
                                color="on" if color_enabled else "off",
                            )
                            last_payload = result_info["payload"]
                            last_mode = "annotated"
                            last_result = result_info["result"]
                            last_code = last_result.code if last_result else None
                            last_corpus_entry_idx = entry_idx
                        except Exception as exc:
                            print(f"error: {exc}")
                            continue
                        surface_ok, annotated_ok = _do_exec()
                        if surface_ok and annotated_ok:
                            _advance_cursor(1)
                        continue

                    if cmd in {"next", "prev"}:
                        _advance_cursor(1 if cmd == "next" else -1)
                        continue

                    if cmd == "goto":
                        if not args:
                            print("error: :goto N")
                            continue
                        try:
                            target_idx = int(args[0])
                        except Exception:
                            print("error: :goto N")
                            continue
                        pos = _find_entry_pos(corpus_entries, target_idx)
                        if pos is None:
                            print(f"error: index not found: {target_idx}")
                            continue
                        corpus_pos = pos
                        _update_progress(
                            progress_data,
                            corpus_abs,
                            cursor_idx=target_idx,
                            statuses=corpus_statuses,
                        )
                        status = corpus_statuses.get(str(target_idx))
                        print(f"cursor={target_idx} status={status or '-'}")
                        continue

                    if cmd == "mark":
                        if not args:
                            print("error: :mark good|done|bad|skip|clear")
                            continue
                        mark = args[0].lower()
                        if mark == "clear":
                            corpus_statuses.pop(entry_id, None)
                            status = "-"
                        elif mark in {"good", "done", "bad", "skip"}:
                            corpus_statuses[entry_id] = mark
                            status = mark
                        else:
                            print("error: :mark good|done|bad|skip|clear")
                            continue
                        _update_progress(
                            progress_data,
                            corpus_abs,
                            cursor_idx=entry_idx,
                            statuses=corpus_statuses,
                        )
                        print(f"marked index={entry_idx} status={status}")
                        if mark in {"good", "done"}:
                            _advance_cursor(1)
                        continue
                if cmd == "registry":
                    _print_registry()
                    continue
                if cmd == "exec":
                    _do_exec()
                    continue

                print("Unknown command. :help for options.")
                continue

            try:
                result_info = run_once(
                    line,
                    mode=mode,
                    emit=emit,
                    beam=beam,
                    allow_seq=allow_seq,
                    seq_op=seq_op,
                    rerank_k=rerank_k,
                    rerank_weight=rerank_weight,
                    rewrite_variants=rewrite_variants,
                    finalize_top_k=finalize_top_k,
                    use_lexicon=use_lexicon,
                    lexicon_modules=lexicon_modules,
                    color="on" if color_enabled else "off",
                )
                last_payload = result_info["payload"]
                last_mode = mode
                last_result = result_info["result"]
                last_code = last_result.code if last_result else None
                last_corpus_entry_idx = None
            except Exception as exc:
                print(f"error: {exc}")
    finally:
        if readline:
            try:
                readline.write_history_file(history_path)
            except Exception:
                pass
        if corpus_entries and corpus_abs:
            entry = corpus_entries[corpus_pos]
            entry_idx = _entry_index(entry, corpus_pos)
            _update_progress(
                progress_data,
                corpus_abs,
                cursor_idx=entry_idx,
                statuses=corpus_statuses,
            )


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
    parser.add_argument("--rerank-k", type=int, default=0)
    parser.add_argument("--rerank-weight", type=float, default=1.0)
    parser.add_argument("--rewrite-variants", type=int, default=4)
    parser.add_argument("--finalize-k", type=int, default=8)
    parser.add_argument("--no-lexicon", dest="use_lexicon", action="store_false")
    parser.add_argument(
        "--color",
        default="auto",
        choices=["auto", "on", "off"],
        help="ANSI color output in :exec (default: auto).",
    )
    parser.add_argument(
        "--lexicon-modules",
        default="",
        help="Comma-separated modules to load as lexicon (default: built-ins).",
    )
    parser.add_argument(
        "--corpus",
        default="",
        help="Path to JSONL corpus file for progress tracking.",
    )

    args = parser.parse_args(argv)

    if args.payload:
        lexicon_modules = (
            [m.strip() for m in args.lexicon_modules.split(",") if m.strip()]
            if args.lexicon_modules
            else None
        )
        run_once(
            args.payload,
            mode=args.mode,
            emit=args.emit,
            beam=args.beam,
            allow_seq=args.allow_seq,
            seq_op=args.seqop,
            rerank_k=args.rerank_k,
            rerank_weight=args.rerank_weight,
            rewrite_variants=args.rewrite_variants,
            finalize_top_k=args.finalize_k,
            use_lexicon=args.use_lexicon,
            lexicon_modules=lexicon_modules,
        )
    else:
        lexicon_modules = (
            [m.strip() for m in args.lexicon_modules.split(",") if m.strip()]
            if args.lexicon_modules
            else None
        )
        corpus_path = args.corpus.strip() or None
        repl(
            mode=args.mode,
            emit=args.emit,
            beam=args.beam,
            allow_seq=args.allow_seq,
            seq_op=args.seqop,
            rerank_k=args.rerank_k,
            rerank_weight=args.rerank_weight,
            rewrite_variants=args.rewrite_variants,
            finalize_top_k=args.finalize_k,
            use_lexicon=args.use_lexicon,
            lexicon_modules=lexicon_modules,
            corpus_path=corpus_path,
            color=args.color,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
