#!/usr/bin/env python3
"""Build one searchable HTML snapshot of Figueira's 1628 Wikisource text.

The Wikisource print page transcludes all 198 scan leaves. This script keeps
that rendered transcription and its TemplateStyles intact, embeds every image,
records the current revision of each leaf, and adds local folio navigation.

Network access is required only while regenerating the checked-in snapshot.
"""

from __future__ import annotations

import argparse
import base64
from datetime import date
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import ssl
import tempfile
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
API_URL = "https://pt.wikisource.org/w/api.php"
WIKISOURCE_ORIGIN = "https://pt.wikisource.org"
PRINT_PAGE = "Anexo:Imprimir/Arte da Lingua Brasilica"
WORK_URL = "https://pt.wikisource.org/wiki/Arte_da_Lingua_Brasilica"
PRINT_URL = "https://pt.wikisource.org/wiki/Anexo:Imprimir/Arte_da_Lingua_Brasilica"
DEFAULT_OUTPUT = ROOT / "docs/primary_sources/figueira_arte_1628.html"
DEFAULT_METADATA = ROOT / "docs/primary_sources/figueira_arte_1628.json"
EXPECTED_LEAF_PAGES = 198
EXPECTED_PAGE_MARKERS = 189
USER_AGENT = "nhe-enga-source-preservation/1.0 (+https://github.com/kiansheik/nhe-enga)"


PAGE_CSS = r"""
:root {
    color-scheme: light;
    font-family: Georgia, "Times New Roman", serif;
    background: #f4f1e8;
    color: #241f18;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    line-height: 1.55;
}
a { color: #5b3218; }
a:focus-visible { outline: 3px solid #b56b2a; outline-offset: 3px; }
.source-header,
.page-index,
.source-text {
    width: min(100% - 2rem, 62rem);
    margin-inline: auto;
}
.source-header {
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid #b9aa91;
}
.source-header h1 {
    margin: 0;
    font-size: clamp(2rem, 7vw, 4.5rem);
    line-height: 0.95;
    letter-spacing: 0.025em;
    text-align: center;
}
.source-header .byline {
    margin: 0.8rem 0 1.5rem;
    text-align: center;
    font-size: 1.15rem;
}
.source-note {
    padding: 0.85rem 1rem;
    border-left: 4px solid #8b5a2b;
    background: #fffaf0;
}
.source-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem 1.1rem;
    margin-bottom: 0;
}
.page-index {
    padding: 1rem 0;
}
.page-index summary {
    cursor: pointer;
    font-weight: 700;
}
.page-links {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.75rem;
}
.page-links a {
    min-width: 2.6rem;
    padding: 0.2rem 0.45rem;
    border: 1px solid #cbbda6;
    border-radius: 0.25rem;
    background: #fffdf8;
    text-align: center;
    text-decoration: none;
    font: 0.82rem/1.3 system-ui, sans-serif;
}
.source-text {
    margin-bottom: 5rem;
    padding: 2.25rem clamp(1rem, 4vw, 3rem) 4rem;
    background: #fffdf8;
    box-shadow: 0 0.2rem 1.4rem rgb(65 48 31 / 12%);
    overflow-x: auto;
    overflow-wrap: break-word;
}
.source-text img {
    max-width: 100%;
    height: auto;
}
.source-text .poem p { margin: 0; }
.source-text table { max-width: 100%; }
.source-text table.multicol td { vertical-align: top; }
.source-text .ws-noexport,
.source-text .noprint { display: none !important; }
.source-text .ws-pagenum {
    position: relative;
    display: block;
    clear: both;
    height: 1px;
    margin: 3.25rem 0 2.25rem;
    border-top: 1px solid #cbbda6;
}
.source-text .ws-pagenum::after {
    content: attr(id);
    position: absolute;
    top: -0.95rem;
    left: 50%;
    min-width: 3rem;
    padding: 0.18rem 0.55rem;
    transform: translateX(-50%);
    border: 1px solid #b9aa91;
    border-radius: 999px;
    background: #eee8dc;
    color: #493c2c;
    text-align: center;
    font: 700 0.78rem/1.35 system-ui, sans-serif;
}
@media (max-width: 44rem) {
    .source-header,
    .page-index,
    .source-text { width: min(100% - 1rem, 62rem); }
    .source-text { padding-inline: 0.75rem; }
    .source-text table.multicol { font-size: 0.88rem; }
}
@media print {
    :root { background: white; }
    .source-header,
    .page-index { display: none; }
    .source-text {
        width: auto;
        margin: 0;
        padding: 0;
        box-shadow: none;
    }
    .source-text .ws-pagenum {
        break-before: page;
        border: 0;
    }
}
"""


