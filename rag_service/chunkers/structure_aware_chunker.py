"""Structure-Aware chunker for heterogeneous multi-format documents (PDF, DOCX, Web)."""

import re
from typing import Any, Dict, List, Optional
from rag_service.chunkers.base import BaseChunker, Chunk
from rag_service.chunkers.recursive_chunker import RecursiveCharacterChunker
from rag_service.chunkers.tokenizer import E5Tokenizer


class StructureAwareChunker(BaseChunker):
    """Chunks documents based on domain-specific structural semantics.

    Multi-format handling:
      - Web:
          * qa_pairs (FAQ): Preserves Question + Answer pair as an atomic unit.
          * procedural: Groups sequential steps (e.g., 2-3 steps per chunk).
          * comparison / numeric: Keeps comparison tables and fee breakdowns intact.
      - DOCX:
          * Splits at Heading boundaries (Heading 1, 2, 3), keeping paragraphs and tables
            under their parent heading.
      - PDF:
          * Splits at document sections and keeps Markdown tables intact as single chunks.
    All chunks are strictly bounded to <= 512 E5 tokens via recursive fallback.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        tokenizer: Optional[E5Tokenizer] = None,
    ):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
        )
        self._fallback_recursive = RecursiveCharacterChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=self.tokenizer,
        )

    def chunk_document(self, document: Dict[str, Any]) -> List[Chunk]:
        """Dispatch document chunking based on source_type and content_type."""
        source_type = document.get("source_type", "web").lower()
        content_type = document.get("content_type", "").lower()
        clean_text = document.get("clean_text", "")

        if source_type == "web":
            return self._chunk_web_document(document)
        elif source_type == "docx":
            return self._chunk_docx_document(document)
        elif source_type == "pdf":
            return self._chunk_pdf_document(document)

        # Fallback to general structured text chunking
        return self.chunk_text(
            text=clean_text,
            doc_id=document.get("doc_id", "doc"),
            source_type=source_type,
            source_title=document.get("title", "Untitled"),
            metadata=document.get("metadata", {}),
        )

    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc",
        source_type: str = "text",
        source_title: str = "Untitled",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Chunk arbitrary structured text by headings and sections."""
        text = text.strip()
        if not text:
            return []

        metadata = dict(metadata or {})
        content_type = metadata.get("content_type", "").lower()

        if "qa" in content_type or "faq" in content_type:
            return self._chunk_qa_text(text, doc_id, source_type, source_title, metadata)

        # Split on markdown headings (# Heading, ## Heading)
        sections = re.split(r"(?m)^(?=#{1,4}\s+)", text)
        if len(sections) <= 1:
            sections = re.split(r"\n{2,}", text)

        return self._pack_units_into_chunks(
            units=sections,
            doc_id=doc_id,
            source_type=source_type,
            source_title=source_title,
            metadata=metadata,
            structure_tag="section",
        )

    def _chunk_web_document(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Specialized chunking for Web pages."""
        content_type = doc.get("content_type", "").lower()
        text = doc.get("clean_text", "")
        doc_id = doc.get("doc_id", "web_doc")
        title = doc.get("title", "Web Page")
        metadata = doc.get("metadata", {})

        # 1. FAQ / QA Pairs
        if "qa" in content_type or "faq" in doc_id or "faq" in content_type:
            return self._chunk_qa_text(text, doc_id, "web", title, metadata)

        # 2. Procedural steps (e.g. Alur Pendaftaran)
        if "procedur" in content_type or "pendaftaran" in doc_id:
            steps = re.split(r"(?m)(?=(?:Langkah|Tahap|Step|\d+\.)\s+)", text)
            if len(steps) > 1:
                # Group 2-3 steps per chunk
                grouped_units = []
                current_group = []
                for step in steps:
                    if not step.strip():
                        continue
                    current_group.append(step.strip())
                    if len(current_group) >= 2:
                        grouped_units.append("\n\n".join(current_group))
                        current_group = []
                if current_group:
                    grouped_units.append("\n\n".join(current_group))

                return self._pack_units_into_chunks(
                    units=grouped_units,
                    doc_id=doc_id,
                    source_type="web",
                    source_title=title,
                    metadata={**metadata, "structure": "procedural_grouped"},
                    structure_tag="step_group",
                )

        # Default web sections by double newline or headers
        units = re.split(r"\n{2,}", text)
        return self._pack_units_into_chunks(
            units=units,
            doc_id=doc_id,
            source_type="web",
            source_title=title,
            metadata=metadata,
            structure_tag="web_block",
        )

    def _chunk_docx_document(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Specialized chunking for DOCX files preserving Heading hierarchies and tables."""
        text = doc.get("clean_text", "")
        doc_id = doc.get("doc_id", "docx_doc")
        title = doc.get("title", "Word Document")
        metadata = doc.get("metadata", {})
        sections = doc.get("sections", [])

        if sections:
            units = []
            for sec in sections:
                heading = sec.get("heading", "")
                sec_text = sec.get("text", "")
                units.append(f"### {heading}\n{sec_text}" if heading else sec_text)
            return self._pack_units_into_chunks(
                units=units,
                doc_id=doc_id,
                source_type="docx",
                source_title=title,
                metadata={**metadata, "structure": "docx_heading_tree"},
                structure_tag="heading_section",
            )

        # Split on Markdown headers if sections list is absent
        units = re.split(r"(?m)^(?=#{1,4}\s+)", text)
        return self._pack_units_into_chunks(
            units=units,
            doc_id=doc_id,
            source_type="docx",
            source_title=title,
            metadata=metadata,
            structure_tag="docx_block",
        )

    def _chunk_pdf_document(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Specialized chunking for PDF files isolating tables and sections."""
        text = doc.get("clean_text", "")
        doc_id = doc.get("doc_id", "pdf_doc")
        title = doc.get("title", "PDF Document")
        metadata = doc.get("metadata", {})
        tables = doc.get("tables", [])

        # If tables are explicitly extracted, format them as standalone units
        units: List[str] = []
        if tables:
            for tbl in tables:
                caption = tbl.get("caption", "Tabel")
                md_table = tbl.get("markdown_table", "")
                if md_table:
                    units.append(f"**{caption}**\n{md_table}")

        # Split remaining text by page breaks or section headings
        text_sections = re.split(r"(?m)(?:--- Page \d+ ---|(?=#{1,3}\s+))", text)
        for ts in text_sections:
            if ts.strip():
                units.append(ts.strip())

        return self._pack_units_into_chunks(
            units=units,
            doc_id=doc_id,
            source_type="pdf",
            source_title=title,
            metadata=metadata,
            structure_tag="pdf_section",
        )

    def _chunk_qa_text(
        self,
        text: str,
        doc_id: str,
        source_type: str,
        source_title: str,
        metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """Preserve Q&A pairs as complete individual chunks."""
        # Detect start of Question / Pertanyaan / FAQ item
        qa_blocks = re.split(r"(?m)(?=(?:^|\n+)\s*(?:Q\s*\d*[:.]|Pertanyaan\s*\d*[:.]|\bFAQ\s*\d*[:.]))", text)
        qa_units = [b.strip() for b in qa_blocks if b.strip()]

        if not qa_units:
            qa_units = re.split(r"\n{2,}", text)

        return self._pack_units_into_chunks(
            units=qa_units,
            doc_id=doc_id,
            source_type=source_type,
            source_title=source_title,
            metadata={**metadata, "structure": "qa_pair"},
            structure_tag="qa_item",
        )

    def _pack_units_into_chunks(
        self,
        units: List[str],
        doc_id: str,
        source_type: str,
        source_title: str,
        metadata: Dict[str, Any],
        structure_tag: str,
    ) -> List[Chunk]:
        """Pack structural units into <= 512 token chunks, falling back if a unit is too large."""
        chunks: List[Chunk] = []
        chunk_idx = 0

        for unit in units:
            unit = unit.strip()
            if not unit:
                continue

            unit_tokens = self.tokenizer.count_tokens(unit)

            if unit_tokens <= self.chunk_size:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}_str_{chunk_idx:04d}",
                        doc_id=doc_id,
                        source_type=source_type,
                        source_title=source_title,
                        content=unit,
                        token_count=unit_tokens,
                        start_char=0,
                        end_char=len(unit),
                        metadata={
                            **metadata,
                            "chunk_index": chunk_idx,
                            "strategy": "structure_aware",
                            "structure_type": structure_tag,
                        },
                    )
                )
                chunk_idx += 1
            else:
                # If a single structural unit exceeds 512 tokens, apply recursive fallback
                sub_chunks = self._fallback_recursive.chunk_text(
                    text=unit,
                    doc_id=f"{doc_id}_part",
                    source_type=source_type,
                    source_title=source_title,
                    metadata={**metadata, "structure_fallback": True},
                )
                for sc in sub_chunks:
                    sc.chunk_id = f"{doc_id}_str_{chunk_idx:04d}"
                    sc.metadata["chunk_index"] = chunk_idx
                    sc.metadata["strategy"] = "structure_aware"
                    sc.metadata["structure_type"] = f"{structure_tag}_split"
                    chunks.append(sc)
                    chunk_idx += 1

        return chunks
