"""aios_ingest.parser.pdf —— PDF 解析器（unstructured[pdf]）。"""
from __future__ import annotations

import io
import logging

from . import BaseParser, ParsedDocument

logger = logging.getLogger("aios_ingest.pdf")


class PdfParser(BaseParser):
    """PDF 解析：先尝试 unstructured[pdf]，失败回退 pypdf。"""

    kind = "pdf"

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        text_parts: list[str] = []
        sections: list[dict] = []
        tables: list[list[list[str]]] = []

        # 优先 unstructured
        try:
            from unstructured.partition.pdf import partition_pdf  # type: ignore

            elements = partition_pdf(file=io.BytesIO(content), strategy="fast")
            for el in elements:
                text_parts.append(str(el))
                if hasattr(el, "category") and el.category == "Title":
                    sections.append({"title": str(el), "content": "", "level": 1})
            if text_parts:
                return ParsedDocument(
                    kind=self.kind,
                    text="\n".join(text_parts),
                    sections=sections,
                    tables=tables,
                    metadata={"parser": "unstructured", "filename": filename},
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("unstructured failed, fallback pypdf: %s", e)

        # 回退 pypdf
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return ParsedDocument(
                kind=self.kind,
                text="\n".join(text_parts),
                sections=sections,
                tables=tables,
                metadata={"parser": "pypdf", "filename": filename, "page_count": len(reader.pages)},
            )
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"PDF 解析失败: {e}") from e


__all__ = ["PdfParser"]