class ElementInnerHtml(HTMLParser):
    """Retain the untouched inner markup of one classed div."""

    def __init__(self, target_class: str):
        super().__init__(convert_charrefs=False)
        self.target_class = target_class
        self.div_depth = 0
        self.target_depth: int | None = None
        self.parts: list[str] = []
        self.found = False
        self.complete = False

    @property
    def capturing(self) -> bool:
        return self.target_depth is not None

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if tag == "div" and not self.found and self.target_class in classes:
            self.found = True
            self.div_depth += 1
            self.target_depth = self.div_depth
            return
        if self.capturing:
            self.parts.append(self.get_starttag_text())
        if tag == "div":
            self.div_depth += 1

    def handle_startendtag(self, _tag, _attrs):
        if self.capturing:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag == "div":
            if self.capturing and self.div_depth == self.target_depth:
                self.target_depth = None
                self.complete = True
                self.div_depth -= 1
                return
            if self.capturing:
                self.parts.append(f"</{tag}>")
            self.div_depth -= 1
            return
        if self.capturing:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.capturing:
            self.parts.append(data)

    def handle_entityref(self, name):
        if self.capturing:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if self.capturing:
            self.parts.append(f"&#{name};")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    if ssl.get_default_verify_paths().cafile:
        return context
    for candidate in (
        Path("/etc/ssl/cert.pem"),
        Path("/etc/ssl/certs/ca-certificates.crt"),
        Path("/opt/homebrew/etc/openssl@3/cert.pem"),
    ):
        if candidate.is_file():
            context.load_verify_locations(cafile=candidate)
            return context
    raise RuntimeError("No trusted CA bundle is available for Wikisource HTTPS")


SSL_CONTEXT = verified_ssl_context()


def fetch(url: str) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    with urlopen(request, timeout=90, context=SSL_CONTEXT) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://"):
            raise ValueError(f"Source redirected away from HTTPS: {final_url}")
        return response.read(), response.headers.get_content_type(), final_url


def api(params: dict[str, str]) -> dict:
    payload, content_type, _ = fetch(f"{API_URL}?{urlencode(params)}")
    if content_type != "application/json":
        raise ValueError(f"Unexpected API content type: {content_type}")
    result = json.loads(payload)
    if "error" in result:
        raise ValueError(result["error"])
    return result


def extract_transcription(rendered: str) -> str:
    # The print page's prp-pages-output div is not a reliable outer boundary:
    # transcluded historical markup closes it early. The API's top-level
    # mw-parser-output wrapper is balanced and contains all 189 visible folio
    # markers; its print/navigation furniture is hidden by ws-noexport CSS.
    parser = ElementInnerHtml("mw-parser-output")
    parser.feed(rendered)
    parser.close()
    if not parser.found or not parser.complete:
        raise ValueError("Wikisource response has no complete mw-parser-output")
    return "".join(parser.parts).strip()


def make_urls_absolute(fragment: str) -> str:
    attribute = re.compile(
        r"(?<![\w:-])(?P<name>href)\s*=\s*(?P<quote>['\"])(?P<url>.*?)(?P=quote)",
        re.I,
    )

    def replace(match: re.Match) -> str:
        value = unescape(match.group("url"))
        if value.startswith("//"):
            value = "https:" + value
        elif value.startswith("/"):
            value = urljoin(WIKISOURCE_ORIGIN, value)
        elif not re.match(r"^(?:https?:|data:|mailto:|#|mw-data:)", value, re.I):
            value = urljoin(WIKISOURCE_ORIGIN + "/", value)
        return f'{match.group("name")}={match.group("quote")}{escape(value, quote=True)}{match.group("quote")}'

    return attribute.sub(replace, fragment)


def embed_images(fragment: str) -> tuple[str, list[dict]]:
    image_tag = re.compile(r"<img\b[^>]*>", re.I)
    src_attribute = re.compile(r"(?<![\w:-])src\s*=\s*(['\"])(.*?)\1", re.I)
    srcset_attribute = re.compile(r"\s+srcset\s*=\s*(['\"]).*?\1", re.I | re.S)
    cache: dict[str, tuple[str, bytes, str]] = {}
    records: list[dict] = []

    def replace_tag(match: re.Match) -> str:
        tag = match.group(0)
        source_match = src_attribute.search(tag)
        if not source_match:
            raise ValueError("Image without src in Wikisource rendering")
        raw_url = unescape(source_match.group(2))
        source_url = (
            "https:" + raw_url
            if raw_url.startswith("//")
            else urljoin(WIKISOURCE_ORIGIN, raw_url)
        )
        if source_url not in cache:
            payload, content_type, final_url = fetch(source_url)
            if not content_type.startswith("image/"):
                guessed = mimetypes.guess_type(final_url)[0]
                if not guessed or not guessed.startswith("image/"):
                    raise ValueError(f"Unexpected image content type: {content_type}")
                content_type = guessed
            data_uri = (
                f"data:{content_type};base64,{base64.b64encode(payload).decode()}"
            )
            cache[source_url] = (data_uri, payload, content_type)
            records.append(
                {
                    "url": source_url,
                    "resolved_url": final_url,
                    "content_type": content_type,
                    "bytes": len(payload),
                    "sha256": sha256(payload),
                }
            )
        data_uri, _payload, _content_type = cache[source_url]
        tag = src_attribute.sub(f'src="{data_uri}"', tag, count=1)
        return srcset_attribute.sub("", tag)

    return image_tag.sub(replace_tag, fragment), records


