"""Directional Navarro -> Emerson spelling alignment, never morphological analysis.

Callers supply actual or explicitly hypothesized *surface forms*.  In particular,
``aî-``, ``a-`` and ``xe-`` are not learned as spelling insertions.  The weights
are retrieval costs, not estimated probabilities or assertions of equivalence.
All original text stays outside this module and remains untouched.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
import unicodedata


NAVARRO_SOURCE = "https://www.scielo.br/j/bgoeldi/a/vy7RnrNvd5B4rrCCX6vVx4d/?lang=pt"
EMERSON_SOURCE = "https://sites.google.com/site/vocabularionalinguabrasilica/"
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "ʻ": "'"})


def normalize_form(text):
    """Canonicalize case/apostrophe typography only; retain nasal/stress marks."""
    return unicodedata.normalize("NFC", str(text).casefold().translate(_APOSTROPHES)).strip()


def normalize_headword(text):
    """Exclusion key: keep phonological marks, omit terminal editorial punctuation.

    For example, the dictionary contains both ``marã`` and ``marã?``.  A held-out
    headword must also exclude this question-punctuation variant.  Apostrophes,
    internal hyphens and nasalization remain intact.
    """
    return normalize_form(text).rstrip("?!.,:;…").rstrip()


@lru_cache(maxsize=65536)
def _graphemes(text):
    clusters = []
    for char in unicodedata.normalize("NFD", text):
        if unicodedata.combining(char) and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return tuple(unicodedata.normalize("NFC", cluster) for cluster in clusters)


@lru_cache(maxsize=4096)
def _base_marks(grapheme):
    expanded = unicodedata.normalize("NFD", grapheme)
    return expanded[:1], frozenset(expanded[1:])


def prior_model():
    """Return a fresh, JSON-serializable set of documented retrieval hypotheses.

    Navarro (2022), paleographic criteria a/c/e/f/i, describes variable colonial
    spellings.  Exact VLB pilot examples support the more specific alternatives.
    They establish possible spellings, not a single canonical VLB orthography.
    """
    specs = [
        ("k", "c", .16, "velar-c", {"target_after_not_bases": "ei"}, "VLB Aiapigpigc and contextual c described by Navarro; exclude c before historical e/i"),
        ("k", "qu", .16, "velar-qu", {"target_after_bases": "ei"}, "VLB Aquîrara; qu before historical e/i, including accented i"),
        ("s", "ç", .16, "sibilant-cedilla", {}, "Navarro criterion f; VLB Xeputuçoc"),
        ("s", "c", .22, "sibilant-c", {"target_after_bases": "ei"}, "Navarro criterion f; VLB Aicuapigcigc before ig"),
        ("y", "ig", .18, "central-vowel-ig", {}, "Navarro criterion a; VLB Potyra/Potigra; ig is a unit, never global g deletion"),
        ("y", "i", .40, "central-vowel-i", {}, "Navarro criterion a; VLB moendypuk/Aimoendipuc"),
        ("y", "î", .40, "central-vowel-i-circumflex", {}, "VLB akyrara/Aquîrara; competing historical notation"),
        ("y", "j", .55, "central-vowel-j", {}, "Navarro criterion a, general colonial-document prior"),
        ("î", "i", .14, "palatal-glide-i", {}, "Navarro criterion e; VLB Aiacoc"),
        ("î", "j", .18, "palatal-glide-j", {}, "Navarro criterion e; VLB Aimojepotar"),
        ("î", "y", .22, "palatal-glide-y", {}, "Navarro criterion e; VLB Aimocanãy"),
        ("û", "u", .14, "labial-glide-u", {}, "Navarro criterion e; VLB Xeaguaçâ"),
        ("ŷ", "y", .18, "central-glide-y", {}, "Navarro criterion e, general colonial-document prior"),
        ("gûa", "goa", .30, "labialized-goa", {}, "VLB pokarugûar/Xepocarugoar; not global u/o interchange"),
        ("'", "", .40, "unwritten-glottal", {}, "Navarro criterion c; VLB eirapu'a/Eirapua"),
        ("-", "", .30, "editorial-hyphen", {}, "Editorial segmentation alternative, not a phonological deletion"),
        (" ", "", .35, "word-joining", {}, "Token-joining alternative; actual surface form must be supplied"),
    ]
    rules = [
        {"id": name, "from": old, "to": new, "cost": cost,
         "context": context, "origin": "prior", "description": description,
         "support": {"seed_count": 0, "distinct_headwords": 0, "distinct_pages": 0},
         "examples": []}
        for old, new, cost, name, context, description in specs
    ]
    return {
        "schema_version": 1,
        "direction": "Navarro modern surface -> Emerson historical surface",
        "weights_are_probabilities": False,
        "normalization": "NFC, casefold, apostrophe typography; diacritics retained",
        "default_costs": {"edit": 1.0, "stress_mark_difference": .26,
                          "nasal_mark_difference": .75},
        "rules": rules,
        "sources": [
            {"url": NAVARRO_SOURCE, "attribution": "Eduardo de Almeida Navarro (2022), DOI 10.1590/2178-2547-BGOELDI-2021-0034; Critérios para a transcrição paleográfica, a/c/e/f/i; general colonial priors"},
            {"url": EMERSON_SOURCE, "attribution": "Emerson José Silveira da Costa, VLB transcription; exact local pilot examples in rule descriptions; multiple spellings preserved"},
        ],
        "limitations": [
            "A spelling alignment is retrieval evidence, not lexical identity or reviewed citation coverage.",
            "Morphological prefixes, nominal -a and stem alternations require explicitly supplied surface forms.",
            "Nasalization is retained and penalized separately; no global g or final-a deletion is learned.",
        ],
    }


@dataclass(frozen=True)
class _Rule:
    rule_id: str
    source: tuple
    target: tuple
    cost: float
    origin: str
    context: dict


class OrthographyModel:
    """Compile once per frozen model; score pairs with a bounded per-model cache."""

    def __init__(self, model):
        self.model = model
        costs = model.get("default_costs", {})
        self.edit_cost = float(costs.get("edit", 1.0))
        self.stress_cost = float(costs.get("stress_mark_difference", .26))
        self.nasal_cost = float(costs.get("nasal_mark_difference", .75))
        self.rules_by_end = defaultdict(list)
        self.deletions = {}
        self.rules_by_id = {}
        for item in model.get("rules", []):
            src = _graphemes(normalize_form(item["from"]))
            # A literal space is a segmentation rule; normalize_form strips it.
            if item["from"] == " ":
                src = (" ",)
            dst = _graphemes(normalize_form(item["to"]))
            cost = float(item["cost"])
            if not src or cost < 0 or not math.isfinite(cost):
                raise ValueError("Rules require a nonempty source and finite nonnegative cost")
            rule = _Rule(item["id"], src, dst, cost, item.get("origin", "prior"), item.get("context", {}))
            self.rules_by_id[rule.rule_id] = rule
            if not dst:
                if len(src) != 1:
                    raise ValueError("Only explicit one-grapheme deletion priors are supported")
                previous = self.deletions.get(src[0])
                if previous is None or cost < previous.cost:
                    self.deletions[src[0]] = rule
            else:
                self.rules_by_end[(src[-1], dst[-1])].append(rule)
        self._cached_cost = lru_cache(maxsize=100000)(self._distance_uncached)

    def _substitution_cost(self, source, target):
        if source == target:
            return 0.0
        a, am = _base_marks(source)
        b, bm = _base_marks(target)
        if a == b:
            # Tilde presence is separate from stress.  It is never normalized away.
            if ("\u0303" in am) != ("\u0303" in bm):
                return self.nasal_cost
            return self.stress_cost
        return self.edit_cost

    @staticmethod
    def _context_matches(rule, source, target, i, j):
        """i/j are end positions after the candidate rule has consumed text."""
        context = rule.context
        after = context.get("target_after_bases")
        if after is not None and (j == len(target) or _base_marks(target[j])[0] not in after):
            return False
        forbidden_after = context.get("target_after_not_bases")
        if forbidden_after is not None and j < len(target) and _base_marks(target[j])[0] in forbidden_after:
            return False
        after = context.get("source_after_bases")
        if after is not None and (i == len(source) or _base_marks(source[i])[0] not in after):
            return False
        if context.get("source_end") and i != len(source):
            return False
        if context.get("target_end") and j != len(target):
            return False
        return True

    def _distance_uncached(self, source_text, target_text):
        return self._calculate(source_text, target_text, trace=False)[0]

    def _calculate(self, source_text, target_text, trace):
        source, target = _graphemes(source_text), _graphemes(target_text)
        n, m = len(source), len(target)
        grid = [[0.0] * (m + 1) for _ in range(n + 1)]
        back = [[None] * (m + 1) for _ in range(n + 1)] if trace else None
        for i in range(1, n + 1):
            rule = self.deletions.get(source[i - 1])
            delta = min(self.edit_cost, rule.cost) if rule else self.edit_cost
            grid[i][0] = grid[i - 1][0] + delta
            if trace:
                back[i][0] = (i - 1, 0, delta, rule.rule_id if rule and rule.cost <= self.edit_cost else None)
        for j in range(1, m + 1):
            grid[0][j] = grid[0][j - 1] + self.edit_cost
            if trace:
                back[0][j] = (0, j - 1, self.edit_cost, None)
        for i in range(1, n + 1):
            a = source[i - 1]
            deletion = self.deletions.get(a)
            deletion_cost = min(self.edit_cost, deletion.cost) if deletion else self.edit_cost
            deletion_id = deletion.rule_id if deletion and deletion.cost <= self.edit_cost else None
            row, previous = grid[i], grid[i - 1]
            for j in range(1, m + 1):
                b = target[j - 1]
                delta = self._substitution_cost(a, b)
                best = previous[j - 1] + delta
                predecessor = (i - 1, j - 1, delta, None)
                candidate = previous[j] + deletion_cost
                if candidate < best - 1e-12:
                    best, predecessor = candidate, (i - 1, j, deletion_cost, deletion_id)
                candidate = row[j - 1] + self.edit_cost
                if candidate < best - 1e-12:
                    best, predecessor = candidate, (i, j - 1, self.edit_cost, None)
                for rule in self.rules_by_end.get((a, b), ()):
                    si, tj = i - len(rule.source), j - len(rule.target)
                    if si < 0 or tj < 0:
                        continue
                    if source[si:i] != rule.source or target[tj:j] != rule.target:
                        continue
                    if not self._context_matches(rule, source, target, i, j):
                        continue
                    candidate = grid[si][tj] + rule.cost
                    if candidate < best - 1e-12:
                        best, predecessor = candidate, (si, tj, rule.cost, rule.rule_id)
                row[j] = best
                if trace:
                    back[i][j] = predecessor
        cost = grid[n][m]
        if not trace:
            return cost, None
        operations = []
        i, j = n, m
        while i or j:
            si, tj, delta, rule_id = back[i][j]
            modern, historical = "".join(source[si:i]), "".join(target[tj:j])
            kind = "rule" if rule_id else "match" if modern == historical else "insert" if not modern else "delete" if not historical else "substitute"
            operation = {"kind": kind, "modern": modern, "historical": historical,
                         "modern_start": si, "modern_end": i,
                         "historical_start": tj, "historical_end": j, "cost": round(delta, 8)}
            if rule_id:
                operation.update(rule_id=rule_id, origin=self.rules_by_id[rule_id].origin)
            operations.append(operation)
            i, j = si, tj
        operations.reverse()
        return cost, operations

    def score(self, modern_form, historical_form):
        source, target = normalize_form(modern_form), normalize_form(historical_form)
        if source == target:
            return 0.0
        denominator = max(len(_graphemes(source)), len(_graphemes(target)), 1)
        return min(1.0, self._cached_cost(source, target) / denominator)

    def align(self, modern_form, historical_form):
        source, target = normalize_form(modern_form), normalize_form(historical_form)
        cost, operations = self._calculate(source, target, trace=True)
        denominator = max(len(_graphemes(source)), len(_graphemes(target)), 1)
        normalized = min(1.0, cost / denominator)
        return {"modern_form": modern_form, "historical_form": historical_form,
                "normalized_modern": source, "normalized_historical": target,
                "cost": round(cost, 8), "normalized_cost": round(normalized, 8),
                "similarity": round(1.0 - normalized, 8),
                "score_is_probability": False, "operations": operations,
                "informative_operations": [op for op in operations if op["kind"] != "match"]}

    def cache_info(self):
        return self._cached_cost.cache_info()


_DEFAULT_MODEL = None


def compile_model(model=None):
    global _DEFAULT_MODEL
    if isinstance(model, OrthographyModel):
        return model
    if model is None:
        if _DEFAULT_MODEL is None:
            _DEFAULT_MODEL = OrthographyModel(prior_model())
        return _DEFAULT_MODEL
    return OrthographyModel(model)


def score(modern_form, historical_form, model=None):
    """Return normalized retrieval cost (lower is closer); compile a model once."""
    return compile_model(model).score(modern_form, historical_form)


def align(modern_form, historical_form, model=None):
    """Return auditable minimum-cost operations; offsets count NFC graphemes."""
    return compile_model(model).align(modern_form, historical_form)


def _exclusion_sets(exclusions):
    exclusions = exclusions or {}
    heads = set(exclusions.get("headwords", [])) | set(exclusions.get("holdout_headwords", []))
    pages = set(exclusions.get("page_ids", [])) | set(exclusions.get("excluded_pages", [])) | set(exclusions.get("holdout_page_ids", []))
    sources = set(exclusions.get("source_ids", [])) | set(exclusions.get("holdout_source_ids", []))
    for case in exclusions.get("selected", []):
        heads.add(case["headword"])
        pages.add(case["page_id"])
    return {normalize_headword(h) for h in heads}, pages, sources


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def train(seeds, exclusions=None, config=None):
    """Count frozen-prior alignments of caller-supplied silver or reviewed seeds.

    Exclusions are applied before alignment/counting.  Candidate rules require
    multiple independent headwords/pages, have nonempty sides, and are at most
    three graphemes long.  This is one pass: no self-training from ranked output.
    Repeated citations of the same headword/surface pair count once.
    """
    options = {"min_distinct_headwords": 3, "min_distinct_pages": 2,
               "max_rule_graphemes": 3, "max_seed_normalized_cost": .30,
               "max_examples_per_rule": 8}
    options.update(config or {})
    model = prior_model()
    frozen = compile_model(model)
    excluded_heads, excluded_pages, excluded_sources = _exclusion_sets(exclusions)
    counts = Counter()
    accepted = []
    seen = set()
    evidence = defaultdict(lambda: {"heads": set(), "pages": set(), "seeds": set(), "examples": []})
    source_support = defaultdict(set)

    def observe(pair, seed, operation):
        if not pair[0] or not pair[1] or pair[0] == pair[1]:
            return
        if max(len(_graphemes(pair[0])), len(_graphemes(pair[1]))) > options["max_rule_graphemes"]:
            return
        item = evidence[pair]
        item["heads"].add(normalize_headword(seed["headword"]))
        item["pages"].add(seed["page_id"])
        item["seeds"].add(seed["seed_id"])
        if len(item["examples"]) < options["max_examples_per_rule"] and all(example["seed_id"] != seed["seed_id"] for example in item["examples"]):
            item["examples"].append({key: seed.get(key) for key in ("seed_id", "citation_id", "page_id", "source_id", "headword", "modern_form", "vlb_form", "evidence_kind", "morphology")})

    seeds = sorted(list(seeds), key=lambda s: (s.get("seed_id", ""), s.get("citation_id", ""), s.get("modern_form", ""), s.get("vlb_form", "")))
    for seed in seeds:
        counts["input_seeds"] += 1
        if normalize_headword(seed["headword"]) in excluded_heads or seed["page_id"] in excluded_pages or seed.get("source_id") in excluded_sources:
            counts["excluded_seeds"] += 1
            continue
        signature = (normalize_headword(seed["headword"]), normalize_form(seed["modern_form"]), normalize_form(seed["vlb_form"]))
        if signature in seen:
            counts["duplicate_surface_pairs"] += 1
            continue
        seen.add(signature)
        result = frozen.align(seed["modern_form"], seed["vlb_form"])
        if result["normalized_cost"] > options["max_seed_normalized_cost"]:
            counts["high_cost_seeds_skipped"] += 1
            continue
        accepted.append(seed)
        counts["accepted_seeds"] += 1
        for op in result["operations"]:
            source_support[op["modern"]].add(signature[0])
            if op["kind"] != "match":
                observe((op["modern"], op["historical"]), seed, op)
        # Adjacent generic substitutions/edits can reveal one multigraph rule.
        # Empty-side runs never become rules, so prefixes/suffixes stay separate.
        run = []
        for op in result["operations"] + [{"kind": "match"}]:
            if op["kind"] in {"substitute", "insert", "delete"}:
                run.append(op)
            else:
                if len(run) > 1:
                    observe(("".join(x["modern"] for x in run), "".join(x["historical"] for x in run)), seed, run[0])
                run = []

    existing = defaultdict(list)
    for rule in model["rules"]:
        existing[(rule["from"], rule["to"])].append(rule)
    learned_candidates = []
    for pair, item in sorted(evidence.items()):
        support = {"seed_count": len(item["seeds"]), "distinct_headwords": len(item["heads"]), "distinct_pages": len(item["pages"])}
        examples = item["examples"]
        if pair in existing:
            for rule in existing[pair]:
                rule["support"], rule["examples"] = support, examples
            continue
        enough = support["distinct_headwords"] >= options["min_distinct_headwords"] and support["distinct_pages"] >= options["min_distinct_pages"]
        # Conservative shrinkage: observational support can lower a generic edit
        # only to 0.35, never to the cost of a documented prior or exact identity.
        cost = round(max(.35, .65 - .025 * min(support["distinct_headwords"], 12)), 6)
        # Accent-folded selection is weak evidence for loss of nasal information.
        # Keep any learned nasal change substantially costlier than stress or a
        # documented spelling correspondence, even when numerous seeds contain it.
        source_tildes = sum("\u0303" in _base_marks(g)[1] for g in _graphemes(pair[0]))
        target_tildes = sum("\u0303" in _base_marks(g)[1] for g in _graphemes(pair[1]))
        if source_tildes != target_tildes:
            cost = max(.65, cost)
        # A single-grapheme rule at or above the always-available fallback can
        # never win the strict minimum-cost transition.  Retain its observational
        # evidence, but do not count it as an executable improvement.  Removing
        # these inert transitions does not change any distance or winning trace.
        source_units, target_units = _graphemes(pair[0]), _graphemes(pair[1])
        fallback_cost = None
        if len(source_units) == len(target_units) == 1:
            fallback_cost = frozen._substitution_cost(source_units[0], target_units[0])
        effective = fallback_cost is None or cost < fallback_cost - 1e-12
        active = enough and effective
        candidate = {"id": "learned-" + _json_hash(pair)[:12], "from": pair[0], "to": pair[1],
                     "cost": cost, "origin": "learned_silver", "context": {},
                     "support": support, "source_headword_opportunities": len(source_support[pair[0]]),
                     "examples": examples, "supported": enough, "active": active,
                     "description": "Observed nonempty grapheme correspondence in selected silver seed alignments; uncalibrated retrieval weight"}
        if fallback_cost is not None:
            candidate["existing_single_grapheme_fallback_cost"] = fallback_cost
        if not active:
            candidate["inactivity_reason"] = "insufficient_independent_support" if not enough else "cost_does_not_improve_existing_fallback"
        learned_candidates.append(candidate)
        if active:
            model["rules"].append(candidate)
    model["training"] = {
        "method": "One pass over frozen-prior alignments; no evaluation labels or ranked output used",
        "config": options, "counts": dict(sorted(counts.items())),
        "accepted_seed_sha256": _json_hash(accepted),
        "excluded_headwords": sorted(excluded_heads), "excluded_page_ids": sorted(excluded_pages),
        "excluded_source_ids": sorted(excluded_sources),
        "exclusions_sha256": _json_hash({"headwords": sorted(excluded_heads), "page_ids": sorted(excluded_pages), "source_ids": sorted(excluded_sources)}),
        "active_learned_rule_count": sum(rule["active"] for rule in learned_candidates),
        "supported_learned_observation_count": sum(rule["supported"] for rule in learned_candidates),
        "effective_learned_rule_count": sum(rule["active"] for rule in learned_candidates),
        "supported_but_inert_observation_count": sum(rule["supported"] and not rule["active"] for rule in learned_candidates),
        "learned_candidates": learned_candidates,
        "selection_warning": "Seeds selected with existing spelling aliases and contextual agreement are silver, biased evidence; counts do not validate those aliases or dictionary coverage.",
    }
    return model
