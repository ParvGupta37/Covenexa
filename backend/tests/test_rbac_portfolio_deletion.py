"""
Comprehensive Tests for RBAC Enforcement, Borrower Deletion, Loan Facility Deletion,
Tenant Isolation, and Last-Admin Protection.
"""
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.endpoints.borrowers import delete_borrower
from app.api.v1.endpoints.loans import delete_loan
from app.api.v1.endpoints.organizations import update_member_role, remove_member
from app.application.borrowers.commands import DeleteBorrowerCommand
from app.application.borrowers.handlers import DeleteBorrowerHandler
from app.application.loans.commands import DeleteLoanCommand
from app.application.loans.handlers import DeleteLoanHandler
from app.core.exceptions import EntityNotFoundException, ForbiddenException
from app.core.schemas.auth import MemberRoleUpdateSchema
from app.domain.entities.borrower import Borrower
from app.domain.entities.loan import Loan, LoanStatus
from app.domain.entities.user import User, UserRole
from app.domain.value_objects.email import Email
from app.domain.value_objects.money import Money
from app.domain.value_objects.risk_rating import RiskRating


@pytest.fixture
def admin_user():
    return User(
        id="admin-1",
        name="Alex Morgan",
        email=Email("alex.morgan@covenexacapital.com"),
        password_hash="pw_hash",
        role=UserRole.ADMIN,
        organization_id="org-blue-owl",
    )


@pytest.fixture
def analyst_user():
    return User(
        id="analyst-1",
        name="Sarah Mitchell",
        email=Email("sarah.mitchell@covenexacapital.com"),
        password_hash="pw_hash",
        role=UserRole.ANALYST,
        organization_id="org-blue-owl",
    )


@pytest.fixture
def other_org_admin():
    return User(
        id="admin-2",
        name="Other Admin",
        email=Email("admin@otherfund.com"),
        password_hash="pw_hash",
        role=UserRole.ADMIN,
        organization_id="org-other",
    )


@pytest.fixture
def sample_borrower():
    return Borrower(
        id="borr-1",
        organization_id="org-blue-owl",
        company_name="Apex Industrial Technologies",
        sector="Technology",
        country="USA",
        risk_rating=RiskRating(level="LOW", score=2),
    )


@pytest.fixture
def sample_loan():
    return Loan(
        id="loan-1",
        borrower_id="borr-1",
        principal_amount=Money(amount=Decimal("50000000.0"), currency="USD"),
        interest_rate=0.105,
        start_date="2026-08-30",
        maturity_date="2031-08-29",
        status=LoanStatus.ACTIVE,
    )


