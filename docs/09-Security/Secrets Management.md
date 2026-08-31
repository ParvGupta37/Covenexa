# Secrets Management

## Overview

All secrets are loaded from environment variables. In development, these are stored in a `.env` file at the project root. In production, they should be managed by a secret manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, or Kubernetes Secrets).

## Required Secrets

| Variable | Description | Sensitivity |
|:---------|:-----------|:-----------|
| `SECRET_KEY` | JWT signing key (HS256) | CRITICAL — rotate immediately if exposed |
| `DATABASE_URL` | PostgreSQL connection string | HIGH — contains DB password |
| `REDIS_URL` | Redis connection string | HIGH — may contain password |
| `COHERE_API_KEY` | Cohere LLM + Embed API key | HIGH — billing impact if exposed |
| `PINECONE_API_KEY` | Pinecone vector DB key | HIGH — billing impact if exposed |
| `NEO4J_PASSWORD` | Neo4j database password | HIGH |

## Local Development (.env)

```bash
# backend/.env
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql+asyncpg://covenexa_user:password@localhost:5432/covenexa_db
REDIS_URL=redis://localhost:6379/0
COHERE_API_KEY=your-cohere-key-or-leave-blank-for-mock
PINECONE_API_KEY=your-pinecone-key-or-leave-blank
PINECONE_ENVIRONMENT=us-east-1
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
ENVIRONMENT=development
```

**Never commit `.env` to version control.** `.env` is in `.gitignore`.

## Generating a Secure SECRET_KEY

```bash
openssl rand -hex 32
# Example output: 8f4b9c2e1a3d5f7b9e2c4a6d8f0b2e4a6c8e0a2c4e6a8c0e2a4c6e8a0b2c4e
```

## Production Secret Rotation

1. Generate a new `SECRET_KEY`
2. Deploy the new key to the secret manager
3. Restart backend processes (all active JWTs signed with old key will immediately expire — users must re-login)
