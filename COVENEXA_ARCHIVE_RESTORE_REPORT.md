# COVENEXA — ARCHIVE + RESTORE FEATURE REPORT

## Executive Summary
The non-destructive **Archive + Restore** lifecycle has been implemented and verified across the full Covenexa stack for both **Borrowers** and **Loan Facilities**. Physical deletion of portfolio data during administrative lifecycle transitions has been replaced with persistent archival state management, preserving historical financial metrics, covenants, risk assessments, credit agreements, documents, and audit logs.

---

## 1. Files Changed

### Database & Migrations
- **[`backend/alembic/versions/0008_add_archival_to_borrowers_and_loans.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/alembic/versions/0008_add_archival_to_borrowers_and_loans.py)**: Added `is_archived` (boolean, default FALSE), `archived_at` (timestamp with timezone), and `archived_by` (foreign key to `users.id`) with indexes to both `borrowers` and `loans` tables.

### Domain Entities & ORM Models
- **[`backend/app/domain/entities/borrower.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/domain/entities/borrower.py)**: Added `is_archived`, `archived_at`, `archived_by`, and domain methods `archive(user_id)` and `restore()`.
- **[`backend/app/domain/entities/loan.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/domain/entities/loan.py)**: Added `is_archived`, `archived_at`, `archived_by`, and domain methods `archive(user_id)` and `restore()`.
- **[`backend/app/infrastructure/orm/borrower_orm.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/infrastructure/orm/borrower_orm.py)**: Added ORM column mappings and entity converters.
- **[`backend/app/infrastructure/orm/loan_orm.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/infrastructure/orm/loan_orm.py)**: Added ORM column mappings and entity converters.
- **[`backend/app/core/schemas/borrower.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/core/schemas/borrower.py)**: Added `is_archived`, `archived_at`, and `archived_by` to response schema.
- **[`backend/app/core/schemas/loan.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/core/schemas/loan.py)**: Added `is_archived`, `archived_at`, and `archived_by` to response schema.

### Application Commands, Queries & Handlers
- **[`backend/app/application/borrowers/commands.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/borrowers/commands.py)**: Added `ArchiveBorrowerCommand` and `RestoreBorrowerCommand`.
- **[`backend/app/application/borrowers/queries.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/borrowers/queries.py)**: Added `status: str = "ACTIVE"` filter.
- **[`backend/app/application/borrowers/handlers.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/borrowers/handlers.py)**: Implemented `ArchiveBorrowerHandler` and `RestoreBorrowerHandler`.
- **[`backend/app/application/loans/commands.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/loans/commands.py)**: Added `ArchiveLoanCommand` and `RestoreLoanCommand`.
- **[`backend/app/application/loans/queries.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/loans/queries.py)**: Added `status: str = "ACTIVE"` and `organization_id` filters.
- **[`backend/app/application/loans/handlers.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/loans/handlers.py)**: Implemented `ArchiveLoanHandler` and `RestoreLoanHandler`.
- **[`backend/app/application/uploads/handlers.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/application/uploads/handlers.py)**: Added validation preventing document uploads to archived loan facilities.

### Repositories
- **[`backend/app/infrastructure/repositories/borrower_repository_impl.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/infrastructure/repositories/borrower_repository_impl.py)**: Added status filtering (`ACTIVE`, `ARCHIVED`, `ALL`) and `archive()`/`restore()` operations.
- **[`backend/app/infrastructure/repositories/loan_repository_impl.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/infrastructure/repositories/loan_repository_impl.py)**: Added status filtering (`ACTIVE`, `ARCHIVED`, `ALL`) and `archive()`/`restore()` operations.

### API Endpoints
- **[`backend/app/api/v1/endpoints/borrowers.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/api/v1/endpoints/borrowers.py)**:
  - `POST /borrowers/{id}/archive` (ADMIN only, audit log `borrower.archived`).
  - `POST /borrowers/{id}/restore` (ADMIN only, audit log `borrower.restored`).
  - `GET /borrowers/?status=ACTIVE|ARCHIVED|ALL` (default `ACTIVE`).
- **[`backend/app/api/v1/endpoints/loans.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/api/v1/endpoints/loans.py)**:
  - `POST /loans/{id}/archive` (ADMIN only, audit log `loan.archived`).
  - `POST /loans/{id}/restore` (ADMIN only, audit log `loan.restored`).
  - `GET /loans/?status=ACTIVE|ARCHIVED|ALL` (default `ACTIVE`).
  - `GET /loans/count?status=ACTIVE|ARCHIVED|ALL`.
