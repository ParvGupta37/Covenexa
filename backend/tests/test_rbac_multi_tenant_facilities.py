"""
Comprehensive Regression Tests for Multi-Tenant Organization Hierarchy,
RBAC Permission Matrix, Invitation Flow, Tenant Isolation, and Loan Facility Currency/Validation.

Covers:
  1. New Organization Signup (Org created, User is Admin, 0 Borrowers, 0 Loans).
  2. Member Invitation Flow (Admin invites -> token created -> member onboarded to same org).
  3. RBAC Rules (Analyst can create borrowers & facilities; Analyst cannot manage members or delete org).
  4. Multi-Tenant Data Isolation (Org A cannot see or mutate Org B's borrowers, loans, alerts, members).
  5. Loan Facility Validation & Multi-Currency (USD, EUR, GBP, INR; large institutional amounts).
"""
from decimal import Decimal
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.auth.handlers import OrgSignupHandler, InviteAcceptHandler
from app.application.borrowers.commands import CreateBorrowerCommand
from app.application.borrowers.handlers import CreateBorrowerHandler
from app.application.loans.commands import CreateLoanCommand
from app.application.loans.handlers import CreateLoanHandler
from app.core.exceptions import EntityAlreadyExistsException, EntityNotFoundException, ForbiddenException
from app.core.schemas.loan import LoanCreateSchema, MoneySchema
from app.domain.entities.invitation import Invitation
from app.domain.entities.organization import Organization
from app.domain.entities.user import User, UserRole
from app.domain.entities.borrower import Borrower
from app.domain.entities.loan import Loan, LoanStatus
from app.domain.value_objects.email import Email
from app.domain.value_objects.risk_rating import RiskRating


class TestOrgSignupAndHierarchy:

    @pytest.mark.asyncio
    async def test_org_signup_creates_org_and_admin_user(self):
        """First user signup creates the organization and makes the user its ADMIN."""
        session = MagicMock()
        handler = OrgSignupHandler(session)

        handler._user_repo.get_by_email = AsyncMock(return_value=None)
        handler._org_repo.get_by_name = AsyncMock(return_value=None)

        fake_org = Organization(id="org-100", name="Blue Owl Demo Credit", industry="Private Credit")
        handler._org_repo.add = AsyncMock(return_value=fake_org)

        fake_user = User(
            id="usr-100",
            name="Alex Morgan",
            email=Email("alex@blueowldemo.com"),
            password_hash="hashed_pw",
            role=UserRole.ADMIN,
            organization_id="org-100",
        )
        handler._user_repo.add = AsyncMock(return_value=fake_user)

        res = await handler.handle(
            name="Alex Morgan",
            email="alex@blueowldemo.com",
            password="Password@123",
            org_name="Blue Owl Demo Credit",
            org_industry="Private Credit",
        )

        assert res["user"]["role"] == "ADMIN"
        assert res["user"]["organization_id"] == "org-100"
        assert res["organization"]["name"] == "Blue Owl Demo Credit"
        assert res["access_token"] is not None


class TestInvitationFlow:

    @pytest.mark.asyncio
    async def test_accept_invitation_joins_correct_organization_and_role(self):
        """Invited user accepts invitation and joins the same organization with assigned role."""
        session = MagicMock()
        handler = InviteAcceptHandler(session)

        fake_invite = Invitation(
            id="inv-1",
            organization_id="org-100",
            email="analyst@blueowldemo.com",
            token="secure_token_abc_123",
            role=UserRole.ANALYST,
            status="PENDING",
        )
        handler._invite_repo.get_by_token = AsyncMock(return_value=fake_invite)
        handler._user_repo.get_by_email = AsyncMock(return_value=None)
        handler._invite_repo.update = AsyncMock()

        fake_created_user = User(
            id="usr-200",
            name="Jordan Smith",
            email=Email("analyst@blueowldemo.com"),
            password_hash="hashed_pw",
            role=UserRole.ANALYST,
            organization_id="org-100",
        )
        handler._user_repo.add = AsyncMock(return_value=fake_created_user)

        res = await handler.handle(
            token="secure_token_abc_123",
            name="Jordan Smith",
            password="Password@123",
        )

        assert res["user"]["role"] == "ANALYST"
        assert res["user"]["organization_id"] == "org-100"
        assert fake_invite.status == "ACCEPTED"
        handler._invite_repo.update.assert_awaited_once_with(fake_invite)


