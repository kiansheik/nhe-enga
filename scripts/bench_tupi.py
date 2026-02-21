#!/usr/bin/env python3
import argparse
import gc
import sys
import tracemalloc
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tupi"))

from tupi import Noun, Verb  # noqa: E402


def format_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def bench(label, fn):
    gc.collect()
    tracemalloc.start()
    t0 = perf_counter()
    result = fn()
    dt = perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return label, dt, peak, result


def bench_verb_instantiate(n):
    def run():
        verbs = [Verb("katu", "v.tr. (r, s)", "test") for _ in range(n)]
        return verbs[-1].verbete

    return bench(f"verb_instantiate n={n}", run)


def bench_noun_instantiate(n):
    def run():
        nouns = [Noun("katu", "v.tr. (r, s)") for _ in range(n)]
        return nouns[-1].verbete()

    return bench(f"noun_instantiate n={n}", run)


def bench_noun_chain(n):
    def run():
        out = None
        for _ in range(n):
            n1 = Noun("katu", "v.tr. (r, s)")
            out = n1.possessive("1ps").sara().puer().ram().substantivo()
        return out

    return bench(f"noun_chain n={n}", run)


def bench_verb_conjugate(ops):
    def run():
        v = Verb("katu", "v.tr. (r, s)", "test")
        pairs = [
            ("1ps", "3p"),
            ("2ps", "3p"),
            ("3p", "1ps"),
            ("3p", "2ps"),
            ("1ppi", "3p"),
        ]
        out = None
        for i in range(ops):
            subj, obj = pairs[i % len(pairs)]
            out = v.conjugate(
                subject_tense=subj,
                object_tense=obj,
                mode="indicativo",
                pos="anteposto",
                anotar=False,
            )
        return out

    return bench(f"verb_conjugate ops={ops}", run)


def bench_irregular_lookup(n):
    def run():
        v = None
        for _ in range(n):
            v = Verb("'u", "v.tr.", "test", vid=10660)
        return v.verbete

    return bench(f"irregular_lookup n={n}", run)


def main():
    parser = argparse.ArgumentParser(description="Tupi performance benchmark")
    parser.add_argument("--n", type=int, default=2000, help="items per test")
    parser.add_argument("--ops", type=int, default=20000, help="verb ops")
    parser.add_argument(
        "--irregular",
        action="store_true",
        help="include irregular verb lookup test",
    )
    args = parser.parse_args()

    results = [
        bench_verb_instantiate(args.n),
        bench_noun_instantiate(args.n),
        bench_noun_chain(args.n),
        bench_verb_conjugate(args.ops),
    ]
    if args.irregular:
        results.append(bench_irregular_lookup(args.n))

    print("Tupi benchmarks")
    for label, dt, peak, _ in results:
        print(f"- {label}: {dt:.3f}s, peak {format_bytes(peak)}")


if __name__ == "__main__":
    main()