class TestBorrowerDeletion:

    @pytest.mark.asyncio
    async def test_admin_can_delete_borrower(self, admin_user, sample_borrower):
        """Organization Admin can successfully delete a borrower in their organization."""
        session = MagicMock()
        session.commit = AsyncMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls, \
             patch("app.api.v1.endpoints.borrowers.DeleteBorrowerHandler") as mock_dh_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=sample_borrower)

            mock_dh = mock_dh_cls.return_value
            mock_dh.handle = AsyncMock(return_value=True)

            await delete_borrower(
                borrower_id="borr-1",
                session=session,
                current_user=admin_user,
            )

            mock_dh.handle.assert_awaited_once()
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "borrower.deleted"
            assert mock_audit.await_args.kwargs["resource_id"] == "borr-1"

    @pytest.mark.asyncio
    async def test_cross_tenant_borrower_deletion_prevented(self, other_org_admin, sample_borrower):
        """Admin from Org B cannot delete a borrower belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.borrowers.BorrowerQueryHandler") as mock_qh_cls:
            mock_qh = mock_qh_cls.return_value
            mock_qh.get_by_id = AsyncMock(return_value=sample_borrower)

            with pytest.raises(ForbiddenException):
                await delete_borrower(
                    borrower_id="borr-1",
                    session=session,
                    current_user=other_org_admin,
                )

    @pytest.mark.asyncio
    async def test_delete_borrower_handler_deletes_and_commits(self, sample_borrower):
        """Handler verifies borrower ownership and executes repository deletion."""
        session = MagicMock()
        session.commit = AsyncMock()

        handler = DeleteBorrowerHandler(session)
        handler._borrower_repo.get_by_id = AsyncMock(return_value=sample_borrower)
        handler._borrower_repo.delete = AsyncMock(return_value=True)

        res = await handler.handle(DeleteBorrowerCommand(borrower_id="borr-1", organization_id="org-blue-owl"))
        assert res is True
        handler._borrower_repo.delete.assert_awaited_once_with("borr-1")
        session.commit.assert_awaited_once()


class TestLoanFacilityDeletion:

    @pytest.mark.asyncio
    async def test_admin_can_delete_loan(self, admin_user, sample_loan, sample_borrower):
        """Organization Admin can successfully delete a loan facility."""
        session = MagicMock()
        session.commit = AsyncMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls, \
             patch("app.api.v1.endpoints.loans.DeleteLoanHandler") as mock_dl_cls, \
             patch("app.api.v1.endpoints.audit.log_audit_event", new_callable=AsyncMock) as mock_audit:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=sample_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=sample_borrower)

            mock_dl = mock_dl_cls.return_value
            mock_dl.handle = AsyncMock(return_value=True)

            await delete_loan(
                loan_id="loan-1",
                session=session,
                current_user=admin_user,
            )

            mock_dl.handle.assert_awaited_once()
            mock_audit.assert_awaited_once()
            assert mock_audit.await_args.kwargs["action"] == "loan.deleted"
            assert mock_audit.await_args.kwargs["resource_id"] == "loan-1"

    @pytest.mark.asyncio
    async def test_cross_tenant_loan_deletion_prevented(self, other_org_admin, sample_loan, sample_borrower):
        """Admin from Org B cannot delete a loan belonging to Org A."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.loans.LoanQueryHandler") as mock_lq_cls, \
             patch("app.api.v1.endpoints.loans.BorrowerRepositoryImpl") as mock_br_cls:

            mock_lq = mock_lq_cls.return_value
            mock_lq.get_by_id = AsyncMock(return_value=sample_loan)

            mock_br = mock_br_cls.return_value
            mock_br.get_by_id = AsyncMock(return_value=sample_borrower)

            with pytest.raises(ForbiddenException):
                await delete_loan(
                    loan_id="loan-1",
                    session=session,
                    current_user=other_org_admin,
                )

    @pytest.mark.asyncio
    async def test_delete_loan_handler_deletes_and_commits(self, sample_loan, sample_borrower):
        """Handler verifies borrower ownership and executes repository deletion."""
        session = MagicMock()
        session.commit = AsyncMock()

        handler = DeleteLoanHandler(session)
        handler._loan_repo.get_by_id = AsyncMock(return_value=sample_loan)
        handler._borrower_repo.get_by_id = AsyncMock(return_value=sample_borrower)
        handler._loan_repo.delete = AsyncMock(return_value=True)

        res = await handler.handle(DeleteLoanCommand(loan_id="loan-1", organization_id="org-blue-owl"))
        assert res is True
        handler._loan_repo.delete.assert_awaited_once_with("loan-1")
        session.commit.assert_awaited_once()


class TestLastAdminProtection:

    @pytest.mark.asyncio
    async def test_demoting_sole_admin_rejected(self, admin_user):
        """Cannot demote the last administrator in an organization."""
        session = MagicMock()

        with patch("app.api.v1.endpoints.organizations.UserRepositoryImpl") as mock_ur_cls:
            mock_ur = mock_ur_cls.return_value
            mock_ur.get_by_id = AsyncMock(return_value=admin_user)
            mock_ur.get_by_organization_id = AsyncMock(return_value=[admin_user])

            payload = MemberRoleUpdateSchema(role="ANALYST")

            with pytest.raises(HTTPException) as exc:
                await update_member_role(
                    org_id="org-blue-owl",
                    user_id="admin-1",
                    payload=payload,
                    session=session,
                    current_user=admin_user,
                )

            assert exc.value.status_code == 400
            assert "Cannot demote the last Administrator" in exc.value.detail

    @pytest.mark.asyncio
    async def test_removing_sole_admin_rejected(self, admin_user):
        """Cannot remove the last administrator in an organization."""
        session = MagicMock()

        second_admin = User(
            id="admin-2",
            name="Second Admin",
            email=Email("admin2@blueowl.com"),
            password_hash="pw",
            role=UserRole.ADMIN,
            organization_id="org-blue-owl",
        )

        with patch("app.api.v1.endpoints.organizations.UserRepositoryImpl") as mock_ur_cls:
            mock_ur = mock_ur_cls.return_value
            mock_ur.get_by_id = AsyncMock(return_value=second_admin)
            # Only 1 admin in org
            mock_ur.get_by_organization_id = AsyncMock(return_value=[second_admin])

            with pytest.raises(HTTPException) as exc:
                await remove_member(
                    org_id="org-blue-owl",
                    user_id="admin-2",
                    session=session,
                    current_user=admin_user,
                )

            assert exc.value.status_code == 400
            assert "Cannot remove the last Administrator" in exc.value.detail
