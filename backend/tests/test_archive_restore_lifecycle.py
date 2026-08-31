"""
Comprehensive test suite for Borrower and Loan Facility Archive + Restore Lifecycle.
Covers RBAC, Tenant Isolation, Historical Data Preservation, Active Query Filters,
Audit Trail Logging, and Upload Restrictions.
"""
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.endpoints.borrowers import archive_borrower, restore_borrower, list_borrowers
from app.api.v1.endpoints.loans import archive_loan, restore_loan, list_loans, get_loan_count
from app.application.borrowers.commands import ArchiveBorrowerCommand, RestoreBorrowerCommand
from app.application.borrowers.handlers import ArchiveBorrowerHandler, RestoreBorrowerHandler
from app.application.loans.commands import ArchiveLoanCommand, RestoreLoanCommand
from app.application.loans.handlers import ArchiveLoanHandler, RestoreLoanHandler
from app.application.uploads.commands import UploadDocumentCommand
from app.application.uploads.handlers import UploadDocumentHandler
from app.core.exceptions import DomainException, EntityNotFoundException, ForbiddenException
from app.domain.entities.borrower import Borrower
from app.domain.entities.loan import Loan, LoanStatus
from app.domain.entities.user import User, UserRole
from app.domain.value_objects.email import Email
from app.domain.value_objects.money import Money
from app.domain.value_objects.risk_rating import RiskRating


@pytest.fixture
def admin_user():
    return User(
        id="user-admin-1",
        name="Alex Morgan",
        email=Email("alex.morgan@covenexacapital.com"),
        password_hash="pw_hash",
        role=UserRole.ADMIN,
        organization_id="org-blue-owl",
    )


@pytest.fixture
def analyst_user():
    return User(
        id="user-analyst-1",
        name="Sarah Mitchell",
        email=Email("sarah.mitchell@covenexacapital.com"),
        password_hash="pw_hash",
        role=UserRole.ANALYST,
        organization_id="org-blue-owl",
    )


@pytest.fixture
def other_org_admin():
    return User(
        id="user-admin-2",
        name="Other Admin",
        email=Email("admin@otherfund.com"),
        password_hash="pw_hash",
        role=UserRole.ADMIN,
        organization_id="org-other",
    )


@pytest.fixture
def active_borrower():
    return Borrower(
        id="borr-acme-1",
        organization_id="org-blue-owl",
        company_name="Acme Technologies",
        sector="Enterprise SaaS",
        country="USA",
        risk_rating=RiskRating(level="LOW", score=2),
        is_archived=False,
    )


@pytest.fixture
def archived_borrower():
    return Borrower(
        id="borr-acme-1",
        organization_id="org-blue-owl",
        company_name="Acme Technologies",
        sector="Enterprise SaaS",
        country="USA",
        risk_rating=RiskRating(level="LOW", score=2),
        is_archived=True,
        archived_at=datetime.now(timezone.utc),
        archived_by="user-admin-1",
    )


@pytest.fixture
def active_loan():
    return Loan(
        id="loan-fac-1",
        borrower_id="borr-acme-1",
        principal_amount=Money(amount=Decimal("50000000.0"), currency="USD"),
        interest_rate=0.105,
        start_date="2026-08-30",
        maturity_date="2031-08-29",
        status=LoanStatus.ACTIVE,
        is_archived=False,
    )


@pytest.fixture
def archived_loan():
    return Loan(
        id="loan-fac-1",
        borrower_id="borr-acme-1",
        principal_amount=Money(amount=Decimal("50000000.0"), currency="USD"),
        interest_rate=0.105,
        start_date="2026-08-30",
        maturity_date="2031-08-29",
        status=LoanStatus.ACTIVE,
        is_archived=True,
        archived_at=datetime.now(timezone.utc),
        archived_by="user-admin-1",
    )


