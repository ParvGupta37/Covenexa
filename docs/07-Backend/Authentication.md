# Authentication & Authorization

## Overview

Covenexa uses **JWT-based stateless authentication** with two token types: a short-lived `access_token` and a longer-lived `refresh_token`. All tokens are generated using the HS256 algorithm and signed with a configurable secret key.

---

## Authentication Flow

```
1. POST /api/v1/auth/register
   Payload: { name, email, password, role }
   → PasswordStrengthValidation (min 8 chars, uppercase, lowercase, digit, special)
   → EmailVO validation (format check at domain layer)
   → bcrypt hash of password
   → INSERT user row
   → Return UserResponseSchema

2. POST /api/v1/auth/login
   Payload: { email, password }
   → Lookup user by email
   → bcrypt verify password against stored hash
   → If match: create access_token (30min) + refresh_token (7 days)
   → Return { access_token, refresh_token, token_type: "bearer" }
   → Audit log: action="user_login"

3. GET /api/v1/auth/me
   Header: Authorization: Bearer <access_token>
   → Decode JWT, extract user_id from "sub" claim
   → Lookup user in DB
   → Return UserResponseSchema (no password_hash)
```

---

## Frontend Token Storage

```typescript
// auth.store.ts (Zustand)
// Tokens stored in localStorage:
//   "access_token"  → attached to every Axios request
//   "refresh_token" → stored for future refresh

// api.ts (Axios instance)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});
```

---

## Role-Based Access Control (RBAC)

| Role | Permissions |
|:-----|:-----------|
| `ADMIN` | Full platform access — create/delete orgs, manage all data |
| `ANALYST` | Read + upload documents + run copilot queries — no deletion |

### Backend Enforcement

```python
# app/core/dependencies.py
require_role([UserRole.ADMIN, UserRole.ANALYST])  # Read endpoints
require_role([UserRole.ADMIN])                    # Delete / admin endpoints
```

Every API router specifies `dependencies=[Depends(require_role(...))]` at the route level. No route is unguarded except `/auth/login` and `/auth/register`.

---

## Token Structure

```json
// Access Token Payload
{
  "sub": "user-uuid",
  "role": "ADMIN",
  "type": "access",
  "exp": 1234567890
}

// Refresh Token Payload
{
  "sub": "user-uuid",
  "type": "refresh",
  "exp": 1234567890
}
```

---

## Password Security

- **Hashing:** `passlib` with `bcrypt` scheme, 12 rounds
- **Strength Policy:** Enforced at `AuthDomainService.is_strong_password()`:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

---

## Logout & Session Invalidation

Since tokens are stateless (no server-side session store), logout is handled client-side:
```typescript
// auth.store.ts
logout: () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  set({ user: null });
}

// company.store.ts
clearCompanies: () => {
  localStorage.removeItem("selected_company_id");
  set({ companies: [], selectedCompanyId: "" });
}
```

On organization deletion, both stores are cleared before redirecting to `/login` to prevent ghost state.

---

## Audit Logging

Every authenticated action is recorded:

```python
await log_audit_event(
    action="user_login",
    resource_type="auth",
    user_id=user.id,
    user_email=user.email,
    details={"email": email}
)
```

Audit log is append-only — no updates or deletes. Visible via `GET /api/v1/audit/`.
