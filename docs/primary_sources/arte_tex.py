#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse Anchieta grammar HTML and export a JSON representation, preserving inline HTML.

Changes from previous version:
- Lines in chapter content now keep original HTML (e.g., <i>, <b>, <span>).
- Chapter detection runs on a text-only version of the same line.

Usage:
    python parse_anchieta_html.py /path/to/emerson_arte_anchieta.html [-o output.json]

Requires:
    pip install beautifulsoup4 lxml
"""
import argparse
import json
import os
import re
from bs4 import BeautifulSoup

CHAPTER_REGEX = re.compile(r"\bCap\.\s*([IVXLCDM]+)\b", re.IGNORECASE)


def normalize_ws(s: str) -> str:
    import re as _re

    return _re.sub(r"\s+", " ", s.strip())


def roman_to_int(roman: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in roman.upper()[::-1]:
        v = vals.get(ch, 0)
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    return total


def html_to_text(html_fragment: str) -> str:
    """Turn a small HTML fragment into plain text (no tags), preserving visible chars/newlines."""
    # Use a lightweight soup parse of the fragment
    frag_soup = BeautifulSoup(html_fragment, "lxml")
    # Keep newlines as-is; normalize only multiple spaces
    txt = frag_soup.get_text()
    return txt


def extract_metadata(soup: BeautifulSoup, html_path: str) -> dict:
    meta = {}
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        meta["language"] = html_tag["lang"]

    head_title = soup.title.get_text(strip=True) if soup.title else None
    h1 = soup.select_one("#apresentacao h1")
    body_title = h1.get_text(strip=True) if h1 else None
    titles = [t for t in [head_title, body_title] if t]
    meta["title"] = titles[0] if titles else os.path.basename(html_path)
    if len(set(titles)) > 1:
        meta["alt_titles"] = list(dict.fromkeys(titles[1:]))

    apresentacao = soup.select_one("#apresentacao")
    if apresentacao:
        italics = [normalize_ws(i.get_text()) for i in apresentacao.find_all("i")]
        author = None
        for itm in italics:
            if "Anchieta" in itm or "José" in itm or "Ioſeph" in itm or "Ioseph" in itm:
                author = itm
                break
        if author:
            meta["author"] = author

        pres_text = apresentacao.get_text(" ", strip=True)
        import re as _re

        years = _re.findall(
            r"\b(1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b",
            " ".join([head_title or "", body_title or "", pres_text]),
        )
        if years:
            yr_159x = [y for y in years if y.startswith("15")]
            meta["year"] = int(yr_159x[0]) if yr_159x else int(years[-1])

    digitalizacao = None
    for h2 in soup.find_all("h2"):
        if h2.get("id", "").lower().startswith("digital"):
            digitalizacao = h2.parent
            break
    if digitalizacao:
        text = digitalizacao.get_text(" ", strip=True)
        import re as _re

        m = _re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if m:
            meta["digitization_date"] = m.group(1)
        a = digitalizacao.find("a")
        if a:
            meta["digitized_by"] = normalize_ws(a.get_text())
            href = a.get("href")
            if href:
                meta["digitizer_url"] = href

    meta["rights_note"] = "Rights/license not stated in source HTML."
    meta["source_file"] = os.path.basename(html_path)
    return meta


def iter_pre_blocks(soup: BeautifulSoup):
    """Yield (pre_id, html_string) for each <pre> under #texto_original, preserving inline HTML."""
    article = soup.select_one("#texto_original")
    if not article:
        return
    for pre in article.find_all("pre"):
        pid = pre.get("id") or ""
        # Keep the exact inner HTML of the <pre> (tags + text)
        inner_html = pre.decode_contents()
        # Normalize line endings for splitting
        inner_html = inner_html.replace("\r\n", "\n").replace("\r", "\n")
        yield pid, inner_html


def detect_chapter_header(line_html: str) -> tuple[bool, dict]:
    """
    Detect chapters from a line (HTML fragment). We strip tags for detection only.
    Returns (is_header, info_dict with roman, number, title_text).
    """
    text_line = html_to_text(line_html)
    m = CHAPTER_REGEX.search(text_line)
    if not m:
        return False, {}
    roman = m.group(1)
    title_text = normalize_ws(text_line)
    info = {"roman": roman, "number": roman_to_int(roman), "title": title_text}
    return True, info


