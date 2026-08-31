# Sprint 1 — Enterprise Foundation & Platform Architecture

## Sprint Goal

Build the complete enterprise foundation for Covenexa: backend DDD architecture, PostgreSQL schema (Wave 1), authentication, RBAC, Docker infrastructure, frontend routing and layout, and AI scaffolding.

**Exit Criteria:** User can register, log in, see a dashboard skeleton, and the backend API is documented.

---

## Objectives Completed

- [x] Clean Architecture (DDD) — 4 layers: API, Application, Domain, Infrastructure
- [x] FastAPI backend with async SQLAlchemy
- [x] PostgreSQL schema — Wave 1: organizations, users, borrowers, loans, agreements, financial_statements, compliance_results, reports
- [x] Alembic migrations (`0001_initial_schema.py`)
- [x] JWT authentication (access + refresh tokens)
- [x] RBAC middleware (ADMIN / ANALYST roles)
- [x] bcrypt password hashing with strength validation
- [x] React 18 + TypeScript + Vite frontend
- [x] React Router v6 route map
- [x] Zustand stores: auth.store, company.store
- [x] Axios API client with auth interceptor
- [x] Custom CSS design system (Inter font, navy/indigo palette)
- [x] Sidebar + Topbar layout
- [x] Dashboard skeleton
- [x] Docker Compose (PostgreSQL, Redis, Neo4j)
- [x] OpenAPI docs at `/docs`
- [x] AI scaffolding: BaseAgent, agent registry, LangGraph dependency setup

---

## Architecture Established

### Backend Layer Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/   # FastAPI route handlers
│   ├── application/        # Use case handlers (command/query)
│   │   ├── commands/
│   │   ├── handlers/
│   │   └── queries/
│   ├── domain/             # Business entities, value objects, services
│   │   ├── entities/
│   │   ├── services/
│   │   └── value_objects/
│   └── infrastructure/     # DB repos, external adapters
│       └── repositories/
```

### Frontend Structure
```
frontend/src/
├── pages/          # One folder per route
├── components/
│   ├── shared/     # Reusable UI components
│   └── layout/     # Sidebar, Topbar, AppLayout
├── store/          # Zustand stores
├── lib/            # api.ts (Axios), utils
└── types/          # TypeScript interfaces
```

---

## Key Sprint 1 Decisions

| Decision | Detail |
|:---------|:-------|
| DDD over MVC | Forces clean separation; scales better for complex domain logic |
| Async SQLAlchemy | Required for FastAPI's async nature |
| Zustand over Redux | Simpler for a medium-complexity SaaS app |
| Vanilla CSS | Full design control without Tailwind's utility-class complexity |
| JWT stateless | No server-side session store needed |