#!/usr/bin/env python3
"""Audit dictionary citations without changing dictionary data or rendering PDFs.

Run from anywhere: python scripts/data/source_inventory.py
Python's standard library and Node.js (to run the site's actual linkSources) suffice.
The gzip audit retains every parenthetical segment, including rejected candidates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "docs/dict-conjugated.json.gz"
BIBLIOGRAPHY = ROOT / "docs/primary_sources/DTAbib.txt"
LINKER = ROOT / "js/index.js"
OUTPUT = ROOT / "docs/primary_sources"


def normalized(text):
    text = text.replace("’", "'").replace("‘", "'")
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    ).lower()


def search_form(text):
    """Map accent-insensitive match offsets back to the untouched definition."""
    chunks, offsets = [], []
    for index, char in enumerate(text):
        chunk = normalized(char)
        chunks.append(chunk)
        offsets.extend([index] * len(chunk))
    offsets.append(len(text))
    return "".join(chunks), offsets


def read_dictionary(path):
    raw = path.read_bytes()
    payload = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
    data = json.loads(payload)
    return data, {
        "path": (
            path.relative_to(ROOT).as_posix()
            if path.is_relative_to(ROOT)
            else str(path)
        ),
        "entries": len(data),
        "encoding": "gzip" if raw[:2] == b"\x1f\x8b" else "JSON",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
    }


def read_bibliography():
    """Only line-initial labels introduce authors, never editorial parentheses."""
    lines = BIBLIOGRAPHY.read_text(encoding="utf-8").splitlines()
    records = []
    author = None
    for number, line in enumerate(lines, 1):
        match = re.match(r"^\(([^)]+)\)", line)
        if match:
            author = match[1]
        elif line.startswith("DENUNCIAÇÕES DE PERNAMBUCO"):
            author = "Denunciações de Pernambuco"
        if line.strip():
            records.append({"source": author, "line": number, "text": line.strip()})
    return records


# These are conservative work-family classifications, not newly researched editions.
# Bibliography line references are to DTAbib.txt and validated against the author.
# A selected line reports what Navarro's transcription says, not scan availability.
WORKS = {
    "ABN": [(r".*", "Anais da Biblioteca Nacional", [1])],
    "Anch.": [
        (r"^arte\b", "Arte", [2]),
        (r"^cartas\b", "Cartas", [3]),
        (r"^dial\w*\.?\s*(?:da\s*)?fe\b", "Diálogo da Fé", [4, 8]),
        (r"^poesias\b", "Poesias", [5]),
        (r"^doutr\w*\.?\s*crista\s*,?\s*ii\b", "Doutrina Cristã II", [7]),
        (r"^doutr\w*\.?\s*crista\s*,?\s*i\b", "Doutrina Cristã I", [6]),
        (r"^poemas\b", "Poemas", [9]),
        (r"^teatro\b", "Teatro", [10]),
    ],
    "Ar.": [(r"^cat\w*\.?", "Catecismo", [11, 12])],
    "Bettendorff": [
        (r"^compendio\b", "Compêndio", [14]),
        (r"^(?:\[\d+\]\s*,?\s*)?cron", "Crônica da Missão", [13]),
    ],
    "Brandão": [(r"^dialogos\b", "Diálogos", [15])],
    "Brasil Holandês": [(r".*", "Brasil Holandês", [16])],
    "Cadornega": [(r"^hist", "História Geral das Guerras Angolanas", [17])],
    "Calado": [(r"^o val[eo]roso", "O Valoroso Lucideno", [18])],
    "Camarões": [(r".*", "Cartas dos Camarões", [19])],
    "Carder": [(r"^the rel", "The relation of Peter Carder", [20])],
    "Cardim": [(r"^trat", "Tratados da Terra e Gente do Brasil", [21])],
    "Castilho": [(r"^nomes\b", "Os Nomes das Partes do Corpo Humano", [22])],
    "Col. Niedenthal": [
        (r"^brasil holandes", "Coleção Niedenthal / Brasil Holandês", [23, 24])
    ],
    "D'Abbeville": [(r"^histoire\b", "Histoire", [25])],
    "D'Evreux": [(r"^viagem\b", "Viagem", [26])],
    "Denunciações de Pernambuco": [(r".*", "Denunciações de Pernambuco", [27])],
    "DHA": [(r".*", "Documentos para a História do Açúcar", [28])],
    "Ferreira": [(r"^america abreviada", "América Abreviada", [29])],
    "Fig.": [
        (r"^arte\b", "Arte", [30]),
        (r"^missao do maranhao", "Missão do Maranhão", [31]),
    ],
    "Gândavo": [
        (r"^hist", "História da Província de Santa Cruz", [32]),
        (r"^trat", "Tratado da Província do Brasil", [33]),
    ],
    "Griebe": [
        (
            r"^(?:brasil holandes|naturalien)",
            "Naturalien-Buch / Brasil Holandês",
            [34, 35],
        )
    ],
    "Heriarte": [(r'^"?descr', "Descrição do Estado do Maranhão", [36])],
    "Knivet": [(r"^the adm", "The admirable adventures", [37])],
    "Laet": [(r"^(?:novus orbis|livro)", "Novus Orbis", [38])],
    "Leite": [
        (r"^hist", "História da Companhia de Jesus no Brasil", [39]),
        (r"^lu[iz]+s? figueira", "Luís Figueira", [40]),
        (r"^cartas", "Cartas dos Primeiros Jesuítas do Brasil", [41]),
        (r"^novas cartas", "Novas Cartas Jesuíticas", [42]),
    ],
    "Léry": [(r"^histoire\b", "Histoire", [43, 44])],
    "Libri Princ.": [(r".*", "Libri Principis", [45, 46])],
    "Lisboa": [(r"^hist", "História dos Animais e Árvores do Maranhão", [47])],
    "Marcgrave": [(r"^hist", "História Natural do Brasil", [48])],
    "Monteiro": [(r'^"?rel', "Relação da Província do Brasil", [49])],
    "Nieuhof": [
        (r"^ged", "Gedenkenweerdige Brasilianense Zee en Lant-Reize", [50]),
        (r"^mem", "Memorável Viagem Marítima e Terrestre ao Brasil", [51]),
    ],
    "Piso": [(r"^de med", "De Medicina Brasiliensis", [52])],
    "Rodrigues": [(r"^relacao", "A Missão dos Carijós / Relação", [53])],
    "Salvador": [(r"^hist", "História do Brasil", [54])],
    "Silveira": [(r"^rel", "Relação Sumária das Cousas do Maranhão", [55])],
    "Soares": [(r"^coisa", "Coisas Notáveis do Brasil", [56])],
    "Sotomaior": [(r"^jornada ao pacaja", "Jornada ao Pacajá", [57])],
    "Sousa": [(r"^trat", "Tratado Descritivo do Brasil", [58])],
    "Staden": [(r"^(?:viagem|d\.v\.b\.)", "Viagem ao Brasil", [59])],
    "Theat. Rer. Nat. Bras.": [(r".*", "Theatrum Rerum Naturalium Brasiliae", [60])],
    "Thevet": [
        (r"^cosm", "La Cosmographie Universelle", [61]),
        (r"^les sing", "Les Singularités de la France Antarctique", []),
    ],
    "Travaços": [(r"^declaracao", "Declaração do Brasil", [62])],
    "Valente": [(r"^cantigas", "Cantigas / Poemas Brasílicos", [63])],
    "Vasconcelos": [(r"^cronica", "Crônica da Companhia de Jesus", [64])],
    "Vieira": [(r"^cartas", "Cartas", [65])],
    "VLB": [(r".*", "Vocabulário na Língua Brasílica", [66])],
    "Wagener": [(r"^zoobiblion", "Zoobiblion", [67])],
}
ALIASES = {
    "Anch.": ["Anchieta", "José de Anchieta"],
    "Ar.": ["Araújo"],
    "Fig.": ["Figueira"],
    "Libri Princ.": ["Libri Principis"],
    "VLB": ["VBL"],
    "Camarões": ["Cartas dos Camarões"],
    "Salvador": ["Frei Vicente do Salvador"],
    "Cardim": ["Pe. Fernão Cardim"],
    "Theat. Rer. Nat. Bras.": ["Thet. Rer. Nat. Bras.", "Theat. Rer. Nat., Bras."],
}


def author_pattern(author):
    patterns = []
    for alias in [author, *ALIASES.get(author, [])]:
        value = re.escape(normalized(alias))
        value = value.replace(r"\.", r"\.?")
        # re.escape spaces are '\ '; apostrophes are literal in Python regexes.
        value = value.replace("\\ ", r"\s*").replace("'", r"'\s*")
        patterns.append(value)
    return re.compile(r"(?<![\w])(?:" + "|".join(patterns) + r")(?![\w])")


def parenthetical_spans(text):
    """Keep all parenthetical spans, including nested and unclosed spans."""
    starts = []
    for index, char in enumerate(text):
        if char == "(":
            starts.append(index)
        elif char == ")" and starts:
            yield starts.pop(), index + 1, True
    for start in reversed(starts):
        yield start, len(text), False


LOCATOR = re.compile(
    r"(?:^|[,\s])(?:p{1,2}|fls?|fol|vol|livro|cap|prancha|versos?|v)\b\.?\s*(?=[\dIVXLCDM])"
    r"|(?<=,)\s*(?=\d|[IVXLCDM]+\b)|\s+(?=\d+(?:v\b|\b))",
    re.I,
)


def work_and_bibliography(author, tail):
    value = normalized(tail).lstrip(" ,.")
    for pattern, work, lines in WORKS[author]:
        if re.search(pattern, value):
            if author == "Ar." and work == "Catecismo":
                year = "1686" if re.search(r"\b1686\b", value) else "1618 (default)"
                return f"Catecismo {year}", [12] if year == "1686" else [11]
            if author == "Léry" and work == "Histoire":
                return (
                    ("Histoire 1580", [44])
                    if "1580" in value
                    else ("Histoire 1578 (default)", [43])
                )
            return work, lines
    label = LOCATOR.split(tail.strip(" ,."), maxsplit=1)[0].strip(" ,.")
    return "UNRESOLVED: " + (label or "work omitted"), []


def citation_candidate(raw):
    value = raw.strip()
    if re.search(r"\b(?:op\.\s*cit|apud|fonte\s*:|https?://|www\.)", value, re.I):
        return True
    if re.search(r"\b(?:p{1,2}|fls?|fol|vol|cap|versos?)\.\s*\d", value, re.I):
        return True
    return bool(
        re.search(r",\s*(?:\d|[IVXLCDM]+\b)|\[\d{4}\]", value)
        and re.search(r"[A-ZÀ-Ý]", value)
    )


def link_targets(strings):
    """Execute only the production linkSources function, never the browser app."""
    source = LINKER.read_text(encoding="utf-8")
    start = source.index("  function linkSources(definition) {")
    end = source.index("\n  function splitByBullet(", start)
    function = source[start:end].strip()
    program = r"""