def split_html_lines(pre_inner_html: str):
    """
    Split the inner HTML of a <pre> into per-line HTML fragments.
    We split on literal newlines which are preserved inside <pre>.
    """
    # Use simple splitlines; keepends=False so lines don't include trailing '\n'
    return pre_inner_html.split("\n")


def parse_content_to_chapters(soup: BeautifulSoup) -> list:
    chapters = []
    current = None

    for pid, pre_html in iter_pre_blocks(soup):
        for raw_line_html in split_html_lines(pre_html):
            # Remove only trailing carriage returns; keep leading spaces and inline HTML intact
            line_html = raw_line_html.rstrip("\r")
            if not line_html.strip():
                continue  # skip blank (HTML-empty) lines

            is_hdr, info = detect_chapter_header(line_html)
            if is_hdr:
                current = {
                    "chapter_number_roman": info["roman"],
                    "chapter_number": info["number"],
                    "chapter_title": info["title"],  # plain-text title
                    "lines": [],  # will contain HTML strings
                }
                chapters.append(current)
                continue

            if current is None:
                current = {
                    "chapter_number_roman": None,
                    "chapter_number": None,
                    "chapter_title": "Front matter",
                    "lines": [],
                }
                chapters.append(current)

            # Append the HTML line exactly as it appears inside <pre>
            current["lines"].append(line_html)

    return chapters


def list_unique_tags(content) -> set[str]:
    """
    Accepts either a list of HTML line strings OR
    the list of chapter dicts (with 'lines' keys).
    Returns a set of unique tag names.
    """
    tags = set()

    # If content looks like chapters
    if content and isinstance(content[0], dict) and "lines" in content[0]:
        lines = [line for chap in content for line in chap["lines"]]
    else:
        lines = content

    for line in lines:
        soup = BeautifulSoup(line, "lxml")
        for tag in soup.find_all(True):
            tags.add(tag.name)
    return tags


def content_to_latex(content):
    r"""
    Convert parsed content (list of chapters with 'chapter_number', 'chapter_title', 'lines')
    into LaTeX strings of the form:

    \chapter{Title}
    \section*{Texto original e tradução moderna}
    \begin{OriginalVsModern}
      \pair{\textbf{[n]} LINE}{\textit{[[INTERPRETAÇÃO AQUI]]}}
    \end{OriginalVsModern}
    """
    lines_out = []

    for chap in content:
        chap_num = chap.get("chapter_number")
        chap_title = chap.get(
            "chapter_title", f"Capítulo {chap_num}" if chap_num else "Front matter"
        )
        lines_out.append(f"\\chapter{{{chap_title}}}")
        lines_out.append("\\section*{Texto original e tradução moderna}")
        lines_out.append("\\begin{OriginalVsModern}")

        for i, line in enumerate(chap["lines"], start=1):
            # escape curly braces for LaTeX safety
            safe_line = line.replace("{", "\\{").replace("}", "\\}")
            pair = f"  \\pair{{\\textbf{{[{i}]}} {safe_line}}}{{\\textit{{[[INTERPRETAÇÃO AQUI]]}}}}"
            lines_out.append(pair)

        lines_out.append("\\end{OriginalVsModern}")
        lines_out.append("")  # blank line between chapters

    return "\n".join(lines_out)


def main():
    ap = argparse.ArgumentParser(
        description="Convert Anchieta HTML to structured JSON (preserving inline HTML)."
    )
    ap.add_argument("input_html", help="Path to emerson_arte_anchieta.html")
    ap.add_argument(
        "-o", "--output", help="Path to write JSON (default: alongside input, .json)"
    )
    args = ap.parse_args()

    with open(args.input_html, "rb") as f:
        soup = BeautifulSoup(f, "lxml")

    data = {
        "metadata": extract_metadata(soup, args.input_html),
        "content": parse_content_to_chapters(soup),
    }

    out_path = args.output
    if not out_path:
        base, _ = os.path.splitext(args.input_html)
        out_path = base + ".json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Print to stdout as well
    # print(json.dumps(data, ensure_ascii=False, indent=2))
    # now print with list_unique_tags all tags in dataset
    unique_tags = list_unique_tags(data["content"])
    # print("Unique tags found:", unique_tags)
    print(content_to_latex(data["content"]))


if __name__ == "__main__":
    main()
