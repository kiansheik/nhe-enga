#!/usr/bin/env python3
"""Capture a reproducible, long-entry-biased sample from the real dictionary UI.

The sampler reads the served compressed dictionary, selects records from its
longest percentile by a seeded SHA-256 ranking, and asks the production
JavaScript renderer to build each ``.entry`` in headless Chromium.  The JSON
output contains the source definition, rendered outer HTML (minus unrelated,
hidden conjugation controls), and a few structural warnings intended to guide
(not replace) qualitative review.

Example, from the repository root::

    .venv/bin/python scripts/qa/sample_dictionary_entries.py \
      --seed 20261025 --sample-size 24 --longest-percent 10 \
      --include 'ranhẽ#2' \
      --output /tmp/nhe-enga-entry-sample.json \
      --gallery /tmp/nhe-enga-entry-sample.html \
      --screenshots /tmp/nhe-enga-entry-screenshots

Playwright is an audit-only dependency.  Install it and its Chromium build with
``python -m pip install playwright`` and ``python -m playwright install chromium``
if they are not already available.
"""

from __future__ import annotations

import argparse
import functools
import gzip
import hashlib
import html
import http.server
import json
import math
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "docs/dict-conjugated.json.gz"
DEFAULT_OUTPUT = Path("/tmp/nhe-enga-entry-sample.json")
DEFAULT_GALLERY = Path("/tmp/nhe-enga-entry-sample.html")
APOSTROPHES_RE = re.compile("[\u2018\u2019\u201b\u02bb\u02bc\uff07]")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--seed", default="20261025")
    parser.add_argument("--sample-size", type=int, default=24)
    parser.add_argument(
        "--longest-percent",
        type=float,
        default=10.0,
        help="sample only from this longest percentage of Tupi-Portuguese entries",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="HEADWORD[#NUMBER]",
        help="include a sentinel entry in addition to the random sample",
    )
    parser.add_argument(
        "--include-index",
        action="append",
        default=[],
        type=int,
        metavar="SOURCE_INDEX",
        help="include an exact served-dictionary array index as a sentinel",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gallery", type=Path, default=DEFAULT_GALLERY)
    parser.add_argument(
        "--screenshots",
        type=Path,
        help="optional directory for one expanded PNG per sampled entry",
    )
    args = parser.parse_args()
    if args.sample_size < 1:
        parser.error("--sample-size must be at least 1")
    if not 0 < args.longest_percent <= 100:
        parser.error("--longest-percent must be greater than 0 and at most 100")
    return args


def normalize_apostrophes(value):
    return APOSTROPHES_RE.sub("'", value or "")


def read_dictionary(path):
    raw = path.read_bytes()
    payload = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
    records = json.loads(payload)
    lexical_end = next(
        (
            index
            for index, record in enumerate(records)
            if record.get("f") == "BIBLIOGRAFIA"
        ),
        len(records),
    )
    return records, {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entry_count": len(records),
        "lexical_entry_count": lexical_end,
        "renderer": {
            "path": "js/index.js",
            "sha256": hashlib.sha256((ROOT / "js/index.js").read_bytes()).hexdigest(),
        },
        "stylesheet": {
            "path": "styles.css",
            "sha256": hashlib.sha256((ROOT / "styles.css").read_bytes()).hexdigest(),
        },
    }


def record_key(record):
    return normalize_apostrophes(record.get("f", "")), str(record.get("o", ""))


def describe_record(record, source_index, reason):
    return {
        "source_index": source_index,
        "headword": normalize_apostrophes(record.get("f", "")),
        "optional_number": str(record.get("o", "")),
        "definition": normalize_apostrophes(record.get("d", "")),
        "definition_chars": len(record.get("d", "")),
        "selection_reason": reason,
        "raw_record": record,
    }


def include_record(records, spec):
    headword, marker, optional_number = spec.rpartition("#")
    if not marker:
        headword, optional_number = spec, None
    expected_headword = normalize_apostrophes(headword)
    matches = []
    for source_index, record in enumerate(records):
        actual_headword, actual_number = record_key(record)
        if actual_headword != expected_headword:
            continue
        if optional_number is not None and actual_number != optional_number:
            continue
        matches.append((source_index, record))
    if len(matches) != 1:
        suffix = f"#{optional_number}" if optional_number is not None else ""
        raise ValueError(
            f"--include {headword}{suffix!s} matched {len(matches)} records; "
            "supply a homonym number that identifies exactly one"
        )
    return matches[0]


def select_records(
    records, sample_size, longest_percent, seed, includes, include_indices
):
    lexical_end = next(
        (
            index
            for index, record in enumerate(records)
            if record.get("f") == "BIBLIOGRAFIA"
        ),
        len(records),
    )
    eligible = [
        (source_index, record)
        for source_index, record in enumerate(records[:lexical_end])
        if record.get("t") in (1, True) and record.get("f") and record.get("d")
    ]
    ordered_longest = sorted(
        eligible, key=lambda item: (-len(item[1].get("d", "")), item[0])
    )
    pool_size = min(
        len(ordered_longest),
        max(sample_size, math.ceil(len(ordered_longest) * longest_percent / 100)),
    )
    pool = ordered_longest[:pool_size]

    def sample_rank(item):
        source_index, record = item
        headword, optional_number = record_key(record)
        material = f"{seed}\0{source_index}\0{headword}\0{optional_number}".encode()
        return hashlib.sha256(material).digest()

    randomly_selected = sorted(pool, key=sample_rank)[:sample_size]
    selected = {
        source_index: describe_record(record, source_index, "long-entry sample")
        for source_index, record in randomly_selected
    }
    for spec in includes:
        source_index, record = include_record(records[:lexical_end], spec)
        if source_index in selected:
            selected[source_index]["selection_reason"] += "; explicit sentinel"
        else:
            selected[source_index] = describe_record(
                record, source_index, "explicit sentinel"
            )
    for source_index in include_indices:
        if not 0 <= source_index < lexical_end:
            raise ValueError(
                f"--include-index {source_index} is outside the lexical dictionary"
            )
        record = records[source_index]
        if (
            record.get("t") not in (1, True)
            or not record.get("f")
            or not record.get("d")
        ):
            raise ValueError(
                f"--include-index {source_index} is not a nonempty Tupi-Portuguese entry"
            )
        if source_index in selected:
            selected[source_index]["selection_reason"] += "; explicit sentinel"
        else:
            selected[source_index] = describe_record(
                record, source_index, "explicit sentinel"
            )

    sentinels = sorted(
        (item for item in selected.values() if "sentinel" in item["selection_reason"]),
        key=lambda item: item["source_index"],
    )
    sampled = sorted(
        (item for item in selected.values() if item not in sentinels),
        key=lambda item: (-item["definition_chars"], item["source_index"]),
    )
    return sentinels + sampled, {
        "eligible_entry_count": len(eligible),
        "long_pool_count": pool_size,
        "long_pool_min_definition_chars": (
            len(pool[-1][1].get("d", "")) if pool else None
        ),
    }


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    site_prefix = "/nhe-enga"

    def log_message(self, *_):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def translate_path(self, path):
        request_path = urlsplit(path).path
        if request_path == self.site_prefix:
            local_path = "/"
        elif request_path.startswith(f"{self.site_prefix}/"):
            local_path = request_path[len(self.site_prefix) :]
        else:
            local_path = "/__nhe_enga_not_found__"
        return super().translate_path(local_path)


PAGE_LAYOUT_JS = r"""
() => {
  const documentRect = node => {
    if (!node) return null;
    const rect = node.getBoundingClientRect();
    return {
      top: rect.top + window.scrollY,
      bottom: rect.bottom + window.scrollY,
    };
  };
  const credits = document.querySelector('.credits');
  const offlineLink = document.querySelector('#offline-link');
  return {
    viewport_height: window.innerHeight,
    document_height: document.documentElement.scrollHeight,
    main: documentRect(document.querySelector('main')),
    credits: documentRect(credits),
    offline_link: documentRect(offlineLink),
    credits_position: credits ? getComputedStyle(credits).position : '',
  };
}
"""


EXPANDED_ENTRY_LAYOUT_JS = r"""
entry => {
  const documentRect = node => {
    if (!node) return null;
    const rect = node.getBoundingClientRect();
    return {
      top: rect.top + window.scrollY,
      bottom: rect.bottom + window.scrollY,
    };
  };
  const credits = document.querySelector('.credits');
  return {
    viewport_height: window.innerHeight,
    document_height: document.documentElement.scrollHeight,
    entry: documentRect(entry),
    main: documentRect(document.querySelector('main')),
    credits: documentRect(credits),
    offline_link: documentRect(document.querySelector('#offline-link')),
    credits_position: credits ? getComputedStyle(credits).position : '',
  };
}
"""


ENTRY_SNAPSHOT_JS = r"""
entries => entries.map((entry, resultIndex) => {
  const preview = entry.querySelector(':scope > .preview');
  const capturedEntry = entry.cloneNode(true);
  const omittedConjugationContainers = capturedEntry.querySelectorAll('.options-container').length;
  capturedEntry.querySelectorAll('.options-container').forEach(node => node.remove());
  const capturedPreview = capturedEntry.querySelector(':scope > .preview');
  const headword = preview?.querySelector(':scope > a.search-link')?.textContent || '';
  const optionalNumber = preview?.querySelector(':scope > sup')?.textContent || '';
  const quoteBlocks = [...preview.querySelectorAll('.sense-quote')];
  const quoteLines = [...preview.querySelectorAll('.quote-tupi, .quote-pt')];
  const emptyQuoteLines = [...preview.querySelectorAll('.quote-tupi, .quote-pt')]
    .filter(node => !node.textContent.trim())
    .map(node => node.className);
  const quoteDirectText = quoteBlocks.flatMap((quote, quoteIndex) =>
    [...quote.childNodes]
      .filter(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim())
      .map(node => ({quote_index: quoteIndex, text: node.textContent.trim()}))
  );
  const unexpectedQuoteChildren = quoteBlocks.flatMap((quote, quoteIndex) =>
    [...quote.children]
      .filter(node => !node.matches('.quote-tupi, .quote-pt, .quote-citation, .dialogue-line'))
      .map(node => ({quote_index: quoteIndex, tag: node.tagName.toLowerCase(), class_name: node.className}))
  );
  const nestedBlockSelectors = [
    '.sense-section-title .sense-quote',
    '.sense-definition .sense-quote',
    '.quote-tupi .sense-section-title',
    '.quote-tupi .sense-definition',
    '.quote-pt .sense-section-title',
    '.quote-pt .sense-definition',
  ];
  const nestedBlocks = nestedBlockSelectors.filter(selector => preview.querySelector(selector));
  const quoteLinesWithWrongParent = quoteLines
    .filter(node => !node.parentElement?.classList.contains('sense-quote'))
    .map(node => ({tag: node.tagName.toLowerCase(), class_name: node.className, text: node.textContent.trim()}));
  const semanticQuotes = quoteBlocks.map((quote, quoteIndex) => ({
    quote_index: quoteIndex,
    tupi: [...quote.querySelectorAll(':scope > .quote-tupi')].map(node => node.textContent.trim()),
    portuguese: [...quote.querySelectorAll(':scope > .quote-pt')].map(node => node.textContent.trim()),
    dialogue_tupi: [...quote.querySelectorAll('.dialogue-tupi')].map(node => node.textContent.trim()),
    dialogue_portuguese: [...quote.querySelectorAll('.dialogue-pt')].map(node => node.textContent.trim()),
    direct_text: [...quote.childNodes]
      .filter(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim())
      .map(node => node.textContent.trim()),
  }));
  const flags = [];
  if (emptyQuoteLines.length) flags.push('empty quote line');
  if (quoteDirectText.length) flags.push('text directly inside quote block');
  if (unexpectedQuoteChildren.length) flags.push('unexpected child inside quote block');
  if (nestedBlocks.length) flags.push('invalid semantic nesting');
  if (quoteLinesWithWrongParent.length) flags.push('quote line outside quote block');
  return {
    result_index: resultIndex,
    headword,
    optional_number: optionalNumber,
    outer_html: capturedEntry.outerHTML,
    preview_html: capturedPreview?.innerHTML || '',
    omitted_conjugation_containers: omittedConjugationContainers,
    rendered_text: preview?.innerText || '',
    dimensions: {
      client_height: preview?.clientHeight || 0,
      scroll_height: preview?.scrollHeight || 0,
    },
    page_layout: {
      credits_position: document.querySelector('.credits')
        ? getComputedStyle(document.querySelector('.credits')).position
        : '',
    },
    diagnostics: {
      flags,
      sense_quote_count: quoteBlocks.length,
      empty_quote_lines: emptyQuoteLines,
      quote_direct_text: quoteDirectText,
      unexpected_quote_children: unexpectedQuoteChildren,
      nested_blocks: nestedBlocks,
      quote_lines_with_wrong_parent: quoteLinesWithWrongParent,
    },
    semantic_outline: {
      section_titles: [...preview.querySelectorAll('.sense-section-title')].map(node => node.textContent.trim()),
      definitions: [...preview.querySelectorAll('.sense-definition')].map(node => node.textContent.trim()),
      quotes: semanticQuotes,
    },
  };
})
"""


def safe_filename(item):
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", item["headword"]).strip("-")
    normalized = normalized or "entry"
    number = f"-{item['optional_number']}" if item["optional_number"] else ""
    return f"{item['source_index']:05d}-{normalized}{number}.png"


def capture_entries(selected, records, screenshots):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is required for rendered capture. Install it with "
            "`python -m pip install playwright` and install Chromium."
        ) from exc

    selected_indices = {item["source_index"] for item in selected}
    browser_records = [
        record
        for source_index, record in enumerate(records)
        if source_index in selected_indices
    ]
    compressed_subset = gzip.compress(
        json.dumps(browser_records, ensure_ascii=False, separators=(",", ":")).encode()
    )

    handler = functools.partial(QuietHandler, directory=ROOT)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/nhe-enga/"
    if screenshots:
        screenshots.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if os.environ.get("CHROMIUM_PATH"):
                launch["executable_path"] = os.environ["CHROMIUM_PATH"]
            browser = playwright.chromium.launch(**launch)
            context = browser.new_context(
                service_workers="block", viewport={"width": 1440, "height": 1000}
            )
            page = context.new_page()
            page.route(
                "**/docs/dict-conjugated.json.gz",
                lambda route: route.fulfill(
                    status=200,
                    body=compressed_subset,
                    content_type="application/gzip",
                ),
            )
            page.route(
                "https://www.googletagmanager.com/**", lambda route: route.abort()
            )
            page.route(
                "**/neologisms.csv",
                lambda route: route.fulfill(
                    status=200,
                    body="Verbete,Categoria Gramatical\n",
                    content_type="text/csv",
                ),
            )
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_function(
                "!document.querySelector('#searchButton').disabled", timeout=60_000
            )
            page.add_style_tag(
                content="*, *::before, *::after { transition: none !important; }"
            )
            initial_page_layout = page.evaluate(PAGE_LAYOUT_JS)

            captures = []
            for item in selected:
                page.locator("#searchInput").fill(item["headword"])
                page.locator("#searchButton").click()
                page.wait_for_function(
                    "document.querySelectorAll('#results > .entry').length > 0"
                )
                snapshots = page.locator("#results > .entry").evaluate_all(
                    ENTRY_SNAPSHOT_JS
                )
                matches = [
                    snapshot
                    for snapshot in snapshots
                    if normalize_apostrophes(snapshot["headword"]) == item["headword"]
                    and snapshot["optional_number"] == item["optional_number"]
                ]
                same_key_indices = sorted(
                    selected_item["source_index"]
                    for selected_item in selected
                    if (
                        selected_item["headword"],
                        selected_item["optional_number"],
                    )
                    == (item["headword"], item["optional_number"])
                )
                occurrence = same_key_indices.index(item["source_index"])
                if occurrence >= len(matches):
                    raise RuntimeError(
                        "Could not identify rendered entry "
                        f"{item['headword']}#{item['optional_number']} "
                        f"(source index {item['source_index']}); found {len(matches)} matches"
                    )
                snapshot = matches[occurrence]
                snapshot["query"] = item["headword"]
                snapshot["initial_page_layout"] = initial_page_layout

                locator = page.locator("#results > .entry").nth(
                    snapshot["result_index"]
                )
                preview = locator.locator(":scope > .preview")
                preview.evaluate("node => node.classList.add('expanded')")
                snapshot["expanded_page_layout"] = locator.evaluate(
                    EXPANDED_ENTRY_LAYOUT_JS
                )
                preview.evaluate("node => node.classList.remove('expanded')")
                captures.append(snapshot)

                if screenshots:
                    locator.locator(":scope > .preview").evaluate(
                        "preview => preview.classList.add('expanded')"
                    )
                    locator.screenshot(
                        path=str(screenshots / safe_filename(item)),
                        animations="disabled",
                    )

            context.close()
            browser.close()
            return captures
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def write_gallery(path, audit):
    styles = (ROOT / "styles.css").read_text(encoding="utf-8")
    cards = []
    for item in audit["entries"]:
        flags = item["rendered"]["diagnostics"]["flags"]
        flag_html = (
            ", ".join(html.escape(flag) for flag in flags)
            if flags
            else "no automatic structural warning"
        )
        cards.append(
            "\n".join(
                [
                    '<section class="audit-card">',
                    (
                        f"<h2>{html.escape(item['headword'])}"
                        f"<sup>{html.escape(item['optional_number'])}</sup></h2>"
                    ),
                    (
                        '<p class="audit-meta">'
                        f"source index {item['source_index']}; "
                        f"{item['definition_chars']} definition characters; "
                        f"{html.escape(item['selection_reason'])}; "
                        f"{flag_html}</p>"
                    ),
                    "<details><summary>Definição bruta</summary>",
                    f"<pre>{html.escape(item['definition'])}</pre>",
                    "</details>",
                    '<div class="results">',
                    item["rendered"]["outer_html"],
                    "</div>",
                    "</section>",
                ]
            )
        )
    document = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nhe'enga dictionary entry formatting audit</title>
