"""Tests for document parsers."""

import tempfile
from pathlib import Path

import pytest

from npersona.exceptions import DocumentParseError, UnsupportedFormatError
from npersona.parsers.base import MAX_CHARS, parse_document
from npersona.parsers.text import TextParser


class TestParseDocument:
    def test_raw_string_returned_as_is(self):
        text = "This is a raw text input describing an AI system."
        result = parse_document(text)
        assert result == text

    def test_raw_string_truncated_at_max_chars(self):
        long_text = "x" * (MAX_CHARS + 1000)
        result = parse_document(long_text)
        assert len(result) == MAX_CHARS

    def test_nonexistent_file_raises_document_parse_error(self):
        with pytest.raises(DocumentParseError, match="file not found"):
            parse_document(Path("/nonexistent/path/file.txt"))

    def test_unsupported_extension_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"content")
            tmp_path = f.name
        with pytest.raises(UnsupportedFormatError, match=".xyz"):
            parse_document(Path(tmp_path))

    def test_path_object_accepted(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("Hello from a temp file.")
            tmp_path = f.name
        result = parse_document(Path(tmp_path))
        assert "Hello from a temp file." in result


class TestTextParser:
    def test_parses_utf8_text_file(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("AI system spec: agent Alpha handles user queries.")
            tmp_path = f.name
        parser = TextParser()
        result = parser.parse(Path(tmp_path))
        assert "agent Alpha" in result

    def test_parses_markdown_file(self):
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("# AI System\n\n## Agents\n- SupportBot\n- PaymentBot\n")
            tmp_path = f.name
        result = parse_document(Path(tmp_path))
        assert "SupportBot" in result
        assert "PaymentBot" in result

    def test_empty_file_raises_error(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("")
            tmp_path = f.name
        parser = TextParser()
        with pytest.raises(DocumentParseError, match="empty"):
            parser.parse(Path(tmp_path))

    def test_long_file_truncated(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("A" * (MAX_CHARS + 5000))
            tmp_path = f.name
        parser = TextParser()
        result = parser.parse(Path(tmp_path))
        assert len(result) == MAX_CHARS

    def test_non_utf8_bytes_handled_gracefully(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Normal text \xff\xfe with bad bytes")
            tmp_path = f.name
        parser = TextParser()
        result = parser.parse(Path(tmp_path))
        assert "Normal text" in result
