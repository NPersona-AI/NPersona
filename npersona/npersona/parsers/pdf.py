"""PDF document parser."""

from __future__ import annotations

from pathlib import Path

from npersona.exceptions import DocumentParseError, UnsupportedFormatError
from npersona.parsers.base import BaseParser


class PDFParser(BaseParser):
    def parse(self, path: Path) -> str:
        try:
            from pypdf import PdfReader  # type: ignore[import]
        except ImportError:
            raise UnsupportedFormatError(
                ".pdf — install support with: pip install npersona[pdf]"
            )

        try:
            reader = PdfReader(str(path))
            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            full_text = "\n".join(pages)
        except Exception as exc:
            raise DocumentParseError(str(path), str(exc)) from exc

        if not full_text.strip():
            raise DocumentParseError(str(path), "PDF produced no extractable text (may be scanned/image-only).")

        return self._truncate(full_text, path)
