# LumiKB Production Deployment Runbook

Story 7.4: Production Deployment Configuration

## Overview

This runbook provides step-by-step instructions for deploying LumiKB to production using Docker Compose or Kubernetes.

## Prerequisites

- Docker 24.0+ and Docker Compose v2.0+
- (Optional) Kubernetes 1.26+ cluster with kubectl configured
- Access to container registry for custom images
- TLS certificates for production domains
- At least one LLM provider (Ollama, OpenAI, Anthropic, or Google)

## Quick Start (Docker Compose)

### 1. Prepare Environment

```bash
cd infrastructure/docker

# Copy the environment template
cp ../.env.prod.template .env.prod

# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For SECRET_KEY
openssl rand -base64 24  # For passwords

# Edit .env.prod with your secure values
nano .env.prod
```

### 2. Build Production Images

```bash
# From project root
docker build -t lumikb-api:latest -f backend/Dockerfile.api backend/
docker build -t lumikb-worker:latest -f backend/Dockerfile.worker backend/
docker build -t lumikb-beat:latest -f backend/Dockerfile.beat backend/
docker build -t lumikb-frontend:latest -f frontend/Dockerfile frontend/
```

### 3. Deploy Services

```bash
cd infrastructure/docker

# Start all services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Verify all services are healthy
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 4. Run Database Migrations

```bash
# Execute migrations in API container
docker exec lumikb-api-prod alembic upgrade head
```

### 5. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check readiness endpoint
curl http://localhost:8000/ready

# Verify frontend
curl http://localhost:3000/
```

## Kubernetes Deployment

### 1. Create Namespace and Secrets

```bash
cd infrastructure/k8s

# Create namespace
kubectl apply -f namespace.yaml

# IMPORTANT: Edit configmaps-secrets.yaml with secure values first!
# Then apply:
kubectl apply -f configmaps-secrets.yaml
```

### 2. Deploy Infrastructure Services

For production Kubernetes, consider using managed services:
- PostgreSQL: Cloud SQL, RDS, or Azure Database
- Redis: ElastiCache, Memorystore, or Azure Cache
- MinIO: S3, GCS, or Azure Blob Storage
- Qdrant: Qdrant Cloud or self-managed

If self-hosting infrastructure, deploy them first (not included in this runbook).

### 3. Deploy Application

```bash
# Apply in order:
kubectl apply -f services.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f worker-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# Verify deployment
kubectl -n lumikb get pods
kubectl -n lumikb get services
```

### 4. Run Migrations

```bash
# Get API pod name
API_POD=$(kubectl -n lumikb get pods -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl -n lumikb exec $API_POD -- alembic upgrade head
```

## Health Checks

### Liveness Probe (`/health`)

Returns 200 if the API service is running. Used by orchestrators to detect crashed containers.

```bash
curl -f http://localhost:8000/health
# Response: {"status": "healthy", "service": "lumikb-api", "timestamp": "..."}
```

### Readiness Probe (`/ready`)

Returns 200 if all dependencies are accessible. Returns 503 if any dependency is down.

```bash
curl -f http://localhost:8000/ready
# Response: {"status": "ready", "checks": {"database": {...}, "redis": {...}, "qdrant": {...}}, "timestamp": "..."}
```

### Worker Health (`/api/v1/health/workers`)

Returns Celery worker status and queue information.

```bash
curl http://localhost:8000/api/v1/health/workers
```

## Environment Variables Reference

See [Environment Variables Reference](#environment-variables-reference) section below.

## Scaling

### Docker Compose Scaling

```bash
# Scale API containers
docker compose -f docker-compose.prod.yml up -d --scale api=3

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery-worker=5
```

### Kubernetes Scaling

```bash
# Scale API
kubectl -n lumikb scale deployment lumikb-api --replicas=3

# Scale workers
kubectl -n lumikb scale deployment lumikb-worker --replicas=5
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lumikb-api-hpa
  namespace: lumikb
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lumikb-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Backup and Recovery

### Database Backup

```bash
# Docker Compose
docker exec lumikb-postgres-prod pg_dump -U lumikb lumikb > backup_$(date +%Y%m%d).sql

# Kubernetes
kubectl -n lumikb exec lumikb-postgres-0 -- pg_dump -U lumikb lumikb > backup_$(date +%Y%m%d).sql
```

### MinIO Backup

```bash
# Using mc (MinIO Client)
mc mirror lumikb-prod/lumikb-documents backup/lumikb-documents
```

### Qdrant Backup

Qdrant supports snapshots. See [Qdrant Documentation](https://qdrant.tech/documentation/concepts/snapshots/).

## Secrets Rotation

### Rotating Database Password

1. Update password in PostgreSQL
2. Update `LUMIKB_DATABASE_URL` in secrets
3. Restart API and worker deployments

```bash
# Kubernetes
kubectl -n lumikb rollout restart deployment lumikb-api lumikb-worker
```

### Rotating JWT Secret

1. Update `LUMIKB_JWT_SECRET` in secrets
2. Restart API deployment
3. Note: All existing sessions will be invalidated

## Monitoring Integration

### Prometheus Scraping

Add to Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'lumikb-api'
    static_configs:
      - targets: ['lumikb-api:8000']
    metrics_path: '/metrics'
```

### Log Aggregation

Logs are in JSON format for easy parsing. Configure your log aggregator (ELK, Loki, etc.) to collect from:
- Docker: `/var/lib/docker/containers/*/`
- Kubernetes: Pod logs via sidecar or DaemonSet

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | - | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | - | PostgreSQL password |
| `POSTGRES_DB` | Yes | - | PostgreSQL database name |
| `MINIO_ROOT_USER` | Yes | - | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | Yes | - | MinIO admin password |
| `SECRET_KEY` | Yes | - | Application secret key |
| `JWT_SECRET` | Yes | - | JWT signing secret |
| `LITELLM_MASTER_KEY` | Yes | - | LiteLLM proxy API key |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `GEMINI_API_KEY` | No | - | Google Gemini API key |
| `OLLAMA_API_BASE` | No | - | Ollama API base URL |
| `API_PORT` | No | 8000 | API server port |
| `FRONTEND_PORT` | No | 3000 | Frontend server port |
| `NEXT_PUBLIC_API_URL` | Yes | - | Public API URL for frontend |

## Troubleshooting

See [Troubleshooting Guide](./deployment-troubleshooting.md) for common issues and solutions.