def page_markers(fragment: str) -> list[dict[str, str]]:
    markers = []
    for tag in re.findall(r"<span\b[^>]*>", fragment, re.I):
        class_match = re.search(r'class=["\']([^"\']+)["\']', tag, re.I)
        if (
            not class_match
            or "ws-pagenum" not in unescape(class_match.group(1)).split()
        ):
            continue
        identifier = re.search(r'id=["\']([^"\']+)["\']', tag, re.I)
        title = re.search(r'title=["\']([^"\']+)["\']', tag, re.I)
        if not identifier or not title:
            raise ValueError("Page marker is missing its id or source title")
        markers.append(
            {
                "id": unescape(identifier.group(1)),
                "source_title": unescape(title.group(1)),
            }
        )
    if len(markers) != EXPECTED_PAGE_MARKERS:
        raise ValueError(
            f"Expected {EXPECTED_PAGE_MARKERS} visible page markers, found {len(markers)}"
        )
    if len({marker["id"] for marker in markers}) != len(markers):
        raise ValueError("Duplicate page-marker ids in Wikisource rendering")
    return markers


def leaf_revisions() -> list[dict]:
    parsed = api(
        {
            "action": "parse",
            "page": PRINT_PAGE,
            "prop": "templates",
            "format": "json",
            "formatversion": "2",
        }
    )["parse"]
    prefix = "Página:Arte da língua brasílica (circa 1628).pdf/"
    titles = [
        template["title"]
        for template in parsed["templates"]
        if template["title"].startswith(prefix)
    ]
    expected = [f"{prefix}{number}" for number in range(1, EXPECTED_LEAF_PAGES + 1)]
    if titles != expected:
        raise ValueError("The transcluded Wikisource leaf-page sequence changed")

    revisions = []
    for start in range(0, len(titles), 50):
        queried = api(
            {
                "action": "query",
                "prop": "revisions",
                "rvprop": "ids|timestamp",
                "titles": "|".join(titles[start : start + 50]),
                "format": "json",
                "formatversion": "2",
            }
        )["query"]["pages"]
        by_title = {page["title"]: page for page in queried}
        for title in titles[start : start + 50]:
            page = by_title[title]
            revision = page["revisions"][0]
            revisions.append(
                {
                    "scan_page": int(title.rsplit("/", 1)[1]),
                    "title": title,
                    "page_id": page["pageid"],
                    "revision_id": revision["revid"],
                    "timestamp": revision["timestamp"],
                }
            )
    return revisions


def validate_safe(fragment: str, *, document: bool = False) -> None:
    candidate = fragment
    if document:
        allowed_meta = {
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<meta name="description" content="Transcrição integral e pesquisável da primeira edição da Arte da Lingua Brasilica de Luís Figueira (1628).">',
        }
        observed_meta = set(re.findall(r"<meta\b[^>]*>", candidate, re.I))
        if observed_meta != allowed_meta:
            raise ValueError(f"Unexpected document metadata: {observed_meta}")
        candidate = re.sub(r"<meta\b[^>]*>", "", candidate, flags=re.I)
    for pattern in (
        r"<\s*(?:script|iframe|object|embed|base|meta|form|input|button|textarea|select)\b",
        r"\son[a-z]+\s*=",
        r"javascript\s*:",
        r"(?:@import|expression\s*\(|-moz-binding|url\s*\()",
    ):
        if re.search(pattern, candidate, re.I):
            raise ValueError(f"Unsafe markup in Wikisource rendering: {pattern}")
    if document:
        for pattern in (r"<link\b", r"<(?:audio|video|source)\b"):
            if re.search(pattern, candidate, re.I):
                raise ValueError(f"External runtime element in snapshot: {pattern}")
        for source in re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", candidate, re.I):
            if not source.startswith("data:image/"):
                raise ValueError(f"Non-embedded image source: {source[:100]}")
        if re.search(r"\bsrcset\s*=", candidate, re.I):
            raise ValueError("Responsive image source escaped self-contained embedding")