- **[`backend/app/api/v1/endpoints/risk.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/api/v1/endpoints/risk.py)**: Filtered archived entities from active portfolio summary, distribution, and graph representations.
- **[`backend/app/api/v1/endpoints/alerts.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/api/v1/endpoints/alerts.py)**: Filtered alerts for active borrowers only.
- **[`backend/app/api/v1/endpoints/organizations.py`](file:///Users/parvgupta/Desktop/Covenexa/backend/app/api/v1/endpoints/organizations.py)**: Filtered active counts for borrower and loan statistics.

### Frontend
- **[`frontend/src/types/index.ts`](file:///Users/parvgupta/Desktop/Covenexa/frontend/src/types/index.ts)**: Added `is_archived`, `archived_at`, and `archived_by` to `Borrower` and `Loan` types.
- **[`frontend/src/pages/borrowers/BorrowersPage.tsx`](file:///Users/parvgupta/Desktop/Covenexa/frontend/src/pages/borrowers/BorrowersPage.tsx)**: Added status filter tabs `[Active] [Archived] [All]`, `ARCHIVED` status badge, Archive & Restore actions for `ADMIN`, and clear confirmation dialogs.
- **[`frontend/src/pages/loans/LoansPage.tsx`](file:///Users/parvgupta/Desktop/Covenexa/frontend/src/pages/loans/LoansPage.tsx)**: Added status filter tabs `[Active] [Archived] [All]`, `ARCHIVED` status badge, Archive & Restore actions for `ADMIN`, and clear confirmation dialogs.

---

## 2. RBAC & Tenant Isolation Matrix

| Operation | `ADMIN` | `ANALYST` | Cross-Tenant Protection |
|:---|:---:|:---:|:---|
| **Archive Borrower** | ✅ Allowed | ❌ HTTP 403 | ❌ HTTP 403 (Tenant Scoped) |
| **Restore Borrower** | ✅ Allowed | ❌ HTTP 403 | ❌ HTTP 403 (Tenant Scoped) |
| **Archive Loan Facility** | ✅ Allowed | ❌ HTTP 403 | ❌ HTTP 403 (Tenant Scoped) |
| **Restore Loan Facility** | ✅ Allowed | ❌ HTTP 403 | ❌ HTTP 403 (Tenant Scoped) |
| **View Active Entities** | ✅ Allowed | ✅ Allowed | Scoped to User's Organization |
| **View Archived Entities** | ✅ Allowed | ✅ Allowed | Scoped to User's Organization |
| **Upload to Archived Loan**| ❌ Rejected (400) | ❌ Rejected (400) | ❌ Rejected |

---

## 3. Audit Log Events

Every lifecycle transition records an immutable audit log entry in the `audit_logs` table:
- `borrower.archived` $\rightarrow$ actor user, borrower ID, previous_state = ACTIVE, new_state = ARCHIVED
- `borrower.restored` $\rightarrow$ actor user, borrower ID, previous_state = ARCHIVED, new_state = ACTIVE
- `loan.archived` $\rightarrow$ actor user, loan ID, previous_state = ACTIVE, new_state = ARCHIVED
- `loan.restored` $\rightarrow$ actor user, loan ID, previous_state = ARCHIVED, new_state = ACTIVE

---

## 4. Test Results & Verification

- **Full Backend Pytest Suite**: **`124 / 124 passed (100%)`** in 11.36s.
  - `test_archive_restore_lifecycle.py`: **11 / 11 passed**
  - `test_rbac_portfolio_deletion.py`: **8 / 8 passed**
  - `test_rbac_multi_tenant_facilities.py`: **6 / 6 passed**
  - All existing domain, engine, and security regression tests: **Passed**
- **Frontend TypeScript (`tsc --noEmit`)**: **`0 Errors`**
- **Frontend Build (`npm run build`)**: **`Clean Build, 0 Errors`**
- **End-to-End Live API Multi-Role Verification**: **Verified** (Alex Morgan Admin + Sarah Mitchell Analyst under Blue Owl).
