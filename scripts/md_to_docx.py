#!/usr/bin/env python3
"""Convert draft korpus .md -> .docx (final format: title + content only).

Strips: draft blockquote, `**Tipe konten:**`, `**Target doc_id:**`, and `---` rules.
Handles: headings, bold, inline code, links, bullet/numbered lists, pipe tables.

Usage: python scripts/md_to_docx.py <input.md> <output.docx>
"""
import re
import sys
from pathlib import Path

from docx import Document

TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def is_meta(line: str) -> bool:
    s = line.strip()
    return (
        s.startswith(">")
        or s.startswith("**Tipe konten:**")
        or s.startswith("**Target ")
        or s == "---"
    )


def add_runs(par, text: str) -> None:
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("*") and part.endswith("*"):
            par.add_run(part[1:-1]).italic = True
        elif part.startswith("`") and part.endswith("`"):
            par.add_run(part[1:-1]).font.name = "Consolas"
        elif part.startswith("[") and "](" in part:
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            if m:
                par.add_run(m.group(1))
        else:
            par.add_run(part)


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md_path: Path, out_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        s = line.strip()

        if is_meta(line):
            i += 1
            continue
        if not s:
            i += 1
            continue

        # pipe table
        if s.startswith("|") and i + 1 < n and set(lines[i + 1].strip()) <= set("|-: "):
            header = split_row(s)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i].strip()))
                i += 1
            table = doc.add_table(rows=1, cols=len(header))
            table.style = "Table Grid"
            for j, h in enumerate(header):
                cell = table.rows[0].cells[j]
                cell.paragraphs[0].clear()
                add_runs(cell.paragraphs[0], h)
                for r in cell.paragraphs[0].runs:
                    r.bold = True
            for row in rows:
                cells = table.add_row().cells
                for j in range(len(header)):
                    text = row[j] if j < len(row) else ""
                    cells[j].paragraphs[0].clear()
                    add_runs(cells[j].paragraphs[0], text)
            doc.add_paragraph()
            continue

        # headings
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            level = len(m.group(1))
            style = {1: "Title", 2: "Heading 1", 3: "Heading 2", 4: "Heading 3"}[level]
            p = doc.add_paragraph(style=style)
            add_runs(p, m.group(2))
            i += 1
            continue

        # bullets
        if re.match(r"^[-*•]\s+", s):
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, re.sub(r"^[-*•]\s+", "", s))
            i += 1
            continue

        # numbered list
        if re.match(r"^\d+\.\s+", s):
            p = doc.add_paragraph(style="List Number")
            add_runs(p, re.sub(r"^\d+\.\s+", "", s))
            i += 1
            continue

        # normal paragraph
        p = doc.add_paragraph()
        add_runs(p, s)
        i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"OK -> {sys.argv[2]}")
