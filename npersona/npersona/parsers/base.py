"""Document parser base class and dispatch logic."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from npersona.exceptions import DocumentParseError, UnsupportedFormatError

logger = logging.getLogger(__name__)

MAX_CHARS = 80_000  # ~20k tokens — enough for most system specs


class BaseParser(ABC):
    """Abstract base for document parsers."""

    @abstractmethod
    def parse(self, path: Path) -> str:
        """Extract plain text from the document at *path*."""

    def _truncate(self, text: str, path: Path) -> str:
        if len(text) > MAX_CHARS:
            logger.warning(
                "Document '%s' truncated from %d to %d characters.",
                path.name,
                len(text),
                MAX_CHARS,
            )
            return text[:MAX_CHARS]
        return text


def parse_document(source: str | Path) -> str:
    """Parse a document from *source* (file path or raw text string).

    Supports: .pdf, .docx, .md, .txt, or any raw string.
    Returns plain UTF-8 text, truncated to MAX_CHARS.
    """
    if isinstance(source, str) and not Path(source).exists():
        # Treat as raw text input
        return source[:MAX_CHARS]

    path = Path(source)
    if not path.exists():
        raise DocumentParseError(str(path), "file not found")

    ext = path.suffix.lower()
    parser = _get_parser(ext, path)
    return parser.parse(path)


def _get_parser(ext: str, path: Path) -> BaseParser:
    if ext == ".pdf":
        from npersona.parsers.pdf import PDFParser
        return PDFParser()
    if ext == ".docx":
        from npersona.parsers.docx import DocxParser
        return DocxParser()
    if ext in (".md", ".txt", ".rst"):
        from npersona.parsers.text import TextParser
        return TextParser()
    raise UnsupportedFormatError(ext)
