"""Multi-format document parsers producing canonical corpus JSON (Task 1.1).

Each parser returns a dictionary with the fields the chunkers and the indexer
expect::

    {
      "doc_id": "panduan_pendaftaran",
      "source_type": "pdf",            # pdf | docx | web
      "title": "Panduan Pendaftaran",
      "source_file": "panduan_pendaftaran.pdf",
      "clean_text": "...",
      "sections": [{"heading": "...", "text": "..."}],
      "tables": [{"caption": "...", "markdown_table": "| ... |"}],
      "metadata": {"page_count": 3, "section_count": 4, "char_count": 1234}
    }

Token counts (E5) are added later by ``finalize_document`` so the parsers stay
pure and easy to test without loading a tokenizer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BLADE_ECHO_RE = re.compile(r"\{!!.*?!!\}|\{\{.*?\}\}", re.DOTALL)
_PHP_BLOCK_RE = re.compile(r"@php\b.*?@endphp", re.DOTALL)
_BLADE_DIRECTIVE_RE = re.compile(r"@end\w+|@\w+(?:\s*\((?:[^()]|\([^()]*\))*\))?")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BLANK_LINES_RE = re.compile(r"\n{3,}")
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")

_QUESTION_RE = re.compile(r"'question'\s*=>\s*'((?:[^'\\]|\\.)*)'")
_ANSWER_STRING_RE = re.compile(r"'answer'\s*=>\s*'((?:[^'\\]|\\.)*)'")
_ANSWER_ARRAY_RE = re.compile(r"'answer'\s*=>\s*\[(.*?)\]", re.DOTALL)
_QUOTED_RE = re.compile(r"'((?:[^'\\]|\\.)*)'")


def make_doc_id(name: str) -> str:
    """Normalize a file name or path into a lowercase underscore doc_id."""
    normalized = re.sub(r"[^a-z0-9]+", "_", str(name).lower())
    return normalized.strip("_")


def _title_from_stem(stem: str) -> str:
    return " ".join(word.capitalize() for word in re.split(r"[_\-\s]+", stem) if word)


def _normalize_text(text: str) -> str:
    """Collapse excess whitespace while keeping paragraph breaks."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [_MULTISPACE_RE.sub(" ", line) for line in lines]
    cleaned = "\n".join(lines)
    return _BLANK_LINES_RE.sub("\n\n", cleaned).strip()


def _unescape(value: str) -> str:
    return value.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def _to_markdown_table(rows: Sequence[Sequence[Any]], caption: str = "Tabel") -> str:
    """Render a list-of-rows table as a GitHub-flavoured Markdown table."""
    cleaned_rows = [
        [str(cell).replace("\n", " ").strip() if cell is not None else "" for cell in row]
        for row in rows
        if row
    ]
    if not cleaned_rows:
        return ""
    header, *body = cleaned_rows
    width = max(len(row) for row in cleaned_rows)
    header = header + [""] * (width - len(header))
    separator = ["---"] * width
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(separator) + " |"]
    for row in body:
        row = row + [""] * (width - len(row))
        lines.append("| " + " | ".join(row) + " |")
    return f"**{caption}**\n" + "\n".join(lines)


def finalize_document(
    document: Dict[str, Any], tokenizer: Optional[Any] = None
) -> Dict[str, Any]:
    """Add derived counts to a parsed document."""
    document = dict(document)
    metadata = dict(document.get("metadata") or {})
    metadata["char_count"] = len(document.get("clean_text", ""))
    metadata["section_count"] = len(document.get("sections") or [])
    if tokenizer is not None:
        metadata["token_count_e5"] = tokenizer.count_tokens(document.get("clean_text", ""))
    document["metadata"] = metadata
    return document


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _strip_repeated_lines(pages: List[str], min_ratio: float = 0.5) -> List[str]:
    """Remove headers/footers that repeat across most pages."""
    if len(pages) < 2:
        return pages

    edge_counts: Dict[str, int] = {}
    for page in pages:
        lines = [line for line in page.splitlines() if line.strip()]
        for edge in {lines[0], lines[-1]} if lines else ():
            edge_counts[edge] = edge_counts.get(edge, 0) + 1

    threshold = max(2, int(len(pages) * min_ratio + 0.5))
    repeated = {line for line, count in edge_counts.items() if count >= threshold}
    if not repeated:
        return pages

    cleaned_pages = []
    for page in pages:
        kept = [
            line
            for line in page.splitlines()
            if line.strip() not in repeated or not line.strip()
        ]
        cleaned_pages.append(_normalize_text("\n".join(kept)))
    return cleaned_pages


def parse_pdf(path: Path) -> Dict[str, Any]:
    """Extract text, tables, and a header/footer-stripped body from a PDF."""
    import pdfplumber

    path = Path(path)
    raw_pages: List[str] = []
    tables: List[Dict[str, str]] = []

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_pages.append(page.extract_text() or "")
            for table_index, table in enumerate(page.extract_tables() or [], start=1):
                markdown = _to_markdown_table(
                    table, caption=f"Tabel {page_number}-{table_index}"
                )
                if markdown:
                    tables.append(
                        {
                            "caption": f"Tabel {page_number}-{table_index}",
                            "markdown_table": markdown,
                        }
                    )

    pages = _strip_repeated_lines([_normalize_text(p) for p in raw_pages])
    clean_text = "\n\n".join(
        f"--- Page {number} ---\n\n{text}"
        for number, text in enumerate(pages, start=1)
        if text.strip()
    )
    sections = [
        {"heading": f"Page {number}", "text": text}
        for number, text in enumerate(pages, start=1)
        if text.strip()
    ]

    return {
        "doc_id": make_doc_id(path.stem),
        "source_type": "pdf",
        "title": _title_from_stem(path.stem),
        "source_file": path.name,
        "clean_text": clean_text.strip(),
        "sections": sections,
        "tables": tables,
        "metadata": {"page_count": len(raw_pages)},
    }


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def _heading_level(style_name: str) -> int:
    match = re.search(r"heading\s*(\d+)", style_name or "", re.IGNORECASE)
    return int(match.group(1)) if match else 0


