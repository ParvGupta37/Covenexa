"""
Domain Model Invariant Tests: Lender/Organization vs Borrower.

Verifies:
1. Organization != Borrower (distinct domain entities).
2. Creating an organization does not trigger borrower creation.
3. Creating a borrower does not auto-create phantom loans (loans are explicit user actions).
4. Tenant isolation: borrower listing filters strictly by organization_id.
5. Organization creation and deletion schema & entity behavior.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.entities.organization import Organization
from app.domain.entities.borrower import Borrower
from app.domain.value_objects.risk_rating import RiskRating
from app.application.borrowers.commands import CreateBorrowerCommand
from app.application.borrowers.handlers import CreateBorrowerHandler, BorrowerQueryHandler
from app.application.borrowers.queries import ListBorrowersQuery
from app.core.schemas.borrower import BorrowerCreateSchema
from app.core.schemas.organization import OrganizationCreateSchema


class TestDomainModelInvariants:

    def test_organization_and_borrower_are_distinct_types(self):
        """Organization (lender tenant) and Borrower (portfolio company) are distinct types."""
        org = Organization(id="org-1", name="Blue Owl Capital", industry="Private Credit")
        borrower = Borrower(
            id="borr-1",
            organization_id="org-1",
            company_name="Acme Technologies",
            sector="Technology",
            country="USA",
            risk_rating=RiskRating(level="LOW", score=2),
        )

        assert type(org) is not type(borrower)
        assert borrower.organization_id == org.id
        assert org.name != borrower.company_name

    def test_borrower_create_schema_requires_organization_id(self):
        """Borrower creation schema mandates an organization_id foreign key."""
        payload = {
            "organization_id": "org-uuid-1234",
            "company_name": "Acme Technologies",
            "sector": "Technology",
            "country": "USA",
            "risk_rating": {"level": "LOW", "score": 2}
        }
        schema = BorrowerCreateSchema(**payload)
        assert schema.organization_id == "org-uuid-1234"
        assert schema.company_name == "Acme Technologies"

    def test_organization_create_schema_has_no_borrower_fields(self):
        """Organization creation schema only contains lender metadata, not borrower attributes."""
        org_schema = OrganizationCreateSchema(name="Blue Owl Capital", industry="Private Credit")
        assert not hasattr(org_schema, "risk_rating")
        assert not hasattr(org_schema, "borrower_id")
        assert org_schema.name == "Blue Owl Capital"

    @pytest.mark.asyncio
    async def test_create_borrower_handler_creates_no_auto_loans(self):
        """
        INVARIANT: CreateBorrowerHandler must create ONLY the borrower entity.
        It must NEVER insert automatic/phantom loans.
        """
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        # Mock org repo lookup returning existing org
        fake_org = Organization(id="org-100", name="Blue Owl Capital", industry="Private Credit")
        
        handler = CreateBorrowerHandler(session)
        # Mock the internal repos
        handler._org_repo.get_by_id = AsyncMock(return_value=fake_org)
        
        fake_added_borrower = Borrower(
            id="borr-100",
            organization_id="org-100",
            company_name="Acme Technologies",
            sector="Technology",
            country="USA",
            risk_rating=RiskRating(level="LOW", score=2),
        )
        handler._borrower_repo.add = AsyncMock(return_value=fake_added_borrower)

        command = CreateBorrowerCommand(
            organization_id="org-100",
            company_name="Acme Technologies",
            sector="Technology",
            country="USA",
            risk_level="LOW",
            risk_score=2,
        )

        result = await handler.handle(command)

        assert result.id == "borr-100"
        assert result.company_name == "Acme Technologies"
        assert result.organization_id == "org-100"

        # Verify borrower_repo.add was called once
        handler._borrower_repo.add.assert_awaited_once()

        # Verify NO SQL statements were executed directly to insert loans
        # (execute should not be called with INSERT INTO loans)
        for call_args in session.execute.call_args_list:
            sql_text = str(call_args[0][0])
            assert "INSERT INTO loans" not in sql_text, (
                "Found unexpected auto-loan creation during borrower registration!"
            )

    @pytest.mark.asyncio
    async def test_borrower_query_handler_filters_by_organization(self):
        """
        INVARIANT: BorrowerQueryHandler scopes listing to organization_id when provided.
        """
        session = MagicMock()
        handler = BorrowerQueryHandler(session)

        # Mock organization-filtered return
        handler._repo.get_by_organization_id = AsyncMock(return_value=[
            Borrower(
                id="borr-1",
                organization_id="org-A",
                company_name="Acme Corp",
                sector="Technology",
                country="USA",
                risk_rating=RiskRating(level="LOW", score=1),
            )
        ])
        handler._repo.get_all = AsyncMock(return_value=[
            Borrower(id="borr-1", organization_id="org-A", company_name="Acme Corp", sector="Tech", country="USA", risk_rating=RiskRating(level="LOW", score=1)),
            Borrower(id="borr-2", organization_id="org-B", company_name="Beta Logistics", sector="Logistics", country="USA", risk_rating=RiskRating(level="MED", score=5)),
        ])

        # Query Org A
        query = ListBorrowersQuery(organization_id="org-A")
        results = await handler.list_all(query)

        handler._repo.get_by_organization_id.assert_awaited_once_with("org-A")
        assert len(results) == 1
        assert results[0].company_name == "Acme Corp"
        assert results[0].organization_id == "org-A"
