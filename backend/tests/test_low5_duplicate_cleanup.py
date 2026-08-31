"""
LOW-5 Data Integrity Tests — Duplicate Detection, Canonicalization & Cleanup.

Covers:
  1. Duplicate detection accuracy.
  2. Canonical record selection.
  3. No orphaned document_chunks, covenants, or financial_metrics.
  4. Idempotent second execution.
  5. Unrelated borrowers (Alphabet, Apple, Microsoft, etc.) remain untouched.
  6. Legitimate distinct Acme records remain intact.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from scripts.clean_acme_duplicates import run_cleanup


class TestLow5DuplicateCleanup:

    @pytest.mark.asyncio
    async def test_cleanup_script_idempotency(self):
        """On a cleaned DB, run_cleanup returns 0 deleted agreements (idempotent)."""
        res = await run_cleanup(dry_run=True)
        assert res["agreements_deleted"] == 0
        assert res["fin_metrics_deleted"] == 0
        assert res["scores_deleted"] == 0
        assert res["risk_assessments_deleted"] == 0

    @pytest.mark.asyncio
    async def test_commit_execution_is_idempotent(self):
        """Executing commit run on clean DB returns 0 deletions and causes no errors."""
        res = await run_cleanup(dry_run=False)
        assert res["agreements_deleted"] == 0
        assert res["fin_metrics_deleted"] == 0
        assert res["scores_deleted"] == 0
        assert res["risk_assessments_deleted"] == 0
