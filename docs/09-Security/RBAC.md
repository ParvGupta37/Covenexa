# Security Architecture

## Authentication Security

| Mechanism | Implementation |
|:----------|:--------------|
| Password Hashing | `passlib` with `bcrypt`, 12 rounds |
| Token Type | JWT (HS256) |
| Access Token TTL | 30 minutes |
| Refresh Token TTL | 7 days |
| Token Storage | `localStorage` (client-side) |
| Token Transmission | `Authorization: Bearer <token>` header |
| Logout | Client clears localStorage + Zustand state |

### Password Strength Policy
Enforced at `AuthDomainService.is_strong_password()`:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (`!@#$%^&*` etc.)

---

## Role-Based Access Control (RBAC)

### Roles

| Role | Capabilities |
|:-----|:------------|
| `ADMIN` | Full platform access — create/delete organizations, manage all users and data |
| `ANALYST` | Read access + upload documents + run AI queries — cannot delete organizations or users |

### Enforcement

Every FastAPI route declares its required roles via:
```python
@router.delete("/{id}", dependencies=[Depends(require_role([UserRole.ADMIN]))])
```

The `require_role()` dependency:
1. Extracts the JWT from the `Authorization` header
2. Decodes and validates the token
3. Checks the `role` claim against the required roles
4. Returns 401 (invalid token) or 403 (insufficient role)

---

## Audit Logging

Every significant platform action is recorded to `audit_logs`:

| Logged Action | trigger |
|:-------------|:--------|
| `user_login` | Every successful login |
| `user_register` | New user creation |
| `document_upload` | File or SEC URL upload |
| `pipeline_run` | Risk intelligence pipeline execution |
| `organization_delete` | Org deletion by admin |
| `report_generate` | Credit memo generation |

The audit log is **append-only** — no updates or deletes are permitted. Accessible via `GET /api/v1/audit/` (ADMIN only).

---

## Tenant Isolation

### PostgreSQL
- All borrower, loan, document, and risk data is scoped by `borrower_id` or `organization_id`
- No cross-tenant data joins
- Cascading deletes enforced at the organization level

### Pinecone (Vector Database)
- Each document's embeddings are stored in a Pinecone namespace keyed to `agreement_id`
- All vector queries include `filter: { borrower_id: "..." }` metadata filter
- Zero-result responses do **not** retry without the filter (no cross-tenant fallback)

### Neo4j (Knowledge Graph)
- All graph nodes include `borrower_id` as a property
- Graph queries are parameterized by borrower_id

---

## Input Validation

| Layer | Implementation |
|:------|:--------------|
| API Layer | Pydantic v2 schemas — strict type validation on all request bodies |
| Domain Layer | `Email` Value Object — validates email format before database queries |
| File Upload | Extension whitelist: `.pdf`, `.docx`, `.html` only |
| Path Traversal | Filenames sanitized before saving: `Path(filename).name` strips directory prefixes |
| URL Validation | SEC EDGAR URLs validated against allowlist: `sec.gov`, `cloudfront.net` — blocks SSRF |

---

## Secret Management

All secrets are loaded from environment variables (`.env` file locally, secret manager in production):

```env
SECRET_KEY=<jwt-signing-key>
DATABASE_URL=postgresql+asyncpg://...
COHERE_API_KEY=...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
NEO4J_URI=...
NEO4J_PASSWORD=...
REDIS_URL=redis://:password@host:port/db
```

No secrets are hardcoded anywhere in the codebase.

---

## Error Handling & Information Leakage

```python
# Production mode: hide internal details
# app/core/config.py
ENVIRONMENT: str = "production"  # or "development"

# Exception handler
if settings.ENVIRONMENT == "production":
    return {"detail": "Internal server error"}
else:
    return {"detail": str(exc)}  # Full traceback only in development
```

Tested in the production readiness suite:
- `test_production_environment_hides_exception_details` ✅
- `test_development_environment_includes_exception_details` ✅

---

## CORS Configuration

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Production CORS origins should be restricted to the deployed frontend domain.
