"""Tests for the multi-format ingestion pipeline (Task 1.1 / 1.2)."""

import json
from pathlib import Path

import pytest

from rag_service.ingestion import (
    IngestionError,
    MetadataError,
    apply_content_types,
    build_metadata,
    discover_sources,
    finalize_document,
    ingest,
    make_doc_id,
    parse_blade,
    parse_docx,
    parse_pdf,
)
from rag_service.ingestion.metadata import load_labels, write_metadata


class FakeTokenizer:
    """Stand-in for E5Tokenizer that never touches a model."""

    def count_tokens(self, text: str) -> int:
        return len(text.split())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def write_pdf(path: Path, pages) -> None:
    """Write a minimal single-font PDF; ``pages`` is a list of line lists."""
    page_objects = []
    content_objects = []
    for page_index, lines in enumerate(pages):
        content = "BT /F1 12 Tf 72 720 Td 14 TL\n" + "".join(
            f"({line}) Tj T*\n" for line in lines
        ) + "ET"
        content_objects.append(content.encode("latin-1"))

    # object ids: 1 catalog, 2 pages, then per page: page obj + content obj, font last
    first_page_obj = 3
    kids = []
    for index in range(len(pages)):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        kids.append(f"{page_obj} 0 R")
    font_obj = 3 + len(pages) * 2

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        ("<< /Type /Pages /Kids [" + " ".join(kids) + f"] /Count {len(pages)} >>").encode(),
    ]
    for index, content in enumerate(content_objects):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_obj} 0 R "
                f"/Resources << /Font << /F1 {font_obj} 0 R >> >> >>"
            ).encode()
        )
        objects.append(
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
            + content + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode()
    path.write_bytes(bytes(out))


BLADE_FAQ = """@extends('layouts.master')
@section('content')
<h2>FAQ</h2>
@php
$faqs = [
  ['id' => 'faq1', 'question' => 'Apa itu LPK MBJ?', 'answer' => 'Lembaga pelatihan bahasa Jepang.'],
  ['id' => 'faq2', 'question' => 'Siapa yang bisa mendaftar?', 'answer' => [
      'Warga Negara Indonesia', 'Usia 18-30 tahun'
  ]],
];
@endphp
@foreach($faqs as $faq)
  <p>{{ $faq['question'] }}</p>
@endforeach
@endsection
"""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def test_make_doc_id():
    assert make_doc_id("Panduan Pendaftaran.pdf") == "panduan_pendaftaran_pdf"
    assert make_doc_id("informasi/biaya-hidup") == "informasi_biaya_hidup"


def test_parse_pdf_extracts_text_and_strips_headers(tmp_path):
    path = tmp_path / "panduan.pdf"
    write_pdf(
        path,
        [
            ["LPK MBJ Indonesia", "Syarat usia 18-30 tahun", "LPK MBJ Indonesia"],
            ["LPK MBJ Indonesia", "Pendaftaran melalui halaman daftar", "LPK MBJ Indonesia"],
        ],
    )
    document = parse_pdf(path)
    assert document["doc_id"] == "panduan"
    assert document["source_type"] == "pdf"
    assert "18-30 tahun" in document["clean_text"]
    assert "--- Page 1 ---" in document["clean_text"]
    assert document["metadata"]["page_count"] == 2
    # repeated edge lines are removed from the body
    assert document["clean_text"].count("LPK MBJ Indonesia") == 0


def test_parse_docx_extracts_headings_and_tables(tmp_path):
    import docx

    path = tmp_path / "silabus.docx"
    document = docx.Document()
    document.add_heading("Silabus Program", level=1)
    document.add_paragraph("Materi bahasa Jepang dasar.")
    document.add_heading("Biaya", level=2)
    document.add_paragraph("Biaya hidup 80.000 yen per bulan.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Biaya"
    table.cell(1, 0).text = "Asrama"
    table.cell(1, 1).text = "30000"
    document.save(str(path))

    parsed = parse_docx(path)
    assert parsed["doc_id"] == "silabus"
    assert parsed["source_type"] == "docx"
    assert len(parsed["sections"]) == 2
    assert parsed["sections"][0]["heading"] == "Silabus Program"
    assert parsed["tables"] and "| Item |" in parsed["tables"][0]["markdown_table"]
    assert "Biaya hidup" in parsed["clean_text"]


def test_parse_blade_extracts_faq_and_body(tmp_path):
    path = tmp_path / "faq.blade.php"
    path.write_text(BLADE_FAQ, encoding="utf-8")
    document = parse_blade(path, doc_id="komunitas_faq")

    assert document["doc_id"] == "komunitas_faq"
    assert document["source_type"] == "web"
    assert document["title"] == "FAQ"
    assert "Pertanyaan: Apa itu LPK MBJ?" in document["clean_text"]
    assert "Jawaban: Lembaga pelatihan bahasa Jepang." in document["clean_text"]
    assert "Warga Negara Indonesia; Usia 18-30 tahun" in document["clean_text"]
    assert document["metadata"]["faq_pairs"] == 2
    # Blade directives must not leak into the text
    assert "@foreach" not in document["clean_text"]
    assert "{{" not in document["clean_text"]


def test_finalize_document_adds_counts():
    document = finalize_document(
        {"clean_text": "satu dua tiga", "sections": [{}], "metadata": {}},
        tokenizer=FakeTokenizer(),
    )
    assert document["metadata"]["token_count_e5"] == 3
    assert document["metadata"]["char_count"] == 13
    assert document["metadata"]["section_count"] == 1


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def test_discover_sources(tmp_path):
    (tmp_path / "pdf").mkdir()
    (tmp_path / "docx").mkdir()
    (tmp_path / "pdf" / "a.pdf").write_bytes(b"%PDF")
    (tmp_path / "docx" / "b.docx").write_bytes(b"x")
    views = tmp_path / "views"
    views.mkdir()
    (views / "page.blade.php").write_text("<p>hi</p>", encoding="utf-8")

    sources = discover_sources(tmp_path, views)
    assert [s[1] for s in sources] == ["pdf", "docx", "web"]


def test_ingest_writes_canonical_json(tmp_path):
    views = tmp_path / "views"
    views.mkdir()
    (views / "faq.blade.php").write_text(BLADE_FAQ, encoding="utf-8")
    out = tmp_path / "corpus"

    report = ingest(
        discover_sources(tmp_path / "raw", views),
        out,
        views_dir=views,
        tokenizer=FakeTokenizer(),
    )
    assert report["counts"] == {"web": 1}
    doc_path = out / "faq.json"
    document = json.loads(doc_path.read_text(encoding="utf-8"))
    assert document["source_type"] == "web"
    assert document["metadata"]["token_count_e5"] > 0


def test_ingest_rejects_duplicate_doc_ids(tmp_path):
    views = tmp_path / "views"
    views.mkdir()
    (views / "a-b.blade.php").write_text("<p>one</p>", encoding="utf-8")
    (views / "a_b.blade.php").write_text("<p>two</p>", encoding="utf-8")

    with pytest.raises(IngestionError):
        ingest(discover_sources(tmp_path / "raw", views), tmp_path / "out", views_dir=views)


# ---------------------------------------------------------------------------
# Metadata (Task 1.2)
# ---------------------------------------------------------------------------

DOCUMENTS = [
    {
        "doc_id": "a",
        "source_type": "pdf",
        "title": "A",
        "clean_text": "satu dua tiga",
        "sections": [{"heading": "Bab 1"}, {"heading": "Bab 2"}],
        "metadata": {},
    },
    {
        "doc_id": "b",
        "source_type": "web",
        "title": "B",
        "clean_text": "empat lima",
        "sections": [],
        "metadata": {},
    },
]


def test_build_metadata(tmp_path):
    write_metadata({"documents": [{"doc_id": "a", "content_type": "legal"}]}, tmp_path)
    labels = load_labels(tmp_path)
    payload = build_metadata(DOCUMENTS, tokenizer=FakeTokenizer(), labels=labels)

    by_id = {entry["doc_id"]: entry for entry in payload["documents"]}
    assert by_id["a"]["content_type"] == "legal"
    assert by_id["a"]["token_count_e5"] == 3
    assert by_id["a"]["sections"] == ["Bab 1", "Bab 2"]
    assert by_id["b"]["content_type"] is None


def test_build_metadata_rejects_bad_label():
    with pytest.raises(MetadataError):
        build_metadata(DOCUMENTS, labels={"a": "not_a_type"})


def test_apply_content_types_patches_document_json(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(DOCUMENTS[0]), encoding="utf-8")
    updated = apply_content_types(tmp_path, {"a": "narrative"})
    assert updated == 1
    patched = json.loads((tmp_path / "a.json").read_text(encoding="utf-8"))
    assert patched["content_type"] == "narrative"
    assert patched["metadata"]["content_type"] == "narrative"
    # idempotent
    assert apply_content_types(tmp_path, {"a": "narrative"}) == 0


def test_apply_content_types_rejects_bad_label(tmp_path):
    with pytest.raises(MetadataError):
        apply_content_types(tmp_path, {"a": "bogus"})
