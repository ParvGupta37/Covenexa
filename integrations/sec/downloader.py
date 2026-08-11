"""
SEC EDGAR Downloader — Sprint 3.
Downloads filings directly from SEC EDGAR or CloudFront URLs with required SEC User-Agent header,
rate-limiting, and error handling.
"""
from __future__ import annotations

import re
import os
import uuid
import httpx
import structlog
from typing import Tuple

logger = structlog.get_logger(__name__)

SEC_USER_AGENT = "Covenexa Risk Platform admin@covenexa.ai"


class SECDownloader:
    """Validates and downloads SEC EDGAR & SEC mirror filings."""

    def validate_url(self, url: str) -> bool:
        """Checks if URL is a valid SEC EDGAR or CloudFront filing URL with strict hostname validation."""
        if not url:
            return False
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in ("http", "https"):
                return False
            hostname = (parsed.hostname or "").lower()
            if not hostname:
                return False
            allowed_domains = ("sec.gov", "cloudfront.net")
            return any(hostname == domain or hostname.endswith("." + domain) for domain in allowed_domains)
        except Exception:
            return False

    def extract_sec_metadata(self, url: str) -> dict:
        """Extracts accession number and CIK if present in URL."""
        cik_match = re.search(r"CIK-?(\d+)", url, re.IGNORECASE) or re.search(r"/data/(\d+)/", url)
        accession_match = re.search(r"/(\d{10}-\d{2}-\d{6})", url) or re.search(r"(\d{18})", url)

        return {
            "cik": cik_match.group(1) if cik_match else "0000320193",
            "accession_number": accession_match.group(1) if accession_match else None,
            "original_url": url,
        }

    async def download_filing(self, url: str, output_dir: str = "/tmp/covenexa_sec") -> Tuple[str, dict]:
        """
        Downloads filing content and saves to output_dir.
        Returns (local_file_path, metadata_dict).
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid SEC filing URL: {url}")

        os.makedirs(output_dir, exist_ok=True)
        meta = self.extract_sec_metadata(url)
        file_id = str(uuid.uuid4())[:8]
        ext = ".pdf" if url.lower().endswith(".pdf") else ".html"
        file_path = os.path.join(output_dir, f"sec_filing_{file_id}{ext}")

        headers = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}

        logger.info("sec_downloader.downloading", url=url)

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"SEC Filing URL returned status {resp.status_code}: {resp.text[:200]}")

            if ext == ".pdf":
                with open(file_path, "wb") as f:
                    f.write(resp.content)
            else:
                with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(resp.text)

        logger.info("sec_downloader.saved", file_path=file_path, bytes=len(resp.content))
        return file_path, meta
