# Kubernetes — Not Used in v1.0

## Current Status

Kubernetes is not used in Covenexa v1.0. The application runs via **Docker Compose** for local development.

See [`Docker.md`](./Docker.md) for the current infrastructure setup.

## Recommended v2.0 Setup

For production at scale, a Kubernetes deployment would provide:
- Horizontal pod autoscaling for the FastAPI backend
- Health checks and auto-restart
- Rolling deployments with zero downtime
- Managed secrets (Kubernetes Secrets + external secret operator)
- Ingress with TLS termination

### Minimal Kubernetes Manifest

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: covenexa-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: covenexa-backend
  template:
    spec:
      containers:
        - name: backend
          image: covenexa-backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: covenexa-secrets
                  key: database-url
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
```
