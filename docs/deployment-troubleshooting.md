# LumiKB Deployment Troubleshooting Guide

Story 7.4: Production Deployment Configuration

## Common Issues and Solutions

### 1. Service Won't Start

#### Symptoms
- Container exits immediately
- Error: "Production secrets validation failed"

#### Solution
Check that all required secrets are set with secure values:

```bash
# Check logs for specific missing secrets
docker logs lumikb-api-prod

# Verify environment variables are set
docker exec lumikb-api-prod env | grep LUMIKB
```

The application will fail to start in production if:
- `SECRET_KEY` contains "change-me" or "secret"
- `LITELLM_API_KEY` is "sk-dev-master-key"
- `DATABASE_URL` contains "lumikb_dev_password"
- `MINIO_SECRET_KEY` is "lumikb_dev_password"

### 2. Health Check Failures

#### `/health` Returns Error

This indicates the API process isn't running:

```bash
# Check container status
docker ps -a | grep lumikb-api

# Check container logs
docker logs lumikb-api-prod --tail 100

# Check for OOM (Out of Memory)
docker stats lumikb-api-prod
```

#### `/ready` Returns 503

This indicates a dependency is unavailable:

```bash
# Check which dependency is failing
curl http://localhost:8000/ready | jq .

# Response will show:
# {"status": "not_ready", "checks": {"database": {"healthy": false, "error": "..."}}}
```

**Database Down:**
```bash
docker logs lumikb-postgres-prod
docker exec lumikb-postgres-prod pg_isready
```

**Redis Down:**
```bash
docker logs lumikb-redis-prod
docker exec lumikb-redis-prod redis-cli ping
```

**Qdrant Down:**
```bash
docker logs lumikb-qdrant-prod
curl http://localhost:6333/readyz
```

### 3. Database Connection Issues

#### Error: "Connection refused"

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check network connectivity
docker network inspect lumikb-network-prod

# Verify connection string
docker exec lumikb-api-prod env | grep DATABASE_URL
```

#### Error: "Too many connections"

Increase `max_connections` in PostgreSQL:

```yaml
# docker-compose.prod.yml
postgres:
  command:
    - "postgres"
    - "-c"
    - "max_connections=300"
```

### 4. Celery Worker Issues

#### Workers Not Processing Tasks

```bash
# Check worker status
curl http://localhost:8000/api/v1/health/workers

# Check worker logs
docker logs lumikb-celery-worker-prod --tail 100

# Verify broker connectivity
docker exec lumikb-celery-worker-prod celery -A app.workers.celery_app inspect ping
```

#### Tasks Stuck in Queue

```bash
# Check queue depth
curl http://localhost:8000/api/v1/health/queues

# Purge stuck tasks (use with caution)
docker exec lumikb-celery-worker-prod celery -A app.workers.celery_app purge
```

### 5. Memory Issues

#### Container OOM Killed

```bash
# Check container exit reason
docker inspect lumikb-api-prod | jq '.[0].State'

# Increase memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G  # Increase from 1G
```

#### High Memory Usage

```bash
# Monitor memory usage
docker stats --no-stream

# For Qdrant, check collection sizes
curl http://localhost:6333/collections
```

### 6. Network Issues

#### Services Can't Find Each Other

```bash
# Check network exists
docker network ls | grep lumikb

# Check all services are on the network
docker network inspect lumikb-network-prod

# Test inter-container connectivity
docker exec lumikb-api-prod ping -c 2 postgres
```

#### Port Conflicts

```bash
# Check if ports are in use
sudo lsof -i :8000
sudo lsof -i :3000

# Use alternative ports in .env.prod
API_PORT=8080
FRONTEND_PORT=3001
```

### 7. LiteLLM / LLM Issues

#### LLM Requests Failing

```bash
# Check LiteLLM logs
docker logs lumikb-litellm-prod --tail 100

# Test LiteLLM directly
curl http://localhost:4000/health/readiness

# Verify API keys are set
docker exec lumikb-litellm-prod env | grep API_KEY
```

#### Ollama Not Responding

If using Ollama on the host machine:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# In Docker Compose, use host.docker.internal
OLLAMA_API_BASE=http://host.docker.internal:11434
```

### 8. Frontend Issues

#### API Calls Failing

```bash
# Check CORS settings
docker exec lumikb-api-prod env | grep CORS

# Verify NEXT_PUBLIC_API_URL matches your deployment
# This is baked into the build, so rebuild if changed
docker build -t lumikb-frontend:latest \
  --build-arg NEXT_PUBLIC_API_URL=http://api.example.com \
  frontend/
```

### 9. Kubernetes-Specific Issues

#### Pods Stuck in Pending

```bash
# Check pod events
kubectl -n lumikb describe pod <pod-name>

# Check resource availability
kubectl describe nodes | grep -A 5 "Allocated resources"
```

#### PVC Not Binding

```bash
# Check PVC status
kubectl -n lumikb get pvc

# Check StorageClass
kubectl get storageclass
```

### 10. Log Analysis

#### Finding Errors in Logs

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml logs --since 1h | grep -i error

# Kubernetes
kubectl -n lumikb logs -l app.kubernetes.io/component=api --since=1h | grep -i error
```

#### Enable Debug Logging

```bash
# Temporarily enable debug mode
docker exec -it lumikb-api-prod sh -c "export LUMIKB_DEBUG=true && ..."

# Or restart with debug enabled
LUMIKB_DEBUG=true docker compose -f docker-compose.prod.yml up -d api
```

## Performance Tuning

### API Performance

```yaml
# Increase worker processes (docker-compose.prod.yml)
api:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Performance

```yaml
# PostgreSQL tuning
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=512MB"
    - "-c"
    - "effective_cache_size=1536MB"
    - "-c"
    - "work_mem=8MB"
```

### Qdrant Performance

```yaml
# Increase HNSW parameters for better search quality
# (tradeoff: slower indexing, faster search)
qdrant:
  environment:
    QDRANT__STORAGE__HNSW__EF_CONSTRUCT: 200
```

## Getting Help

If issues persist:

1. Collect diagnostic information:
   ```bash
   docker compose -f docker-compose.prod.yml logs > diagnostic_logs.txt
   docker compose -f docker-compose.prod.yml ps >> diagnostic_logs.txt
   curl http://localhost:8000/ready >> diagnostic_logs.txt
   ```

2. Check GitHub Issues: https://github.com/your-org/lumikb/issues

3. Review architecture documentation in `docs/architecture.md`