<style>
{styles}
body {{ max-width: 1200px; margin: 24px auto; padding: 0 20px; }}
.audit-card {{ border-top: 3px solid #374151; margin: 32px 0; padding-top: 12px; }}
.audit-meta {{ color: #4b5563; font: 14px/1.4 sans-serif; }}
.audit-card pre {{ white-space: pre-wrap; }}
.audit-card .preview {{ max-height: none !important; overflow: visible !important; }}
.audit-card .show-more, .audit-card .options-container {{ display: none !important; }}
</style>
</head>
<body>
<h1>Nhe'enga dictionary entry formatting audit</h1>
<p>Seed {html.escape(str(audit['sampling']['seed']))}; long pool top
{audit['sampling']['longest_percent']:g}%.</p>
{''.join(cards)}
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def main():
    args = parse_args()
    records, source = read_dictionary(args.data.resolve())
    selected, pool = select_records(
        records,
        args.sample_size,
        args.longest_percent,
        args.seed,
        args.include,
        args.include_index,
    )
    captures = capture_entries(selected, records, args.screenshots)
    for item, rendered in zip(selected, captures, strict=True):
        item.pop("raw_record")
        item["rendered"] = rendered

    audit = {
        "schema": 1,
        "source": source,
        "sampling": {
            "seed": args.seed,
            "sample_size": args.sample_size,
            "explicit_includes": args.include,
            "explicit_include_indices": args.include_index,
            "longest_percent": args.longest_percent,
            **pool,
            "captured_entry_count": len(selected),
            "method": "SHA-256-ranked sample within the longest-entry pool",
            "viewport": {"width": 1440, "height": 1000},
        },
        "entries": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_gallery(args.gallery, audit)
    warning_count = sum(
        bool(item["rendered"]["diagnostics"]["flags"]) for item in selected
    )
    print(
        f"Captured {len(selected)} entries ({warning_count} with automatic structural warnings)."
    )
    print(f"JSON: {args.output}")
    print(f"Gallery: {args.gallery}")
    if args.screenshots:
        print(f"Screenshots: {args.screenshots}")


if __name__ == "__main__":
    main()
