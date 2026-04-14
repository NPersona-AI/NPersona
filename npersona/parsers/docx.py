"""DOCX document parser."""

from __future__ import annotations

from pathlib import Path

from npersona.exceptions import DocumentParseError, UnsupportedFormatError
from npersona.parsers.base import BaseParser


class DocxParser(BaseParser):
    def parse(self, path: Path) -> str:
        try:
            from docx import Document  # type: ignore[import]
        except ImportError:
            raise UnsupportedFormatError(
                ".docx — install support with: pip install npersona[docx]"
            )

        try:
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)
        except Exception as exc:
            raise DocumentParseError(str(path), str(exc)) from exc

        if not full_text.strip():
            raise DocumentParseError(str(path), "DOCX produced no extractable text.")

        return self._truncate(full_text, path)
