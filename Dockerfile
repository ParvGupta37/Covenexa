FROM python:3.12-slim as base

LABEL maintainer="Covenexa Engineering"
LABEL description="Covenexa FastAPI Backend — Core SaaS API Platform"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from backend/requirements.txt
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create local uploads directory
RUN mkdir -p /app/uploads

# Copy application source including root modules (ai, integrations, event_bus, etc.)
COPY . .

# ── DEVELOPMENT TARGET ─────────────────────────────────────────
FROM base as development
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]

# ── PRODUCTION TARGET ──────────────────────────────────────────
FROM base as production
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