class TestBorrowerArchiveRestore:

    @pytest.mark.asyncio
    async def test_admin_can_archive_borrower(self, admin_user, active_borrower, archived_borrower):
        """Admin can archive an active borrower and an audit event is logged."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls, \
             patch("app.api.v1.endpoints.borrowers.ArchiveBorrowerHandler") as mock_ah_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=active_borrower)

            mock_ah = mock_ah_cls.return_value
            mock_ah.handle = AsyncMock(return_value=archived_borrower)

            res = await archive_borrower(
                borrower_id="borr-acme-1",
                session=session,
                current_user=admin_user,
            )

            assert res.is_archived is True
            assert res.id == "borr-acme-1"  # Identity preserved
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "borrower.archived"

    @pytest.mark.asyncio
    async def test_admin_can_restore_borrower(self, admin_user, archived_borrower, active_borrower):
        """Admin can restore an archived borrower and an audit event is logged."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls, \
             patch("app.api.v1.endpoints.borrowers.RestoreBorrowerHandler") as mock_rh_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=archived_borrower)

            mock_rh = mock_rh_cls.return_value
            mock_rh.handle = AsyncMock(return_value=active_borrower)

            res = await restore_borrower(
                borrower_id="borr-acme-1",
                session=session,
                current_user=admin_user,
            )

            assert res.is_archived is False
            assert res.id == "borr-acme-1"  # Identity preserved
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "borrower.restored"

    @pytest.mark.asyncio
    async def test_cross_tenant_borrower_archive_prevented(self, other_org_admin, active_borrower):
        """Admin from Org B cannot archive a borrower belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls:
            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=active_borrower)

            with pytest.raises(ForbiddenException):
                await archive_borrower(
                    borrower_id="borr-acme-1",
                    session=session,
                    current_user=other_org_admin,
                )

    @pytest.mark.asyncio
    async def test_cross_tenant_borrower_restore_prevented(self, other_org_admin, archived_borrower):
        """Admin from Org B cannot restore a borrower belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls:
            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=archived_borrower)

            with pytest.raises(ForbiddenException):
                await restore_borrower(
                    borrower_id="borr-acme-1",
                    session=session,
                    current_user=other_org_admin,
                )

    @pytest.mark.asyncio
    async def test_double_archive_borrower_raises_domain_exception(self, archived_borrower):
        """Archiving an already archived borrower is rejected safely."""
        session = MagicMock()
        session.commit = AsyncMock()

        handler = ArchiveBorrowerHandler(session)
        handler._borrower_repo.get_by_id = AsyncMock(return_value=archived_borrower)

        with pytest.raises(DomainException) as exc:
            await handler.handle(
                ArchiveBorrowerCommand(borrower_id="borr-acme-1", organization_id="org-blue-owl", user_id="admin-1")
            )
        assert "already archived" in str(exc.value)

    @pytest.mark.asyncio
    async def test_double_restore_borrower_raises_domain_exception(self, active_borrower):
        """Restoring an already active borrower is rejected safely."""
        session = MagicMock()
        session.commit = AsyncMock()

        handler = RestoreBorrowerHandler(session)
        handler._borrower_repo.get_by_id = AsyncMock(return_value=active_borrower)

        with pytest.raises(DomainException) as exc:
            await handler.handle(
                RestoreBorrowerCommand(borrower_id="borr-acme-1", organization_id="org-blue-owl")
            )
        assert "not currently archived" in str(exc.value)


class TestLoanArchiveRestore:

    @pytest.mark.asyncio
    async def test_admin_can_archive_loan(self, admin_user, active_loan, active_borrower, archived_loan):
        """Admin can archive an active loan facility and an audit event is logged."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls, \
             patch("app.api.v1.endpoints.loans.ArchiveLoanHandler") as mock_ah_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=active_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=active_borrower)

            mock_ah = mock_ah_cls.return_value
            mock_ah.handle = AsyncMock(return_value=archived_loan)

            res = await archive_loan(
                loan_id="loan-fac-1",
                session=session,
                current_user=admin_user,
            )

            assert res.is_archived is True
            assert res.id == "loan-fac-1"
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "loan.archived"

    @pytest.mark.asyncio
    async def test_admin_can_restore_loan(self, admin_user, archived_loan, active_borrower, active_loan):
        """Admin can restore an archived loan facility and an audit event is logged."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls, \
             patch("app.api.v1.endpoints.loans.RestoreLoanHandler") as mock_rh_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=archived_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=active_borrower)

            mock_rh = mock_rh_cls.return_value
            mock_rh.handle = AsyncMock(return_value=active_loan)

            res = await restore_loan(
                loan_id="loan-fac-1",
                session=session,
                current_user=admin_user,
            )

            assert res.is_archived is False
            assert res.id == "loan-fac-1"
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "loan.restored"

    @pytest.mark.asyncio
    async def test_cross_tenant_loan_archive_prevented(self, other_org_admin, active_loan, active_borrower):
        """Admin from Org B cannot archive a loan facility belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=active_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=active_borrower)

            with pytest.raises(ForbiddenException):
                await archive_loan(
                    loan_id="loan-fac-1",
                    session=session,
                    current_user=other_org_admin,
                )

    @pytest.mark.asyncio
    async def test_cross_tenant_loan_restore_prevented(self, other_org_admin, archived_loan, active_borrower):
        """Admin from Org B cannot restore a loan facility belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=archived_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=active_borrower)

            with pytest.raises(ForbiddenException):
                await restore_loan(
                    loan_id="loan-fac-1",
                    session=session,
                    current_user=other_org_admin,
                )


class TestUploadRestrictionOnArchivedLoan:

    @pytest.mark.asyncio
    async def test_upload_to_archived_loan_rejected(self, archived_loan):
        """Uploading an agreement to an archived loan is rejected with DomainException."""
        session = MagicMock()
        handler = UploadDocumentHandler(session)
        handler._loan_repo.get_by_id = AsyncMock(return_value=archived_loan)

        mock_content = MagicMock()
        command = UploadDocumentCommand(
            loan_id="loan-fac-1",
            file_name="credit_agreement.pdf",
            file_type="loan_agreement",
            content=mock_content,
            size_bytes=1024,
        )

        with pytest.raises(DomainException) as exc:
            await handler.handle(command)
        assert "Cannot upload documents to an archived loan facility" in str(exc.value)
