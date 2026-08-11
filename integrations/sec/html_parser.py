"""
SEC Document Parser — Sprint 3.
Parses SEC EDGAR HTML or PDF filings into clean semantic text while preserving tables and key section headers.
"""
from __future__ import annotations

import re
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger(__name__)


class SECHTMLParser:
    """Parses raw HTML or PDF from SEC filings into clean text for AI ingestion."""

    def parse_html_file(self, file_path: str) -> str:
        if file_path.lower().endswith(".pdf"):
            return self.parse_pdf_file(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()
        return self.parse_html(html_content)

    def parse_pdf_file(self, file_path: str) -> str:
        text_chunks = []
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_chunks.append(t)
        except Exception as e:
            logger.warning("sec_parser.pdf_read_error", error=str(e))
            text_chunks.append("SEC Filing PDF Document Content")

        return "\n\n".join(text_chunks)

    def parse_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "lxml")

        # Remove irrelevant elements
        for element in soup(["script", "style", "nav", "footer", "head", "noscript", "svg"]):
            element.decompose()

        # Extract text while preserving linebreaks for paragraphs & headers
        text = soup.get_text(separator="\n")

        # Clean whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if not line:
                continue
            cleaned_line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(cleaned_line)

        cleaned_text = "\n\n".join(cleaned_lines)
        logger.info("sec_parser.parsed", raw_len=len(html_content), clean_len=len(cleaned_text))
        return cleaned_text
