FROM python:3.12-slim as base

LABEL maintainer="Covenexa Engineering"
LABEL description="Covenexa FastAPI Backend — Core SaaS API Platform"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create local uploads directory
RUN mkdir -p /app/uploads

# ── DEVELOPMENT TARGET ─────────────────────────────────────────
FROM base as development
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── PRODUCTION TARGET ──────────────────────────────────────────
FROM base as production
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
