# Deployment Checklist

## Pre-Deployment

- [ ] All environment variables set in production environment
- [ ] `SECRET_KEY` is a cryptographically random 64-char string (not the dev default)
- [ ] `ENVIRONMENT=production` set in environment
- [ ] `COHERE_API_KEY` configured
- [ ] `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT` configured
- [ ] `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` configured
- [ ] `DATABASE_URL` points to production PostgreSQL instance
- [ ] `REDIS_URL` points to production Redis instance
- [ ] CORS origins updated to production frontend domain

## Database

- [ ] PostgreSQL running and accessible
- [ ] All 4 migrations applied: `alembic upgrade head`
- [ ] Verify 19 tables exist: `SELECT tablename FROM pg_tables WHERE schemaname = 'public';`
- [ ] At least one admin user seeded (or registered via `/auth/register`)

## Backend

- [ ] `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
- [ ] Health check passes: `GET /health` returns 200
- [ ] Auth check: `POST /api/v1/auth/login` returns JWT tokens
- [ ] Redis event consumer started (document upload subscriber)

## Frontend

- [ ] `VITE_API_URL` set to production backend URL
- [ ] `npm run build` produces `/dist` without errors
- [ ] Serve `/dist` via Nginx or CDN
- [ ] All routes handle page refresh (Nginx `try_files $uri /index.html`)

## Security

- [ ] HTTPS configured (TLS certificate)
- [ ] CORS restricted to production frontend domain only
- [ ] Rate limiting enabled on auth endpoints
- [ ] File upload directory not web-accessible
- [ ] `ENVIRONMENT=production` — verify error details are hidden

## Post-Deployment Verification

- [ ] Login with admin account works
- [ ] Register a new organization and borrower
- [ ] Upload a test PDF document
- [ ] Verify document analysis pipeline completes (check `agreements.parsing_status = 'completed'`)
- [ ] Run risk pipeline manually: `POST /api/v1/risk/pipeline/{borrower_id}`
- [ ] Verify Dashboard shows live data (not empty)
- [ ] Test AI Copilot query
- [ ] Run stress test
- [ ] Generate credit memorandum
- [ ] Check audit log: `GET /api/v1/audit/`

## Monitoring

- [ ] Application logs being collected (structlog JSON format)
- [ ] Pinecone index accessible and queryable
- [ ] PostgreSQL connection pool not exhausting (check `max_connections`)
- [ ] Redis connection stable
