# CI/CD Pipeline Configuration

## Overview

Covenexa utilizes GitHub Actions for continuous integration and automated deployment across backend and frontend services.

---

## 1. Continuous Integration (CI)

**Workflow File**: [`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml)  
**Triggers**: `push` and `pull_request` on branches `main`, `master`.

### Automated Pipeline Jobs:
1. **Backend Verification (`backend-test`)**:
   - Spawns containerized `postgres:15-alpine` and `redis:7-alpine` services with health checks.
   - Sets up Python 3.11 environment with pip dependency caching.
   - Executes the complete automated test suite (`pytest -v`).

2. **Frontend Typecheck & Build (`frontend-build`)**:
   - Sets up Node.js 20 runtime with npm dependency caching.
   - Executes strict TypeScript type validation (`npx tsc --noEmit`).
   - Compiles production assets bundle (`npm run build`).

3. **Docker Container Build Validation (`docker-build-check`)**:
   - Verifies that both multi-stage production Docker images build cleanly.

---

## 2. Continuous Deployment (CD)

**Workflow File**: [`.github/workflows/cd.yml`](file:///.github/workflows/cd.yml)  
**Triggers**: `push` of version tags (`v*.*.*`) or manual trigger via `workflow_dispatch`.

### Deployment Pipeline Stages:
1. **Container Build & Registry Publishing**:
   - Multi-stage Docker builds for backend and frontend.
   - Tags images with Git version tags.
2. **Production Deployment Execution**:
   - Zero-downtime container rolling update.
3. **Health Verification**:
   - Automated post-deployment API and UI health check.

---

## 3. Local Pre-Deployment Validation Commands

```bash
# 1. Backend test suite
cd backend && PYTHONPATH=.:.. pytest -v

# 2. Frontend typecheck
cd frontend && npx tsc --noEmit

# 3. Frontend production build
cd frontend && npm run build
```
