"""Document parser – extracts clean text from PDF, DOCX, MD, and TXT files."""
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def parse_document(filename: str, content: bytes) -> str:
    """Parse uploaded document bytes into clean text.

    Supports: .pdf, .docx, .md, .txt
    """
    ext = Path(filename).suffix.lower()
    logger.info(f"Parsing document: {filename} (type={ext}, size={len(content)} bytes)")

    if ext == ".pdf":
        return _parse_pdf(content)
    elif ext == ".docx":
        return _parse_docx(content)
    elif ext in (".md", ".markdown"):
        return _parse_markdown(content)
    elif ext == ".txt":
        return content.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx, .md, .txt")


def _parse_pdf(content: bytes) -> str:
    """Extract text from PDF using PyPDF2."""
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    full_text = "\n\n".join(pages)
    logger.info(f"PDF parsed: {len(reader.pages)} pages, {len(full_text)} chars")
    return full_text


def _parse_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    logger.info(f"DOCX parsed: {len(paragraphs)} paragraphs, {len(full_text)} chars")
    return full_text


def _parse_markdown(content: bytes) -> str:
    """Return raw markdown text (strip HTML if markdown lib is used)."""
    import markdown
    from html import unescape
    import re

    raw = content.decode("utf-8", errors="replace")
    # Convert to HTML then strip tags to get clean text, but also keep raw for context
    html = markdown.markdown(raw)
    clean = re.sub(r"<[^>]+>", "", unescape(html))
    logger.info(f"Markdown parsed: {len(clean)} chars")
    return raw  # Return raw markdown – LLM understands it better than stripped text