def render_page(fragment: str, markers: list[dict], retrieved_at: str) -> str:
    links = "\n".join(
        f'<a href="#{escape(marker["id"], quote=True)}">{escape(marker["id"])}</a>'
        for marker in markers
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Transcrição integral e pesquisável da primeira edição da Arte da Lingua Brasilica de Luís Figueira (1628).">
<title>Arte da Lingua Brasilica — Luís Figueira (1628)</title>
<style>
{PAGE_CSS.strip()}
</style>
</head>
<body>
<header class="source-header">
  <h1>Arte da Lingua Brasilica</h1>
  <p class="byline"><i>Luís Figueira · primeira edição, Lisboa, cerca de 1628</i></p>
  <p class="source-note"><strong>Nota de edição:</strong> esta é a transcrição pesquisável da primeira edição preservada no Wikisource. As citações <i>Fig., Arte</i> do dicionário seguem a segunda edição de 1687 no fac-símile de 1878; a paginação não é intercambiável.</p>
  <p>Todo o texto transcrito está nesta página. Use <kbd>Ctrl+F</kbd> ou <kbd>⌘F</kbd> para pesquisar a grafia original.</p>
  <p class="source-actions">
    <a href="{WORK_URL}" target="_blank" rel="noopener">Transcrição no Wikisource</a>
    <a href="{PRINT_URL}" target="_blank" rel="noopener">Versão integral no Wikisource</a>
    <a href="/nhe-enga/docs/primary_sources/?book_name=figueira1878&amp;page_number=1">Fac-símile citado de 1687/1878</a>
  </p>
  <p><small>Instantâneo obtido em {escape(retrieved_at)}. Texto original em domínio público; transcrição do Wikisource sob <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br" target="_blank" rel="noopener">CC BY-SA 4.0</a>, com histórico editorial preservado nos links de origem.</small></p>
</header>
<details class="page-index">
  <summary>Ir para uma folha ({len(markers)} marcadores visíveis)</summary>
  <nav class="page-links" aria-label="Folhas da transcrição">
{links}
  </nav>
</details>
<article id="texto-original" class="source-text mw-parser-output">
{fragment}
</article>
</body>
</html>
"""


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        output.write(data)
    temporary.chmod(0o644)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--retrieved-at", default=date.today().isoformat())
    args = parser.parse_args()

    response = api(
        {
            "action": "parse",
            "page": PRINT_PAGE,
            "prop": "text|revid|displaytitle",
            "format": "json",
            "formatversion": "2",
        }
    )["parse"]
    rendered = response["text"]
    transcription = extract_transcription(rendered)
    validate_safe(transcription)
    transcription = make_urls_absolute(transcription)
    transcription = re.sub(
        r'<link\b[^>]*\bhref=["\']mw-data:[^>]*?/?>', "", transcription, flags=re.I
    )
    transcription, images = embed_images(transcription)
    markers = page_markers(transcription)
    revisions = leaf_revisions()
    html = render_page(transcription, markers, args.retrieved_at)
    validate_safe(html, document=True)
    html_bytes = html.encode("utf-8")

    metadata = {
        "schema_version": 1,
        "id": "figueira_arte_1628_wikisource",
        "title": "Arte da Lingua Brasilica",
        "author": "Luís Figueira",
        "edition": "Primeira edição, Lisboa, Manuel da Silva, cerca de 1628",
        "source_work_url": WORK_URL,
        "source_print_url": PRINT_URL,
        "source_api_url": API_URL,
        "print_wrapper_page_id": response["pageid"],
        "print_wrapper_revision_id": response["revid"],
        "retrieved_at": args.retrieved_at,
        "license": {
            "original": "public domain",
            "transcription": "CC BY-SA 4.0 and GFDL",
            "url": "https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br",
        },
        "snapshot": {
            "rendered_api_html_sha256": sha256(rendered.encode("utf-8")),
            "transcription_html_sha256": sha256(transcription.encode("utf-8")),
            "output_html_sha256": sha256(html_bytes),
            "output_bytes": len(html_bytes),
            "leaf_page_count": len(revisions),
            "visible_page_marker_count": len(markers),
            "embedded_image_count": len(images),
        },
        "edition_warning": (
            "This transcription is the circa-1628 first edition. Navarro's Fig., Arte "
            "citations use the 1687 second edition through Platzmann's 1878 facsimile, "
            "so citation page numbers must not be mapped directly to this transcription."
        ),
        "embedded_images": images,
        "page_markers": markers,
        "leaf_pages": revisions,
    }
    metadata_bytes = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    atomic_write(args.output.resolve(), html_bytes)
    atomic_write(args.metadata.resolve(), metadata_bytes)
    print(
        f"Wrote {args.output}: {len(revisions)} leaves, {len(markers)} markers, "
        f"{len(images)} embedded images, SHA-256 {sha256(html_bytes)}"
    )


if __name__ == "__main__":
    main()
