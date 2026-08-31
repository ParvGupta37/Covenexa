# RBAC — Role-Based Access Control

> Full security documentation is consolidated in [`RBAC.md`](./RBAC.md).

## Quick Reference

| Role | Login Credentials (Dev) | Permissions |
|:-----|:------------------------|:-----------|
| ADMIN | `admin@covenexa.in` / `Admin@123` | Full access |
| ANALYST | Register via `/register` with ANALYST role | Read + upload + query |

### Protected Routes (Frontend)
All routes under `/app/*` require a valid JWT. If `localStorage["access_token"]` is missing or expired, `ProtectedRoute` redirects to `/login`.

### Admin-only Backend Routes
- `DELETE /api/v1/organizations/{id}`
- `DELETE /api/v1/borrowers/{id}`
- `GET /api/v1/audit/`
- `POST /api/v1/risk/pipeline/{borrower_id}`
