# API Design

## Base URL

```
/api/v1
```

All endpoints are versioned. OpenAPI docs at `/docs` (Swagger UI) and `/redoc`.

---

## Authentication Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login → JWT tokens | No |
| GET | `/auth/me` | Get authenticated user profile | Yes |

---

## Organization Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/organizations/` | List all organizations | ADMIN, ANALYST |
| POST | `/organizations/` | Create new organization | ADMIN |
| GET | `/organizations/{id}` | Get org details + stats (borrower_count, loan_count, agreement_count) | ADMIN, ANALYST |
| DELETE | `/organizations/{id}` | Delete org + cascade all data | ADMIN only |

---

## Borrower Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/borrowers/` | List all borrowers | ADMIN, ANALYST |
| POST | `/borrowers/` | Register new borrower | ADMIN |
| GET | `/borrowers/{id}` | Get borrower detail | ADMIN, ANALYST |
| DELETE | `/borrowers/{id}` | Delete borrower | ADMIN only |

---

## Loan Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/loans/` | List all loans | ADMIN, ANALYST |
| POST | `/loans/` | Create loan facility | ADMIN |
| GET | `/loans/{id}` | Get loan detail | ADMIN, ANALYST |

---

## Document Upload Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| POST | `/uploads/` | Upload PDF/DOCX (multipart: loan_id + file) | ADMIN, ANALYST |
| POST | `/uploads/sec-url` | Ingest SEC EDGAR filing by URL | ADMIN, ANALYST |
| GET | `/uploads/{loan_id}` | List documents for a loan | ADMIN, ANALYST |

---

## Document Intelligence Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/documents/loan/{loan_id}` | Get document metadata for a loan | ADMIN, ANALYST |
| GET | `/documents/borrower/{borrower_id}` | Get all documents for a borrower | ADMIN, ANALYST |
| GET | `/documents/{agreement_id}` | Get agreement detail | ADMIN, ANALYST |
| GET | `/documents/{agreement_id}/chunks` | Get document text chunks | ADMIN, ANALYST |
| GET | `/documents/{agreement_id}/covenants` | Get extracted covenants | ADMIN, ANALYST |
| GET | `/documents/{agreement_id}/financials` | Get extracted financial metrics | ADMIN, ANALYST |

---

## Risk Intelligence Endpoints

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/risk/health/{borrower_id}` | Borrower Health Score (0–100) | ADMIN, ANALYST |
| GET | `/risk/default/{borrower_id}` | Default probability (Altman Z-Score based) | ADMIN, ANALYST |
| GET | `/risk/covenants/{borrower_id}` | Covenant compliance status + headroom | ADMIN, ANALYST |
| POST | `/risk/stress` | Run stress test simulation | ADMIN, ANALYST |
| GET | `/risk/recommendations/{borrower_id}` | AI-generated action recommendations | ADMIN, ANALYST |
| GET | `/risk/graph/{borrower_id}` | Knowledge graph nodes + edges | ADMIN, ANALYST |
| POST | `/risk/pipeline/{borrower_id}` | Manually trigger full risk pipeline | ADMIN |

---

## AI Copilot Endpoint

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| POST | `/copilot/query` | Natural language query — returns response + citations | ADMIN, ANALYST |

**Request body:**
```json
{
  "query": "What is the leverage covenant for this borrower?",
  "borrower_id": "uuid",
  "session_id": "optional-uuid"
}
```

---

## Alerts Endpoint

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/alerts/` | List alerts (filterable: unread_only, borrower_id) | ADMIN, ANALYST |
| POST | `/alerts/{id}/read` | Mark alert as read | ADMIN, ANALYST |

---

## Reports Endpoint

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| POST | `/reports/credit-memo` | Generate Executive Credit Memorandum | ADMIN, ANALYST |

---

## Audit Endpoint

| Method | Path | Description | Auth Required |
|:-------|:-----|:-----------|:-------------|
| GET | `/audit/` | List audit log events | ADMIN only |

---

## API Design Principles

1. **GET endpoints are read-only.** No side effects from fetching data.
2. **Lazy computation triggers.** `GET /risk/health` auto-runs the pipeline if no score exists but financial_metrics are present.
3. **Consistent error format.** All errors return `{ "detail": "..." }` with appropriate HTTP status codes.
4. **UUID-based IDs.** All entity identifiers are UUIDs, generated server-side.
5. **Versioned.** All routes under `/api/v1/` to support future `/api/v2/` introduction.
6. **RBAC enforced at route level.** Every route has `dependencies=[Depends(require_role(...))]`.
