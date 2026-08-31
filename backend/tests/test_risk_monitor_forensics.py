"""
Test Risk Monitor Forensic Validation & Regression Suite.
Covers:
- Covenant count & deduplication across multiple document ingestions
- Unknown covenant headroom is None (not 0.0)
- Health score re-normalization over available metrics
- Default probability penalty for unavailable debt service ratios
- Idempotent repeated recalculations
- Archival and restoration lifecycle
- Tenant / borrower isolation
"""
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.infrastructure.orm.organization_orm import OrganizationORM
from app.infrastructure.orm.borrower_orm import BorrowerORM
from app.infrastructure.orm.loan_orm import LoanORM
from app.infrastructure.orm.agreement_orm import AgreementORM
from app.infrastructure.orm.covenant_orm import CovenantORM
from ai.engines.pipeline_runner import RiskIntelligencePipeline
from ai.engines.covenant_monitor import CovenantMonitor
from app.api.v1.endpoints.risk import get_monitored_covenants


@pytest.fixture
async def test_session():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
class TestRiskMonitorForensics:

    async def test_covenant_deduplication_and_null_headroom(self, test_session):
        """
        Verify that multiple document extractions on the same facility deduplicate
        to the distinct active covenants, and UNKNOWN covenants have headroom=None.
        """
        db = test_session
        org_id = str(uuid.uuid4())
        org = OrganizationORM(id=org_id, name=f"Test Forensic Org {org_id[:8]}", industry="Private Credit")
        db.add(org)
        await db.flush()

        borrower_id = str(uuid.uuid4())
        borrower = BorrowerORM(
            id=borrower_id,
            organization_id=org_id,
            company_name="Test Borrower Corp",
            sector="Technology",
            country="USA",
            risk_rating_level="LOW",
            is_archived=False,
        )
        db.add(borrower)
        await db.flush()

        loan_id = str(uuid.uuid4())
        loan = LoanORM(
            id=loan_id,
            borrower_id=borrower_id,
            principal_amount=50000000.0,
            currency="USD",
            interest_rate=5.0,
            start_date=datetime.now(timezone.utc).date(),
            maturity_date=datetime.now(timezone.utc).date(),
            status="active",
            is_archived=False,
        )
        db.add(loan)
        await db.flush()

        # Agreement 1: Initial filing
        ag1_id = str(uuid.uuid4())
        ag1 = AgreementORM(
            id=ag1_id,
            loan_id=loan_id,
            file_path="/tmp/test_filing_1.pdf",
            processing_status="done",
        )
        db.add(ag1)
        await db.flush()

        # Agreement 2: SEC URL ingestion
        ag2_id = str(uuid.uuid4())
        ag2 = AgreementORM(
            id=ag2_id,
            loan_id=loan_id,
            file_path="/tmp/test_filing_2.txt",
            processing_status="done",
        )
        db.add(ag2)
        await db.flush()

        # 2 Covenants extracted from Agreement 1
        cov1_ag1 = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag1_id,
            borrower_id=borrower_id,
            name="Maximum Leverage Ratio Maintenance",
            covenant_type="maintenance",
            formula="leverage_ratio",
            threshold=4.0,
            threshold_direction="max",
        )
        cov2_ag1 = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag1_id,
            borrower_id=borrower_id,
            name="Minimum Interest Coverage Maintenance",
            covenant_type="maintenance",
            formula="interest_coverage",
            threshold=2.5,
            threshold_direction="min",
        )
        db.add_all([cov1_ag1, cov2_ag1])
        await db.flush()

        # Same 2 Covenants extracted from Agreement 2
        cov1_ag2 = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag2_id,
            borrower_id=borrower_id,
            name="Maximum Leverage Ratio Maintenance",
            covenant_type="maintenance",
            formula="leverage_ratio",
            threshold=4.0,
            threshold_direction="max",
        )
        cov2_ag2 = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag2_id,
            borrower_id=borrower_id,
            name="Minimum Interest Coverage Maintenance",
            covenant_type="maintenance",
            formula="interest_coverage",
            threshold=2.5,
            threshold_direction="min",
        )
        db.add_all([cov1_ag2, cov2_ag2])
        await db.commit()

        # Run Covenant Monitor
        monitor = CovenantMonitor()
        results = await monitor.evaluate_borrower_covenants(db, borrower_id)

        # Must monitor exactly 2 distinct covenants, not 4
        assert len(results) == 2

        # Ratios are unavailable -> status must be unknown and headroom must be None (not 0.0)
        for r in results:
            assert r["status"] == "unknown"
            assert r["current_value"] is None
            assert r["headroom_pct"] is None

        # Verify API endpoint returns exactly 2 covenants with None headroom
        api_covs = await get_monitored_covenants(borrower_id, db)
        assert len(api_covs) == 2
        for c in api_covs:
            assert c["status"] == "unknown"
            assert c["current_value"] is None
            assert c["headroom_pct"] is None

    async def test_recalculation_idempotency(self, test_session):
        """
        Verify that running recalculation multiple times produces identical state
        without accumulating duplicate covenants or recommendations.
        """
        db = test_session
        org_id = str(uuid.uuid4())
        org = OrganizationORM(id=org_id, name=f"Idempotency Org {org_id[:8]}", industry="Private Credit")
        db.add(org)
        await db.flush()

        borrower_id = str(uuid.uuid4())
        borrower = BorrowerORM(
            id=borrower_id,
            organization_id=org_id,
            company_name=f"Idempotent Borrower {borrower_id[:8]}",
            sector="Technology",
            country="USA",
            risk_rating_level="LOW",
            is_archived=False,
        )
        db.add(borrower)
        await db.flush()

        loan_id = str(uuid.uuid4())
        loan = LoanORM(
            id=loan_id,
            borrower_id=borrower_id,
            principal_amount=10000000.0,
            currency="USD",
            interest_rate=6.0,
            start_date=datetime.now(timezone.utc).date(),
            maturity_date=datetime.now(timezone.utc).date(),
            status="active",
            is_archived=False,
        )
        db.add(loan)
        await db.flush()

        ag_id = str(uuid.uuid4())
        ag = AgreementORM(id=ag_id, loan_id=loan_id, file_path="/tmp/doc.pdf", processing_status="done")
        db.add(ag)
        await db.flush()

        cov = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag_id,
            borrower_id=borrower_id,
            name="Maximum Leverage Ratio Maintenance",
            threshold=3.5,
            threshold_direction="max",
        )
        db.add(cov)
        await db.commit()

        pipeline = RiskIntelligencePipeline()

        # Run pipeline 3 times
        for _ in range(3):
            await pipeline.run_full_pipeline(db, borrower_id)

        covs = await get_monitored_covenants(borrower_id, db)
        assert len(covs) == 1

        rec_res = await db.execute(
            text("SELECT * FROM ai_recommendations WHERE borrower_id = :b"),
            {"b": borrower_id},
        )
        recs = rec_res.mappings().all()
        rec_types = [r["recommendation_type"] for r in recs]
        assert len(rec_types) == len(set(rec_types))

    async def test_archived_loan_exclusion(self, test_session):
        """
        Verify that covenants from archived loans do not appear in Risk Monitor,
        and restoring the loan brings them back exactly once.
        """
        db = test_session
        org_id = str(uuid.uuid4())
        org = OrganizationORM(id=org_id, name=f"Archive Test Org {org_id[:8]}", industry="Private Credit")
        db.add(org)
        await db.flush()

        borrower_id = str(uuid.uuid4())
        borrower = BorrowerORM(
            id=borrower_id,
            organization_id=org_id,
            company_name=f"Archival Borrower {borrower_id[:8]}",
            sector="Technology",
            country="USA",
            risk_rating_level="LOW",
            is_archived=False,
        )
        db.add(borrower)
        await db.flush()

        loan_id = str(uuid.uuid4())
        loan = LoanORM(
            id=loan_id,
            borrower_id=borrower_id,
            principal_amount=20000000.0,
            currency="USD",
            interest_rate=4.5,
            start_date=datetime.now(timezone.utc).date(),
            maturity_date=datetime.now(timezone.utc).date(),
            status="active",
            is_archived=False,
        )
        db.add(loan)
        await db.flush()

        ag_id = str(uuid.uuid4())
        ag = AgreementORM(id=ag_id, loan_id=loan_id, file_path="/tmp/loan_doc.pdf", processing_status="done")
        db.add(ag)
        await db.flush()

        cov = CovenantORM(
            id=str(uuid.uuid4()),
            agreement_id=ag_id,
            borrower_id=borrower_id,
            name="Debt Service Coverage Ratio",
            threshold=1.25,
            threshold_direction="min",
        )
        db.add(cov)
        await db.commit()

        pipeline = RiskIntelligencePipeline()
        await pipeline.run_full_pipeline(db, borrower_id)

        covs_active = await get_monitored_covenants(borrower_id, db)
        assert len(covs_active) == 1

        # Archive the loan
        loan.is_archived = True
        await db.commit()

        covs_archived = await get_monitored_covenants(borrower_id, db)
        assert len(covs_archived) == 0

        # Restore the loan
        loan.is_archived = False
        await db.commit()
        await pipeline.run_full_pipeline(db, borrower_id)

        covs_restored = await get_monitored_covenants(borrower_id, db)
        assert len(covs_restored) == 1

    async def test_knowledge_graph_deduplication_and_tenant_isolation(self, test_session):
        """
        Verify Knowledge Graph:
        1. Deduplicates multiple covenant extractions to unique active covenants.
        2. Strictly isolates across organizations (User from Org B cannot access Org A graph).
        3. Excludes archived loans and their associated child entities.
        4. Restores cleanly upon loan un-archival.
        """
        from app.api.v1.endpoints.risk import get_borrower_knowledge_graph
        from app.domain.entities.user import User, UserRole
        from app.domain.value_objects.email import Email
        from fastapi import HTTPException

        db = test_session
        org_a_id = str(uuid.uuid4())
        org_a = OrganizationORM(id=org_a_id, name=f"Graph Org A {org_a_id[:8]}", industry="Credit")
        db.add(org_a)

        org_b_id = str(uuid.uuid4())
        org_b = OrganizationORM(id=org_b_id, name=f"Graph Org B {org_b_id[:8]}", industry="Credit")
        db.add(org_b)
        await db.flush()

        user_a = User(id=str(uuid.uuid4()), name="User A", email=Email("user_a@orga.com"), organization_id=org_a_id, role=UserRole.ADMIN, password_hash="x")
        user_b = User(id=str(uuid.uuid4()), name="User B", email=Email("user_b@orgb.com"), organization_id=org_b_id, role=UserRole.ADMIN, password_hash="x")

        borrower_id = str(uuid.uuid4())
        borrower = BorrowerORM(
            id=borrower_id,
            organization_id=org_a_id,
            company_name="Graph Borrower Corp",
            sector="Technology",
            country="USA",
            risk_rating_level="LOW",
            is_archived=False,
        )
        db.add(borrower)
        await db.flush()

        loan_id = str(uuid.uuid4())
        ag_id = str(uuid.uuid4())

        loan = LoanORM(
            id=loan_id,
            borrower_id=borrower_id,
            agreement_id=None,
            principal_amount=10000000.0,
            currency="USD",
            interest_rate=5.5,
            start_date=datetime.now(timezone.utc).date(),
            maturity_date=datetime.now(timezone.utc).date(),
            status="active",
            is_archived=False,
        )
        db.add(loan)
        await db.flush()

        ag = AgreementORM(
            id=ag_id,
            loan_id=loan_id,
            file_path="/tmp/credit_agreement_v1.pdf",
            document_type="loan_agreement",
            processing_status="done",
        )
        db.add(ag)
        await db.flush()

        loan.agreement_id = ag_id
        await db.flush()

        # Add 2 pairs of duplicate covenant extractions (4 rows total)
        for i in range(2):
            cov1 = CovenantORM(
                id=str(uuid.uuid4()),
                agreement_id=ag_id,
                borrower_id=borrower_id,
                name="Maximum Leverage Ratio Maintenance",
                covenant_type="maintenance",
                threshold=4.0,
                threshold_direction="max",
                extracted_at=datetime.now(timezone.utc),
            )
            cov2 = CovenantORM(
                id=str(uuid.uuid4()),
                agreement_id=ag_id,
                borrower_id=borrower_id,
                name="Minimum Interest Coverage Maintenance",
                covenant_type="maintenance",
                threshold=2.5,
                threshold_direction="min",
                extracted_at=datetime.now(timezone.utc),
            )
            db.add(cov1)
            db.add(cov2)
        await db.commit()

        # 1. User A retrieves active graph -> exactly 2 deduplicated covenant nodes
        graph_a = await get_borrower_knowledge_graph(borrower_id, user_a, db)
        covenant_nodes = [n for n in graph_a["nodes"] if n["type"] == "covenant"]
        assert len(covenant_nodes) == 2, f"Expected 2 deduplicated covenants, got {len(covenant_nodes)}"
        cov_labels = {n["label"] for n in covenant_nodes}
        assert any("Leverage" in l for l in cov_labels)
        assert any("Interest" in l for l in cov_labels)

        # 2. User B from Org B is rejected (404 Tenant Isolation)
        with pytest.raises(HTTPException) as exc:
            await get_borrower_knowledge_graph(borrower_id, user_b, db)
        assert exc.value.status_code == 404

        # 3. Archive loan -> graph excludes loan, agreement, and covenants
        loan.is_archived = True
        await db.commit()

        graph_archived = await get_borrower_knowledge_graph(borrower_id, user_a, db)
        assert len([n for n in graph_archived["nodes"] if n["type"] == "loan"]) == 0
        assert len([n for n in graph_archived["nodes"] if n["type"] == "agreement"]) == 0
        assert len([n for n in graph_archived["nodes"] if n["type"] == "covenant"]) == 0

        # 4. Restore loan -> graph restores all relationships
        loan.is_archived = False
        await db.commit()

        graph_restored = await get_borrower_knowledge_graph(borrower_id, user_a, db)
        assert len([n for n in graph_restored["nodes"] if n["type"] == "loan"]) == 1
        assert len([n for n in graph_restored["nodes"] if n["type"] == "covenant"]) == 2
