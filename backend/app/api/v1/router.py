"""
Top level v1 API Router routing sub-endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, organizations, borrowers, loans, uploads, documents,
    risk, alerts, copilot, audit, reports
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(organizations.router)
v1_router.include_router(borrowers.router)
v1_router.include_router(loans.router)
v1_router.include_router(uploads.router)
v1_router.include_router(documents.router)
v1_router.include_router(risk.router)
v1_router.include_router(alerts.router)
v1_router.include_router(copilot.router)
v1_router.include_router(audit.router)
v1_router.include_router(reports.router)