const fs = require('fs');
const vm = require('vm');
const {source, strings} = JSON.parse(fs.readFileSync(0, 'utf8'));
const link = vm.runInNewContext('(' + source + ')', {}, {timeout: 1000});
process.stdout.write(JSON.stringify(strings.map(s => Array.from(link(s).matchAll(
  /<a\s[^>]*href="([^"]+)"[^>]*>/g), m => m[1]))));
"""
    result = subprocess.run(
        ["node", "-e", program],
        input=json.dumps({"source": function, "strings": strings}, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout), hashlib.sha256(function.encode()).hexdigest()


def inventory(data, bibliography):
    end = next(i for i, entry in enumerate(data) if entry["f"] == "BIBLIOGRAFIA")
    patterns = {author: author_pattern(author) for author in WORKS}
    records, outside = [], []
    for entry_index, entry in enumerate(data[:end]):
        definition = entry["d"]
        spans = list(parenthetical_spans(definition))
        for start, stop, balanced in sorted(spans):
            inside_start = start + 1
            inside_stop = stop - 1 if balanced else stop
            masked = list(definition[inside_start:inside_stop])
            # Nested citations belong to the inner group. Keep the outer raw text
            # for audit, but mask children to avoid counting their authors twice.
            for child_start, child_stop, _ in spans:
                if start < child_start and child_stop <= stop:
                    a, b = (
                        child_start - inside_start,
                        min(child_stop, inside_stop) - inside_start,
                    )
                    masked[a:b] = " " * (b - a)
            masked = "".join(masked)
            # A semicolon can separate two cited authors or an abbreviated repeat.
            previous = None
            for part in re.finditer(r"[^;]+", masked):
                raw_start, raw_stop = (
                    inside_start + part.start(),
                    inside_start + part.end(),
                )
                raw = definition[raw_start:raw_stop]
                value, offsets = search_form(part[0])
                hits = sorted(
                    (offsets[m.start()], -len(m[0]), author, offsets[m.end()], m[0])
                    for author, pattern in patterns.items()
                    for m in pattern.finditer(value)
                )
                record = {
                    "entry_index": entry_index,
                    "headword": entry["f"],
                    "start": raw_start,
                    "end": raw_stop,
                    "raw": raw,
                    "balanced_parentheses": balanced,
                }
                if hits:
                    position, _, author, author_end, _ = hits[0]
                    tail = raw[author_end:]
                    work, lines = work_and_bibliography(author, tail)
                    # Narrative mentions and names lacking bibliographic syntax are
                    # retained, but not automatically turned into valid citations.
                    prefix = normalized(part[0][:position]).strip()
                    syntax = not prefix or bool(
                        re.fullmatch(r"(?:in|apud|cf\.?|v\.?|s\.)", prefix)
                    )
                    abbreviated_without_comma = (
                        author in {"Anch.", "Ar.", "Fig."}
                        and raw[position:author_end].endswith(".")
                        and bool(lines)
                    )
                    if (
                        not re.match(r"\s*(?:,|\[|\.|$)", tail)
                        and not abbreviated_without_comma
                    ):
                        syntax = False
                    if author == "Fig." and re.fullmatch(
                        r"(?:s\.\s*)?fig\.?", raw.strip(), re.I
                    ):
                        syntax = False  # adjective 'figurative', not Figueira
                    record.update(
                        source=author,
                        work=work,
                        bibliography_lines=lines,
                        source_spelling=raw[position:author_end],
                        tail=tail.strip(" ,"),
                        classification=(
                            "catalogued" if syntax else "catalogue_name_in_prose"
                        ),
                        host_sources=sorted(
                            {hit[2] for hit in hits[1:] if hit[2] != author}
                        ),
                    )
                    if syntax:
                        previous = (author, work, lines)
                elif previous and re.fullmatch(
                    r"\s*(?:[IVXLCDM]+\s*,\s*)?\d+[\dv,\s–-]*\s*", raw
                ):
                    author, work, lines = previous
                    record.update(
                        source=author,
                        work=work,
                        bibliography_lines=lines,
                        source_spelling="",
                        tail=raw.strip(),
                        host_sources=[],
                        classification="inherited_same_parenthesis",
                    )
                else:
                    record["classification"] = (
                        "unmatched_candidate"
                        if citation_candidate(part[0])
                        else "other_parenthetical"
                    )
                records.append(record)
        normalized_definition, offsets = search_form(definition)
        for author, pattern in patterns.items():
            for match in pattern.finditer(normalized_definition):
                position, stop = offsets[match.start()], offsets[match.end()]
                if not any(a <= position < b for a, b, _ in spans):
                    outside.append(
                        {
                            "entry_index": entry_index,
                            "headword": entry["f"],
                            "source": author,
                            "start": position,
                            "end": stop,
                            "classification": "catalogue_name_outside_parentheses",
                            "context": definition[max(0, position - 50) : stop + 180],
                        }
                    )
    checked = [r for r in records if r["classification"] != "other_parenthetical"]
    targets, linker_hash = link_targets([r["raw"] for r in checked])
    for record, links in zip(checked, targets, strict=True):
        record["actual_link_targets"] = links
    groups = defaultdict(list)
    for record in records:
        if record["classification"] in {"catalogued", "inherited_same_parenthesis"}:
            groups[(record["source"], normalized(record["work"]))].append(record)
    work_summaries = []
    for (author, _), citations in groups.items():
        work = citations[0]["work"]
        work_summaries.append(
            {
                "source": author,
                "work": work,
                "explicit_occurrences": sum(
                    r["classification"] == "catalogued" for r in citations
                ),
                "inherited_occurrences": sum(
                    r["classification"] == "inherited_same_parenthesis"
                    for r in citations
                ),
                "entries": len({r["entry_index"] for r in citations}),
                "bibliography_lines": sorted(
                    {n for r in citations for n in r["bibliography_lines"]}
                ),
                "source_spellings": dict(
                    sorted(
                        Counter(
                            r["source_spelling"]
                            for r in citations
                            if r["source_spelling"]
                        ).items()
                    )
                ),
                "citations_producing_links": sum(
                    bool(r["actual_link_targets"]) for r in citations
                ),
                "viewer_books": sorted(
                    {
                        re.search(r"book_name=([^&]+)", url)[1]
                        for r in citations
                        for url in r["actual_link_targets"]
                        if "book_name=" in url
                    }
                ),
                "examples": list(dict.fromkeys(r["raw"].strip() for r in citations))[
                    :5
                ],
                "locator_tails": sorted({r["tail"] for r in citations}),
                "host_sources": sorted(
                    {host for r in citations for host in r["host_sources"]}
                ),
            }
        )
    work_summaries.sort(
        key=lambda row: (-row["explicit_occurrences"], row["source"], row["work"])
    )
    counts = Counter(record["classification"] for record in records)
    unknowns = defaultdict(list)
    for record in records:
        if record["classification"] == "unmatched_candidate" or (
            record["classification"] == "catalogue_name_in_prose"
            and citation_candidate(record["raw"])
        ):
            label = (
                LOCATOR.split(record["raw"].strip(), maxsplit=1)[0].strip(" ,.")
                or record["raw"].strip()
            )
            unknowns[label].append(record)
    unresolved = [
        {
            "label": label,
            "occurrences": len(rows),
            "examples": [
                {key: r[key] for key in ("entry_index", "headword", "raw")}
                for r in rows[:3]
            ],
        }
        for label, rows in sorted(
            unknowns.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]
    sources = []
    for author in sorted(WORKS):
        primary = [
            r
            for r in records
            if r.get("source") == author and r["classification"] == "catalogued"
        ]
        host = [r for r in records if author in r.get("host_sources", [])]
        prose = [
            r
            for r in records
            if r.get("source") == author
            and r["classification"] == "catalogue_name_in_prose"
        ]
        sources.append(
            {
                "source": author,
                "explicit_primary_occurrences": len(primary),
                "secondary_name_mentions": len(host),
                "prose_or_source_credit_mentions": len(prose),
                "bibliography_lines": [
                    r["line"] for r in bibliography if r["source"] == author
                ],
                "secondary_or_prose_examples": list(
                    dict.fromkeys(r["raw"].strip() for r in [*host, *prose])
                )[:5],
            }
        )
    return (
        records,
        outside,
        {
            "definition_entries_scanned": end,
            "bibliography_entry_start": end,
            "counting": dict(sorted(counts.items())),
            "linker_function_sha256": linker_hash,
            "works": work_summaries,
            "sources": sources,
            "unmatched_labels": unresolved,
            "catalogue_names_only_outside_parentheses": len(outside),
            "bibliography_sources_without_catalogued_citations": sorted(
                {r["source"] for r in bibliography}
                - {r["source"] for r in work_summaries}
            ),
        },
    )


DEVREUX = re.compile(
    r"D['’]\s*[EÉ]vreux\s*,\s*Viagem\s*,\s*(?:(?:p|pp)\.\s*)?(\d+(?:\s*[-–]\s*\d+)?)",
    re.I,
)


def devreux_citations(data, end):
    rows = []
    for index, entry in enumerate(data[:end]):
        for match in DEVREUX.finditer(entry["d"]):
            numbers = [int(n) for n in re.split(r"\s*[-–]\s*", match[1])]
            pages = list(range(numbers[0], numbers[-1] + 1))
            rows.append(
                {
                    "entry_index": index,
                    "headword": entry["f"],
                    "start": match.start(),
                    "end": match.end(),
                    "citation": match[0],
                    "printed_pages": pages,
                }
            )
    targets, _ = link_targets([r["citation"] for r in rows])
    for row, links in zip(rows, targets, strict=True):
        row["actual_link_targets"] = links
    return rows


def markdown_escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(summary):
    works = summary["works"]
    d = summary["devreux"]
    lines = [
        "# Primary-source citation inventory",
        "",
        "Generated by `python scripts/data/source_inventory.py`. This is a research queue and an audit of the dictionary's citation strings. It does not enable links or render scans.",
        "",
        "## Scope and reproducibility",
        "",
        f"The live dictionary requests `{summary['input']['path']}` from `js/index.js`. It contains {summary['input']['entries']:,} records; the first {summary['definition_entries_scanned']:,} precede the `BIBLIOGRAFIA` heading and are scanned here. The remaining records are bibliography, not lexical citations. Both `dict-conjugated.json` and `dict-conjugated.json.gz` are gzip files in this checkout; they are different datasets. This inventory uses the served `.json.gz` only.",
        "",
        f"Decompressed dictionary SHA-256: `{summary['input']['uncompressed_sha256']}`.",
        "",
        "`source_inventory.json` includes the exact 67 bibliography lines from `DTAbib.txt`, work-to-line references, all observed locator tails, spelling variants, unresolved labels, and all D'Evreux occurrences. `source_citation_audit.jsonl.gz` retains **every** nonempty segment of every parenthetical, even segments classified as grammar rather than citations, followed by catalogue-name mentions outside parentheses. Nested text remains visible in the outer raw audit record but is masked during classification, so inner citations are counted once. Entry indices and character offsets refer to the unchanged dictionary definition (`d`). This permits review of rejected candidates without rerunning a different heuristic.",
        "",
        "The extractor recognizes line-initial bibliography labels, plus the unlabelled *Denunciações de Pernambuco* entry. A semicolon starts a separate citation segment. A numeric continuation within the same parentheses can inherit its previous source; these continuations are counted separately from explicitly named citations. Authors cited as a host after `in` remain in `host_sources`; they are not double-counted as another primary citation. Author names occurring in prose remain unresolved. Work labels are conservative families; they are not a claim that all editions or page systems within a family are interchangeable. Completeness here means every parenthetical segment is retained: previously unknown sources mentioned only in unparenthesized prose still require review of the dictionary text.",
        "",
        "Link coverage runs the actual `linkSources()` function from `js/index.js` in Node. A citation producing an anchor means the current formatter matches some part of that string; it **does not certify that a scan exists, the edition is correct, or every locator was linked**. For example, a Valente citation may link its Araújo host, and some 1686 Araújo forms are caught by the older 1618 formatter. This pilot does not repair those other sources.",
        "",
        "## D'Evreux pilot",
        "",
        f"**{d['explicit_occurrences']} explicit Viagem citations in {d['entries']} dictionary records, covering {len(d['printed_pages'])} distinct printed pages.** The complete list is also available in `devreux_citations.csv`.",
        "",
        "Navarro's bibliography specifies **Viagem ao Norte do Brasil**, César Augusto Marques's Portuguese translation, **Rio de Janeiro, 1929**, collated with Ferdinand Denis's **1864** French edition (Leipzig / Paris, A. Franck). Page references must therefore be verified against the 1929 Portuguese pagination; 1613–1614 are the events covered by the book, not the edition of the cited pages.",
        "",
        "Printed pages: " + ", ".join(str(page) for page in d["printed_pages"]) + ".",
        "",
        "Two formatting variants need attention: `tiá!` has `D' Evreux, Viagem, 143`; `Marabá` has `D'Evreux, Viagem, pp. 142-143`. The `Caruaru` article additionally says `Yves D'Evreux, (op. cit., p. 157)`: the work is implicit, so it is retained as unresolved and is **not included in the 120 explicit Viagem citations**. The separate bibliography entry is also excluded.",
        "",
        "## Sources listed in Navarro's primary-source bibliography",
        "",
        "These are all 47 catalogue sources, including sources appearing only as hosts, image credits, or prose mentions. Secondary-name and prose counts are an audit aid, not verified citations: common words such as *leite*, *figueira* and *camarões* create false positives outside bibliographic syntax.",
        "",
        "| Source | Explicit primary citations | Secondary name mentions | Prose / credits | Bibliography lines |",
        "|---|---:|---:|---:|---|",
    ]
    for row in summary["sources"]:
        lines.append(
            "| "
            + " | ".join(
                markdown_escape(value)
                for value in [
                    row["source"],
                    row["explicit_primary_occurrences"],
                    row["secondary_name_mentions"],
                    row["prose_or_source_credit_mentions"],
                    ", ".join(map(str, row["bibliography_lines"])),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Work families found",
        "",
        "The edition column points to exact line numbers in `DTAbib.txt`, whose full text is included below. An empty match means the work/edition needs review. Counts preserve repeated occurrences within a single entry.",
        "",
        "| Source | Work family | Explicit | Inherited | Entries | Citations producing anchors / viewer books | Bibliography lines |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in works:
        coverage = str(row["citations_producing_links"])
        if row["viewer_books"]:
            coverage += " / " + ", ".join(row["viewer_books"])
        lines.append(
            "| "
            + " | ".join(
                markdown_escape(value)
                for value in [
                    row["source"],
                    row["work"],
                    row["explicit_occurrences"],
                    row["inherited_occurrences"],
                    row["entries"],
                    coverage,
                    ", ".join(map(str, row["bibliography_lines"])) or "unresolved",
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Edition and locator cautions",
        "",
        "- **Figueira:** Navarro lists the 1687 Lisbon *Arte*, in Julius Platzmann's 1878 Leipzig facsimile. The lone `1686, 64` citation is preserved verbatim but linked with a warning: authoritative catalogs identify 1687, no separate 1686 edition was found, and the exact *çoába* statement was collated on p. 64 of the selected text.",
        "- **Anchieta:** *Arte* uses the 1933 facsimile, *Poesias* the 1954 documentary edition, *Poemas* the 1997 Navarro edition, and *Teatro* the 1999 Navarro edition. Some dictionary strings add `2006`; retain this discrepancy until that edition is identified. *Doutrina Cristã* I and II are distinct 1993 volumes. The bibliography repeats *Diálogo da Fé* (1988).",
        "- **Araújo:** the unqualified *Cat.* family is provisionally the 1618 edition reproduced in 1952; citations explicitly mentioning 1686 are separated and refer to the 1898 facsimile of the second edition. Existing links can match the wrong edition when a year appears after the page. Valente's cantigas have explicit 1618 and 1686 host references; the bibliography entry identifies the 1686/1898 host, so check each host locator.",
        "- **Léry:** Navarro explicitly defaults to 1578 when no year is mentioned. References to 1580 belong to the second-edition text in the 1994 Lestringant edition. The current formatter can match a year as if it were a page; anchor counts alone are insufficient verification.",
        "- **Gândavo / Soares:** some numbers identify manuscript **lines**, not printed pages. **Lisboa** references manuscript **folios**; **Laet** includes books, chapters and sections; **Wagener** includes plates. Preserve these units before planning image filenames or offsets.",
        "- **Thevet:** *Les Singularités de la France Antarctique* is actually cited, but `DTAbib.txt` only supplies *La Cosmographie Universelle* (1575). It remains a separate work with unresolved edition metadata.",
        "- The compressed dictionary also has bibliographies for modern literature and for toponyms/anthroponyms after the main articles. Their citations are retained in the unresolved queue when no primary-source catalogue match is justified. Those queues include narrative mentions, source omissions, typos, website credits and occasional false positives; they are not an asserted clean count of additional books.",
        "",
        "## Unmatched citation candidates",
        "",
        "All heuristic candidate labels appear below, including false positives. Full occurrence records are in the gzip audit. This prevents the catalogue from silently limiting the project to sources already supported by the older extraction script.",
        "",
        "| Candidate label | Occurrences | Example headword | Example text |",
        "|---|---:|---|---|",
    ]
    for row in summary["unmatched_labels"]:
        example = row["examples"][0]
        lines.append(
            "| "
            + " | ".join(
                markdown_escape(value)
                for value in [
                    row["label"],
                    row["occurrences"],
                    example["headword"],
                    example["raw"],
                ]
            )
            + " |"
        )
    lines += [
        "",
        "Catalogue sources with no confidently classified primary citation: "
        + ", ".join(summary["bibliography_sources_without_catalogued_citations"])
        + ".",
        "",
        "## Navarro's primary-source bibliography (repository transcription)",
        "",
        "The following preserves the repository's wording, including inconsistencies. The integer is the original `DTAbib.txt` line number. Bibliography presence alone is not a copyright or digitization assessment.",
        "",
    ]
    for row in summary["bibliography"]:
        lines += [f"**{row['line']}. {row['source']}** — {row['text']}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    data, metadata = read_dictionary(args.input.resolve())
    bibliography = read_bibliography()
    by_line = {r["line"]: r for r in bibliography}
    for source, works in WORKS.items():
        for _, _, line_numbers in works:
            for line in line_numbers:
                if by_line[line]["source"] != source:
                    raise ValueError(
                        f"Bibliography changed: recheck {source}, line {line}"
                    )
    records, outside, result = inventory(data, bibliography)
    devreux = devreux_citations(data, result["definition_entries_scanned"])
    summary = {
        "schema_version": 1,
        "input": metadata,
        "alternate_input": read_dictionary(ROOT / "docs/dict-conjugated.json")[1],
        "bibliography_path": BIBLIOGRAPHY.relative_to(ROOT).as_posix(),
        "bibliography_sha256": hashlib.sha256(BIBLIOGRAPHY.read_bytes()).hexdigest(),
        "bibliography": bibliography,
        **result,
        "devreux": {
            "explicit_occurrences": len(devreux),
            "entries": len({r["entry_index"] for r in devreux}),
            "printed_pages": sorted({p for r in devreux for p in r["printed_pages"]}),
            "citations": devreux,
        },
    }
    # Offsets and exact strings make the audit independently recoverable.
    for record in records:
        if (
            data[record["entry_index"]]["d"][record["start"] : record["end"]]
            != record["raw"]
        ):
            raise ValueError("Audit offset does not recover the original citation")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "source_inventory.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "source_inventory.md").write_text(
        render_report(summary), encoding="utf-8"
    )
    audit = "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n"
        for r in [*records, *outside]
    )
    compressed_audit = bytearray(gzip.compress(audit.encode(), mtime=0))
    # Python and zlib releases disagree about the gzip OS header byte even
    # with a fixed mtime. Normalize it so regenerating the inventory is
    # byte-for-byte reproducible across supported development environments.
    compressed_audit[9] = 255
    (output / "source_citation_audit.jsonl.gz").write_bytes(compressed_audit)
    with (output / "devreux_citations.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "entry_index",
                "headword",
                "start",
                "end",
                "citation",
                "printed_pages",
                "actual_link_targets",
            ]
        )
        for row in devreux:
            writer.writerow(
                [
                    row["entry_index"],
                    row["headword"],
                    row["start"],
                    row["end"],
                    row["citation"],
                    ";".join(map(str, row["printed_pages"])),
                    ";".join(row["actual_link_targets"]),
                ]
            )
    print(
        json.dumps(
            {
                "work_families": len(result["works"]),
                "audit_records": len(records) + len(outside),
                "classification_counts": result["counting"],
                "unmatched_labels": len(result["unmatched_labels"]),
                "devreux_citations": len(devreux),
                "devreux_printed_pages": len(summary["devreux"]["printed_pages"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
