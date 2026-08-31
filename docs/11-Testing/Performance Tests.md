# Performance Tests

## Current Status (v1.0)

Formal performance benchmarks (load testing, latency profiling) are **not configured** in v1.0.

## Observed Performance (Local Development)

| Endpoint | Approx. Latency |
|:---------|:---------------|
| GET /api/v1/auth/me | <50ms |
| GET /api/v1/risk/health/{id} | 100–300ms |
| GET /api/v1/risk/covenants/{id} | 100–200ms |
| POST /api/v1/risk/stress | 200–500ms |
| POST /api/v1/copilot/query (SQL only) | 2–5 seconds (Cohere API) |
| POST /api/v1/copilot/query (mock) | <100ms |
| Full document pipeline (10-page PDF) | 30–90 seconds |

## v1.1 Load Testing Plan

Use **Locust** or **k6** for load testing:

```python
# locustfile.py
from locust import HttpUser, task

class CoveneXaUser(HttpUser):
    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "admin@covenexa.in",
            "password": "Admin@123"
        })
        self.token = resp.json()["access_token"]

    @task
    def get_health_score(self):
        self.client.get(
            "/api/v1/risk/health/test-borrower-id",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

Target: 100 concurrent users, P95 < 500ms for read endpoints.
