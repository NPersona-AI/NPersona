"""Plain text and Markdown parser."""

from __future__ import annotations

from pathlib import Path

from npersona.exceptions import DocumentParseError
from npersona.parsers.base import BaseParser


class TextParser(BaseParser):
    def parse(self, path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise DocumentParseError(str(path), str(exc)) from exc

        if not text.strip():
            raise DocumentParseError(str(path), "File is empty.")

        return self._truncate(text, path)
