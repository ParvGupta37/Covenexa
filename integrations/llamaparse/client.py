"""
LlamaParse integration client — Sprint 2 implementation.
Parses PDF/DOCX/XLSX/CSV documents with high fidelity.
Falls back to pypdf for plain text extraction when LlamaParse is unavailable.
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class LlamaParseClient:
    """
    LlamaParse API client for document parsing.
    When LLAMAPARSE_API_KEY is not set, falls back to pypdf-based text extraction.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: Any = None
        self._use_fallback = not api_key or api_key == "not_set"
        if self._use_fallback:
            logger.warning("LlamaParseClient: No API key — will use pypdf fallback.")
        else:
            logger.info("LlamaParseClient initialized.")

    def initialize(self) -> None:
        """Initialize LlamaParse client if API key is available."""
        if self._use_fallback:
            return
        try:
            from llama_parse import LlamaParse
            self._client = LlamaParse(
                api_key=self._api_key,
                result_type="markdown",
                verbose=False,
            )
            logger.info("LlamaParseClient connected.")
        except ImportError:
            logger.warning("llama-parse package not installed; using pypdf fallback.")
            self._use_fallback = True

    async def parse_document(
        self,
        file_path: str,
        result_type: str = "markdown",
    ) -> dict[str, Any]:
        """
        Parse a document file and return structured content.

        Returns:
            {
                "text": str,             # full extracted text/markdown
                "pages": list[dict],     # per-page content
                "sections": list[str],   # detected section headers
                "page_count": int,
                "method": str,           # "llamaparse" | "pypdf" | "error"
            }
        """
        ext = os.path.splitext(file_path)[-1].lower()

        if not self._use_fallback and self._client is not None:
            return await self._parse_with_llamaparse(file_path)

        # Fallback
        return await self._parse_with_pypdf(file_path, ext)

    async def _parse_with_llamaparse(self, file_path: str) -> dict[str, Any]:
        """Use LlamaParse API for rich structured parsing."""
        try:
            documents = await self._client.aload_data(file_path)
            pages = []
            full_text_parts = []
            for i, doc in enumerate(documents):
                content = doc.text
                full_text_parts.append(content)
                pages.append({"page": i + 1, "content": content})

            full_text = "\n\n".join(full_text_parts)
            sections = _extract_section_headers(full_text)
            return {
                "text": full_text,
                "pages": pages,
                "sections": sections,
                "page_count": len(pages),
                "method": "llamaparse",
            }
        except Exception as exc:
            logger.error("LlamaParse failed (%s), falling back to pypdf.", exc)
            return await self._parse_with_pypdf(file_path, os.path.splitext(file_path)[-1].lower())

    async def _parse_with_pypdf(self, file_path: str, ext: str) -> dict[str, Any]:
        """Pure Python fallback using pypdf for PDFs, basic text read for others."""
        try:
            if ext == ".pdf":
                return await _parse_pdf(file_path)
            elif ext in (".txt", ".md"):
                with open(file_path, "r", errors="ignore") as f:
                    text = f.read()
                return {
                    "text": text,
                    "pages": [{"page": 1, "content": text}],
                    "sections": _extract_section_headers(text),
                    "page_count": 1,
                    "method": "text_read",
                }
            else:
                # DOCX / XLSX — basic string extraction
                return await _parse_binary_fallback(file_path)
        except Exception as exc:
            logger.error("Fallback parsing also failed: %s", exc)
            return {
                "text": "",
                "pages": [],
                "sections": [],
                "page_count": 0,
                "method": "error",
            }


async def _parse_pdf(file_path: str) -> dict[str, Any]:
    """Extract text from PDF using pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        content = page.extract_text() or ""
        pages.append({"page": i + 1, "content": content})
    full_text = "\n\n".join(p["content"] for p in pages)
    return {
        "text": full_text,
        "pages": pages,
        "sections": _extract_section_headers(full_text),
        "page_count": len(pages),
        "method": "pypdf",
    }


async def _parse_binary_fallback(file_path: str) -> dict[str, Any]:
    """Try to read binary files as UTF-8 text."""
    try:
        with open(file_path, "r", errors="ignore") as f:
            text = f.read()
    except Exception:
        text = ""
    return {
        "text": text,
        "pages": [{"page": 1, "content": text}],
        "sections": _extract_section_headers(text),
        "page_count": 1,
        "method": "text_fallback",
    }


def _extract_section_headers(text: str) -> list[str]:
    """Extract markdown-style or ALL-CAPS section headers from text."""
    sections = []
    for line in text.splitlines():
        stripped = line.strip()
        # Markdown headings
        if stripped.startswith("#") and len(stripped) > 2:
            sections.append(stripped.lstrip("#").strip())
        # All-caps lines (typical in legal docs)
        elif stripped.isupper() and 5 < len(stripped) < 120 and stripped.replace(" ", "").isalpha():
            sections.append(stripped)
    return sections[:50]  # cap to avoid noise
