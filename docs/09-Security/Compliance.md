# Compliance — Regulatory & Data Handling Notes

## Overview

Covenexa v1.0 is a portfolio intelligence tool, not a regulated financial service. However, the platform is built with enterprise security principles that align with common financial services compliance requirements.

---

## Data Handling

| Concern | Implementation |
|:--------|:--------------|
| Personal Data | Minimal PII — only user name and email stored |
| Password Storage | bcrypt hash — never stored in plaintext |
| Document Storage | Uploaded files stored in `/uploads/` directory (server-local in v1.0) |
| Audit Trail | Append-only `audit_logs` table records every significant action |
| Data Deletion | Organization deletion cascades all related data |

---

## Access Control

- JWT-based authentication — short-lived tokens
- RBAC — ADMIN and ANALYST roles
- All operations logged in audit trail
- No unauthenticated data access

---

## What is Out of Scope for v1.0

- SOC 2 compliance
- GDPR / CCPA data subject rights (right to deletion, right to access export)
- FCA / SEC regulatory reporting
- Data residency controls
- Penetration testing certification

These are production requirements for an enterprise deployment and are planned for v2.0.

---

## Security Features That Support Compliance

See [`RBAC.md`](./RBAC.md) for the full security architecture including:
- Input sanitization (path traversal, SSRF prevention)
- Tenant isolation in vector and graph databases
- Environment-based error exposure control
- All passwords hashed — never logged or transmitted in plaintext
