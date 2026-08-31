# Docker Setup & Local Development

## Docker Compose Services

Covenexa uses Docker Compose to run all infrastructure services locally. The application code (backend, frontend) runs natively outside Docker for development speed.

```yaml
# docker-compose.yml services:
services:
  covenexa_db:      # PostgreSQL 15
  covenexa_redis:   # Redis 7
  covenexa_neo4j:   # Neo4j 5
```

---

## Starting Infrastructure

```bash
# Start all infrastructure services
docker-compose up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f covenexa_db
docker-compose logs -f covenexa_redis
docker-compose logs -f covenexa_neo4j
```

---

## Service Configuration

### PostgreSQL
```
Host: localhost
Port: 5432
Database: covenexa_db
User: covenexa_user
Password: (see .env)
URL: postgresql+asyncpg://covenexa_user:password@localhost:5432/covenexa_db
```

### Redis
```
Host: localhost
Port: 6379
URL: redis://:password@localhost:6379/0
```

### Neo4j
```
Host: localhost
Bolt Port: 7687
Browser UI: http://localhost:7474
URL: bolt://localhost:7687
User: neo4j
Password: (see .env)
```

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations
PYTHONPATH=. alembic upgrade head

# Start development server
uvicorn app.main:app --port 8000 --reload

# API docs
open http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000
```

---

## Environment Variables

Create `backend/.env`:

```env
# Application
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://covenexa_user:password@localhost:5432/covenexa_db

# Redis
REDIS_URL=redis://localhost:6379/0

# AI APIs
COHERE_API_KEY=your-cohere-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=covenexa-docs

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## Running Tests

```bash
cd backend

# Run all tests (except slow cleanup tests)
PYTHONPATH=.:.. .venv/bin/pytest tests/ -v \
  --ignore=tests/test_low5_duplicate_cleanup.py

# Expected: 92 passed
```

---

## Common Commands

```bash
# Reset database (drop + recreate + migrate)
docker-compose down -v              # Remove volumes
docker-compose up -d                # Restart
cd backend
PYTHONPATH=. alembic upgrade head   # Re-run migrations

# Add a new Alembic migration
alembic revision --autogenerate -m "your migration name"

# View all applied migrations
alembic history

# Stop all services
docker-compose down
```