def parse_docx(path: Path) -> Dict[str, Any]:
    """Extract heading hierarchy, paragraphs, and tables from a DOCX file."""
    import docx

    path = Path(path)
    document = docx.Document(str(path))

    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"heading": "", "level": 0, "text_parts": []}

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        level = _heading_level(getattr(paragraph.style, "name", ""))
        if level:
            if current["heading"] or current["text_parts"]:
                sections.append(current)
            current = {"heading": text, "level": level, "text_parts": []}
        else:
            current["text_parts"].append(text)
    if current["heading"] or current["text_parts"]:
        sections.append(current)

    tables: List[Dict[str, str]] = []
    for index, table in enumerate(document.tables, start=1):
        markdown = _to_markdown_table(
            [[cell.text for cell in row.cells] for row in table.rows],
            caption=f"Tabel {index}",
        )
        if markdown:
            tables.append({"caption": f"Tabel {index}", "markdown_table": markdown})

    normalized_sections: List[Dict[str, Any]] = []
    for section in sections:
        text = "\n\n".join(section["text_parts"]).strip()
        heading = section["heading"]
        normalized_sections.append(
            {"heading": heading, "level": section["level"], "text": text}
        )

    text_blocks = []
    for section in normalized_sections:
        if section["heading"]:
            text_blocks.append(f"{'#' * max(1, section['level'])} {section['heading']}")
        if section["text"]:
            text_blocks.append(section["text"])
    text_blocks.extend(table["markdown_table"] for table in tables)

    return {
        "doc_id": make_doc_id(path.stem),
        "source_type": "docx",
        "title": normalized_sections[0]["heading"] if normalized_sections and normalized_sections[0]["heading"] else _title_from_stem(path.stem),
        "source_file": path.name,
        "clean_text": _normalize_text("\n\n".join(text_blocks)),
        "sections": normalized_sections,
        "tables": tables,
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# Blade (web)
# ---------------------------------------------------------------------------

def extract_php_pairs(text: str) -> List[Dict[str, str]]:
    """Extract ``'question' => '...'`` / ``'answer' => ...`` pairs from Blade PHP."""
    matches = list(_QUESTION_RE.finditer(text))
    pairs: List[Dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        window = text[match.start():end]
        answer_match = _ANSWER_STRING_RE.search(window)
        if answer_match:
            answer = _unescape(answer_match.group(1))
        else:
            array_match = _ANSWER_ARRAY_RE.search(window)
            answer = (
                "; ".join(_unescape(item) for item in _QUOTED_RE.findall(array_match.group(1)))
                if array_match
                else ""
            )
        pairs.append({"question": _unescape(match.group(1)), "answer": answer})
    return pairs


def _strip_blade(text: str) -> str:
    text = _HTML_COMMENT_RE.sub(" ", text)
    text = _PHP_BLOCK_RE.sub(" ", text)
    text = _BLADE_ECHO_RE.sub(" ", text)
    return _BLADE_DIRECTIVE_RE.sub(" ", text)


def _visible_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "link", "meta"]):
        tag.decompose()
    return soup.get_text("\n")


def _first_heading(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag_name in ("h1", "h2", "h3"):
        tag = soup.find(tag_name)
        if tag is None:
            continue
        # Some Blade pages close a <h3> with </h1>; the stray close keeps the
        # heading open and swallows sibling markup. Use only direct text nodes
        # so the breadcrumb list is not merged into the title.
        direct = "".join(tag.find_all(string=True, recursive=False)).strip()
        if direct:
            return direct
        nested = tag.get_text(strip=True)
        if nested:
            return nested
    return ""


def parse_blade(path: Path, doc_id: Optional[str] = None, views_root: Optional[Path] = None) -> Dict[str, Any]:
    """Extract clean text (including FAQ PHP pairs) from a Blade template."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")

    pairs = extract_php_pairs(raw)
    html = _strip_blade(raw)
    body = _normalize_text(_visible_text(html))
    title = _first_heading(html)

    qa_text = "\n\n".join(
        f"Pertanyaan: {pair['question']}\nJawaban: {pair['answer']}" for pair in pairs
    )
    clean_text = "\n\n".join(part for part in (qa_text, body) if part).strip()

    if doc_id is None:
        relative = path
        if views_root is not None:
            try:
                relative = path.relative_to(views_root)
            except ValueError:
                relative = path
        name = re.sub(r"\.blade\.php$", "", str(relative))
        doc_id = make_doc_id(name.replace("/", "_"))

    return {
        "doc_id": doc_id,
        "source_type": "web",
        "title": title or _title_from_stem(doc_id),
        "source_file": path.name,
        "clean_text": clean_text,
        "sections": [{"heading": title, "text": clean_text}] if clean_text else [],
        "tables": [],
        "metadata": {"faq_pairs": len(pairs)},
    }


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_PARSERS: Dict[str, Callable[[Path], Dict[str, Any]]] = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}


def parse_file(path: Path, source_type: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    """Parse one file, choosing the parser from its extension."""
    path = Path(path)
    if path.suffix.lower() == ".blade" or path.name.endswith(".blade.php"):
        return parse_blade(path, **kwargs)
    parser = _PARSERS.get(path.suffix.lower())
    if parser is None:
        raise ValueError(f"unsupported file type: {path}")
    return parser(path)


SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".blade.php")
