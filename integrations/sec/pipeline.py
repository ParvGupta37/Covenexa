"""
SEC EDGAR Document Pipeline — Sprint 3.
Downloads SEC filing URL, parses HTML content, registers Agreement in DB,
and invokes Document Processing + Risk Intelligence Pipeline.
"""
from __future__ import annotations

import os
import uuid
import structlog
from datetime import datetime, timezone
from typing import Dict, Any

from integrations.sec.downloader import SECDownloader
from integrations.sec.html_parser import SECHTMLParser
from ai.workflows.workflow_manager import WorkflowManager

logger = structlog.get_logger(__name__)


class SECDocumentPipeline:
    """End-to-end pipeline for analyzing SEC EDGAR filings via URL."""

    def __init__(self):
        self.downloader = SECDownloader()
        self.parser = SECHTMLParser()

    async def process_sec_url(
        self,
        session,
        sec_url: str,
        loan_id: str,
        document_type: str = "sec_10k"
    ) -> Dict[str, Any]:
        logger.info("sec_pipeline.start", url=sec_url, loan_id=loan_id)

        # 1. Download SEC HTML
        file_path, meta = await self.downloader.download_filing(sec_url)

        # 2. Parse HTML to plain text
        parsed_text = self.parser.parse_html_file(file_path)

        # Save parsed plain text file alongside source for ingestion
        txt_path = file_path.rsplit(".", 1)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(parsed_text)

        # 3. Create AgreementORM entry
        from sqlalchemy import text
        res_loan = await session.execute(text("SELECT borrower_id FROM loans WHERE id = :l"), {"l": loan_id})
        loan_row = res_loan.mappings().first()
        if not loan_row:
            raise ValueError(f"Loan facility '{loan_id}' not found.")
        borrower_id = loan_row["borrower_id"]

        agreement_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await session.execute(
            text("""
                INSERT INTO agreements 
                (id, loan_id, version, file_path, upload_date, processing_status, page_count, chunk_count, document_type, source_url, source_type, filing_type, sec_cik)
                VALUES (:id, :lid, '1.0', :fp, :now, 'pending', 1, 0, :dt, :surl, 'sec_edgar', :ftype, :cik)
            """),
            {
                "id": agreement_id,
                "lid": loan_id,
                "fp": txt_path,
                "now": now,
                "dt": document_type,
                "surl": sec_url,
                "ftype": document_type,
                "cik": meta.get("cik"),
            }
        )
        await session.execute(
            text("UPDATE loans SET agreement_id = :aid WHERE id = :lid"),
            {"aid": agreement_id, "lid": loan_id}
        )
        await session.commit()

        # 4. Trigger AI ingestion workflow
        workflow_mgr = WorkflowManager()
        await workflow_mgr.trigger_document_ingestion(
            agreement_id=agreement_id,
            file_path=txt_path,
            file_type=document_type
        )

        logger.info("sec_pipeline.triggered", agreement_id=agreement_id)

        return {
            "agreement_id": agreement_id,
            "loan_id": loan_id,
            "borrower_id": borrower_id,
            "source_url": sec_url,
            "file_path": txt_path,
            "status": "processing",
        }
