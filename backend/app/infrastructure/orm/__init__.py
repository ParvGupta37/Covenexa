"""
SQLAlchemy ORM models package.
Exposes all ORM classes for app-wide use and migration autogeneration.
"""
from app.infrastructure.orm.base import Base
from app.infrastructure.orm.user_orm import UserORM
from app.infrastructure.orm.organization_orm import OrganizationORM
from app.infrastructure.orm.borrower_orm import BorrowerORM
from app.infrastructure.orm.loan_orm import LoanORM
from app.infrastructure.orm.agreement_orm import AgreementORM
# MEDIUM-3 (MEDIUM-5): FinancialStatementORM and ComplianceResultORM are Sprint-1
# tables superseded by financial_metrics and covenant_monitoring respectively.
# They are imported here only to keep their SQLAlchemy metadata registered (so
# Alembic can track them), but are NOT exported in __all__ and must NOT be used
# in any active code path.
from app.infrastructure.orm.financial_statement_orm import FinancialStatementORM  # deprecated, do not use
from app.infrastructure.orm.compliance_result_orm import ComplianceResultORM  # deprecated, do not use
from app.infrastructure.orm.report_orm import ReportORM
# Sprint 2 — Document pipeline models
from app.infrastructure.orm.document_chunk_orm import DocumentChunkORM
from app.infrastructure.orm.covenant_orm import CovenantORM
from app.infrastructure.orm.financial_metric_orm import FinancialMetricORM

from app.infrastructure.orm.invitation_orm import InvitationORM
from app.infrastructure.orm.copilot_orm import CopilotConversationORM, CopilotMessageORM

__all__ = [
    "Base",
    "UserORM",
    "OrganizationORM",
    "BorrowerORM",
    "LoanORM",
    "AgreementORM",
    "InvitationORM",
    # FinancialStatementORM — DEPRECATED (Sprint-1): superseded by FinancialMetricORM.
    # ComplianceResultORM  — DEPRECATED (Sprint-1): superseded by covenant_monitoring.
    # Neither is exported here to avoid misleading active use.
    "ReportORM",
    # Sprint 2
    "DocumentChunkORM",
    "CovenantORM",
    "FinancialMetricORM",
    # Copilot History & Conversations
    "CopilotConversationORM",
    "CopilotMessageORM",
]