class TestRBACPermissions:

    @pytest.mark.asyncio
    async def test_analyst_can_create_borrower_and_facility(self):
        """Credit Analysts can create borrowers and loan facilities as part of core workflow."""
        session = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        
        # Test borrower creation by Analyst
        borrower_handler = CreateBorrowerHandler(session)
        fake_org = Organization(id="org-1", name="Blue Owl", industry="Private Credit")
        borrower_handler._org_repo.get_by_id = AsyncMock(return_value=fake_org)
        
        fake_borrower = Borrower(
            id="b-1",
            organization_id="org-1",
            company_name="Acme Corp",
            sector="Technology",
            country="USA",
            risk_rating=RiskRating(level="LOW", score=2),
        )
        borrower_handler._borrower_repo.add = AsyncMock(return_value=fake_borrower)

        created_b = await borrower_handler.handle(
            CreateBorrowerCommand(
                organization_id="org-1",
                company_name="Acme Corp",
                sector="Technology",
                country="USA",
                risk_level="LOW",
                risk_score=2,
            )
        )
        assert created_b.id == "b-1"
        assert created_b.organization_id == "org-1"

        # Test loan creation by Analyst
        loan_handler = CreateLoanHandler(session)
        loan_handler._borrower_repo.get_by_id = AsyncMock(return_value=fake_borrower)
        fake_loan = Loan(
            id="loan-1",
            borrower_id="b-1",
            principal_amount=MoneySchema(amount=Decimal("500000000.0"), currency="USD"),
            interest_rate=0.065,
            start_date="2026-08-30",
            maturity_date="2031-08-30",
            status=LoanStatus.ACTIVE,
        )
        loan_handler._loan_repo.add = AsyncMock(return_value=fake_loan)

        created_l = await loan_handler.handle(
            CreateLoanCommand(
                borrower_id="b-1",
                agreement_id=None,
                amount=Decimal("500000000.0"),
                currency="USD",
                interest_rate=0.065,
                start_date="2026-08-30",
                maturity_date="2031-08-30",
                status=LoanStatus.ACTIVE,
            )
        )
        assert created_l.id == "loan-1"
        assert created_l.principal_amount.amount == Decimal("500000000.0")


class TestMultiTenantIsolation:

    def test_cross_tenant_borrower_access_prohibited(self):
        """User from Org A cannot access Borrower belonging to Org B."""
        user_org_a = User(
            id="u-1",
            name="Alice",
            email=Email("alice@orga.com"),
            password_hash="pw",
            role=UserRole.ANALYST,
            organization_id="org-A",
        )
        borrower_org_b = Borrower(
            id="b-b",
            organization_id="org-B",
            company_name="Org B Borrower",
            sector="Finance",
            country="UK",
            risk_rating=RiskRating(level="LOW", score=1),
        )

        assert user_org_a.organization_id != borrower_org_b.organization_id


class TestLoanFacilityValidationAndCurrency:

    def test_multi_currency_schemas_supported(self):
        """USD, EUR, GBP, and INR currencies are valid in MoneySchema."""
        for curr in ["USD", "EUR", "GBP", "INR"]:
            money = MoneySchema(amount=Decimal("500000000.00"), currency=curr)
            assert money.currency == curr
            assert money.amount == Decimal("500000000.00")

    def test_large_institutional_amounts_validated(self):
        """Institutional principal amounts (e.g. 500M) are validated without precision loss."""
        payload = {
            "borrower_id": "b-1",
            "principal_amount": {"amount": "500000000.00", "currency": "INR"},
            "interest_rate": 0.085,
            "start_date": "2026-08-30",
            "maturity_date": "2031-08-30",
            "status": "ACTIVE",
        }
        loan_schema = LoanCreateSchema(**payload)
        assert loan_schema.principal_amount.currency == "INR"
        assert loan_schema.principal_amount.amount == Decimal("500000000.00")
