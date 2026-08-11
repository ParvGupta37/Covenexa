"""
Idempotent Duplicate Row Cleanup Script for Acme Tech Inc. (LOW-5)

Identifies and cleans duplicate/stale scaffold records for Acme Tech Inc.:
1. Deletes 0-chunk, failed/pending duplicate agreement uploads.
2. Deletes duplicate null/empty financial metrics rows (retaining the latest).
3. Deletes sub-second duplicate write attempts for health scores and risk assessments.
4. Preserves all 3 completed agreements, all 124 document chunks, loan facility, and distinct historical scores.
5. Re-parents any orphaned FK references.
"""
import argparse
import asyncio
import sys
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql+asyncpg://covenexa_user:covenexa_pass@localhost:5432/covenexa"


async def run_cleanup(dry_run: bool = True) -> Dict[str, Any]:
    engine = create_async_engine(DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Fetch Acme Tech borrower ID
        res_b = await session.execute(
            text("SELECT id, company_name FROM borrowers WHERE LOWER(company_name) LIKE '%acme%'")
        )
        acme_row = res_b.mappings().first()
        if not acme_row:
            print("[INFO] Acme Tech Inc. borrower not found in DB.")
            return {}

        acme_id = acme_row["id"]
        print(f"[FOUND] Acme Tech Inc. Borrower ID: {acme_id}")

        # ── A. AGREEMENTS CLEANUP ──────────────────────────────────────────
        res_agreements = await session.execute(
            text("""
                SELECT a.id, a.upload_date, a.source_url, a.file_path,
                       (SELECT COUNT(*) FROM document_chunks dc WHERE dc.agreement_id = a.id) as chunk_count
                FROM agreements a
                JOIN loans l ON a.loan_id = l.id
                WHERE l.borrower_id = :b
                  AND a.processing_status = 'pending'
            """),
            {"b": acme_id}
        )
        pending_agreements = res_agreements.mappings().all()

        duplicate_agreement_ids = [ag["id"] for ag in pending_agreements if ag["chunk_count"] == 0]

        # Retained agreements
        res_retained_ag = await session.execute(
            text("""
                SELECT a.id, a.document_type, a.processing_status,
                       (SELECT COUNT(*) FROM document_chunks dc WHERE dc.agreement_id = a.id) as chunk_count
                FROM agreements a
                JOIN loans l ON a.loan_id = l.id
                WHERE l.borrower_id = :b
            """),
            {"b": acme_id}
        )
        all_acme_agreements = res_retained_ag.mappings().all()
        retained_agreements = [r for r in all_acme_agreements if r["id"] not in duplicate_agreement_ids]

        # ── B. FINANCIAL METRICS CLEANUP ────────────────────────────────────
        res_fin = await session.execute(
            text("""
                SELECT id, extracted_at, revenue, ebitda, leverage_ratio
                FROM financial_metrics
                WHERE borrower_id = :b
                  AND revenue IS NULL AND ebitda IS NULL AND total_debt IS NULL
                ORDER BY extracted_at DESC
            """),
            {"b": acme_id}
        )
        fin_rows = res_fin.mappings().all()
        duplicate_fin_ids = [r["id"] for r in fin_rows[1:]] if len(fin_rows) > 1 else []

        # ── C. HEALTH SCORES CLEANUP ───────────────────────────────────────
        res_scores = await session.execute(
            text("""
                SELECT id, score, calculated_at
                FROM borrower_health_scores
                WHERE borrower_id = :b
                ORDER BY calculated_at DESC
            """),
            {"b": acme_id}
        )
        score_rows = res_scores.mappings().all()

        duplicate_score_ids = []
        seen_stamps = []
        for s in score_rows:
            ts_str = s["calculated_at"].strftime("%Y-%m-%d %H:%M:%S")
            key = (ts_str, float(s["score"]))
            if key in seen_stamps:
                duplicate_score_ids.append(s["id"])
            else:
                seen_stamps.append(key)

        # ── D. RISK ASSESSMENTS CLEANUP ─────────────────────────────────────
        res_assess = await session.execute(
            text("""
                SELECT id, default_probability, assessed_at
                FROM risk_assessments
                WHERE borrower_id = :b
                ORDER BY assessed_at DESC
            """),
            {"b": acme_id}
        )
        assess_rows = res_assess.mappings().all()

        duplicate_assess_ids = []
        seen_assess_stamps = []
        for r in assess_rows:
            ts_str = r["assessed_at"].strftime("%Y-%m-%d %H:%M:%S")
            key = (ts_str, float(r["default_probability"]))
            if key in seen_assess_stamps:
                duplicate_assess_ids.append(r["id"])
            else:
                seen_assess_stamps.append(key)

        # Print Summary
        print(f"\n--- CLEANUP PLAN SUMMARY ({'DRY RUN' if dry_run else 'EXECUTING'}) ---")
        print(f"Duplicate Pending Agreements to Delete ({len(duplicate_agreement_ids)}): {duplicate_agreement_ids}")
        print(f"Retained Completed Agreements ({len(retained_agreements)}): {[r['id'] for r in retained_agreements]}")
        print(f"Duplicate Financial Metrics to Delete ({len(duplicate_fin_ids)}): {duplicate_fin_ids}")
        print(f"Duplicate Health Scores to Delete ({len(duplicate_score_ids)}): {duplicate_score_ids}")
        print(f"Duplicate Risk Assessments to Delete ({len(duplicate_assess_ids)}): {duplicate_assess_ids}")

        if not dry_run:
            for ag_id in duplicate_agreement_ids:
                await session.execute(
                    text("UPDATE loans SET agreement_id = NULL WHERE agreement_id = :id"),
                    {"id": ag_id}
                )
                await session.execute(
                    text("DELETE FROM agreements WHERE id = :id"),
                    {"id": ag_id}
                )

            for fin_id in duplicate_fin_ids:
                await session.execute(
                    text("DELETE FROM financial_metrics WHERE id = :id"),
                    {"id": fin_id}
                )

            for score_id in duplicate_score_ids:
                await session.execute(
                    text("DELETE FROM borrower_health_scores WHERE id = :id"),
                    {"id": score_id}
                )

            for assess_id in duplicate_assess_ids:
                await session.execute(
                    text("DELETE FROM risk_assessments WHERE id = :id"),
                    {"id": assess_id}
                )

            # Connect Acme loan to its latest completed agreement if null
            res_loan = await session.execute(
                text("SELECT id, agreement_id FROM loans WHERE borrower_id = :b"),
                {"b": acme_id}
            )
            loan_row = res_loan.mappings().first()
            if loan_row and not loan_row["agreement_id"] and retained_agreements:
                latest_ag_id = retained_agreements[0]["id"]
                await session.execute(
                    text("UPDATE loans SET agreement_id = :aid WHERE id = :lid"),
                    {"aid": latest_ag_id, "lid": loan_row["id"]}
                )

            await session.commit()
            print("\n[SUCCESS] Cleanup committed successfully.")

    await engine.dispose()
    return {
        "agreements_deleted": len(duplicate_agreement_ids),
        "fin_metrics_deleted": len(duplicate_fin_ids),
        "scores_deleted": len(duplicate_score_ids),
        "risk_assessments_deleted": len(duplicate_assess_ids),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean duplicate records for Acme Tech Inc.")
    parser.add_argument("--commit", action="store_true", help="Execute deletion (default is dry-run)")
    args = parser.parse_args()

    asyncio.run(run_cleanup(dry_run=not args.commit))
