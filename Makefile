# =============================================================
# Covenexa — Makefile
# Development workflow shortcuts.
# Usage: make <target>
# =============================================================

.PHONY: help up down restart logs ps \
        migrate migrate-check migrate-down migrate-history \
        shell-backend shell-postgres shell-redis \
        test test-backend test-mcp test-events \
        lint format \
        clean clean-volumes \
        frontend-install frontend-dev frontend-build

# Load .env if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

DOCKER_COMPOSE = docker compose
BACKEND_CONTAINER = covenexa_backend
POSTGRES_CONTAINER = covenexa_postgres
REDIS_CONTAINER = covenexa_redis

# ── DEFAULT ───────────────────────────────────────────────────
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "  Covenexa — Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── DOCKER COMPOSE ────────────────────────────────────────────
up: ## Start all services (detached)
	@echo "🚀 Starting Covenexa services..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started. Run 'make ps' to check status."

up-infra: ## Start only infrastructure (postgres, neo4j, redis, pgadmin)
	@echo "🚀 Starting infrastructure services..."
	$(DOCKER_COMPOSE) up -d postgres neo4j redis pgadmin
	@echo "✅ Infrastructure services started."

down: ## Stop all services
	@echo "🛑 Stopping Covenexa services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Services stopped."

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

build: ## Rebuild all Docker images
	@echo "🔨 Building Docker images..."
	$(DOCKER_COMPOSE) build --no-cache
	@echo "✅ Images built."

logs: ## Follow logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Follow backend logs
	$(DOCKER_COMPOSE) logs -f backend

logs-mcp: ## Follow MCP server logs
	$(DOCKER_COMPOSE) logs -f mcp_server

ps: ## Show running service status
	$(DOCKER_COMPOSE) ps

# ── DATABASE MIGRATIONS ───────────────────────────────────────
migrate: ## Run Alembic migrations (upgrade head)
	@echo "🗄️  Running database migrations..."
	$(DOCKER_COMPOSE) exec backend alembic upgrade head
	@echo "✅ Migrations applied."

migrate-check: ## Check for pending migrations
	$(DOCKER_COMPOSE) exec backend alembic check

migrate-down: ## Rollback last migration
	@echo "⏪ Rolling back last migration..."
	$(DOCKER_COMPOSE) exec backend alembic downgrade -1

migrate-history: ## Show migration history
	$(DOCKER_COMPOSE) exec backend alembic history --verbose

migrate-revision: ## Create a new migration (MSG="description")
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(MSG)"

# ── SHELLS ────────────────────────────────────────────────────
shell-backend: ## Open a shell inside the backend container
	$(DOCKER_COMPOSE) exec backend bash

shell-postgres: ## Open psql inside the postgres container
	$(DOCKER_COMPOSE) exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

shell-redis: ## Open redis-cli inside the redis container
	$(DOCKER_COMPOSE) exec redis redis-cli -a $(REDIS_PASSWORD)

shell-neo4j: ## Open cypher-shell inside the neo4j container
	$(DOCKER_COMPOSE) exec neo4j cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASSWORD)

# ── TESTING ───────────────────────────────────────────────────
test: ## Run all tests
	@echo "🧪 Running all tests..."
	$(DOCKER_COMPOSE) exec backend pytest tests/ -v --tb=short
	@echo "✅ Tests complete."

test-backend: ## Run backend tests only
	$(DOCKER_COMPOSE) exec backend pytest tests/backend/ -v --tb=short

test-mcp: ## Run MCP server tests
	$(DOCKER_COMPOSE) exec backend pytest tests/mcp_server/ -v --tb=short

test-events: ## Run event bus tests
	$(DOCKER_COMPOSE) exec backend pytest tests/event_bus/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(DOCKER_COMPOSE) exec backend pytest tests/ --cov=app --cov-report=html --cov-report=term

# ── CODE QUALITY ──────────────────────────────────────────────
lint: ## Run ruff linter on backend
	$(DOCKER_COMPOSE) exec backend ruff check app/ --fix

format: ## Run ruff formatter on backend
	$(DOCKER_COMPOSE) exec backend ruff format app/

typecheck: ## Run mypy type checking
	$(DOCKER_COMPOSE) exec backend mypy app/ --ignore-missing-imports

# ── FRONTEND ──────────────────────────────────────────────────
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend dev server (local, not Docker)
	cd frontend && npm run dev

frontend-build: ## Build frontend production bundle
	cd frontend && npm run build

frontend-lint: ## Lint frontend TypeScript
	cd frontend && npm run lint

# ── SETUP ─────────────────────────────────────────────────────
setup: ## First-time setup: copy .env, start infra, run migrations
	@echo "⚙️  Setting up Covenexa for the first time..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📋 .env created from .env.example — please update secrets!"; \
	else \
		echo "📋 .env already exists, skipping copy."; \
	fi
	@echo "🚀 Starting infrastructure..."
	$(DOCKER_COMPOSE) up -d postgres neo4j redis pgadmin
	@echo "⏳ Waiting 15s for PostgreSQL to be ready..."
	sleep 15
	@echo "🗄️  Running migrations..."
	$(DOCKER_COMPOSE) up -d backend
	sleep 10
	$(DOCKER_COMPOSE) exec backend alembic upgrade head
	@echo ""
	@echo "✅ Covenexa is ready!"
	@echo ""
	@echo "  Backend:    http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo "  pgAdmin:    http://localhost:5050"
	@echo "  Neo4j:      http://localhost:7474"
	@echo ""

# ── CLEANUP ───────────────────────────────────────────────────
clean: ## Stop services and remove containers
	$(DOCKER_COMPOSE) down --remove-orphans

clean-volumes: ## ⚠️  Stop services and DELETE all data volumes
	@echo "⚠️  WARNING: This will DELETE all database data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "✅ All volumes removed."
