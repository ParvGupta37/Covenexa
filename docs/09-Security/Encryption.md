# Encryption

## Data In Transit

All production traffic should be served over **HTTPS (TLS 1.2+)**. This is configured at the reverse proxy / load balancer level (Nginx, AWS ALB, Cloudflare, etc.) — not at the FastAPI level.

In local development, HTTP is used (`http://localhost:8000`).

## Data At Rest

### PostgreSQL
- Database-level encryption can be enabled via the hosting provider (e.g., AWS RDS with AES-256 encryption at rest)
- v1.0 (local): no disk-level encryption (development environment)

### Pinecone
- Pinecone Serverless provides encryption at rest by default (AES-256)
- No additional configuration required

### Uploaded Files
- Files stored in `/uploads/` on the server filesystem
- Disk-level encryption (OS-level) can be applied on the server
- v1.1 plan: migrate to S3/GCS with server-side encryption

## Password Hashing

All user passwords are hashed with **bcrypt** (12 rounds) before storage:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash on registration
hashed = pwd_context.hash(plain_password)

# Verify on login
is_valid = pwd_context.verify(plain_password, stored_hash)
```

Passwords are **never** stored in plaintext, logged, or transmitted.

## JWT Token Signing

JWTs are signed with `HS256` (HMAC-SHA256) using the `SECRET_KEY` from environment config.
The `SECRET_KEY` must be a cryptographically random 64-char string in production.

```bash
# Generate a secure key
openssl rand -hex 32
```
