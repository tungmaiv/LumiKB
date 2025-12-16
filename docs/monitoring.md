# LumiKB Monitoring and Observability

Story 7.5: Monitoring and Observability documentation for production deployment.

## Overview

LumiKB includes comprehensive monitoring through:
- **Prometheus**: Metrics collection and alerting rules
- **Grafana**: Visualization dashboards
- **AlertManager**: Alert routing and notification
- **Structured Logging**: JSON logs with correlation IDs

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Backend    │────▶│ Prometheus  │────▶│ AlertManager │
│  /metrics   │     │             │     │              │
└─────────────┘     └──────┬──────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Grafana   │
                    │ Dashboards  │
                    └─────────────┘
```

## Prometheus Metrics

### Endpoint

The `/metrics` endpoint exposes Prometheus-format metrics:

```bash
curl http://localhost:8000/metrics
```

### Available Metrics

#### HTTP Request Metrics (Auto-instrumented)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `lumikb_http_request_duration_seconds` | Histogram | method, path, status | HTTP request latency |
| `lumikb_http_request_size_bytes` | Histogram | method, path | Request body size |
| `lumikb_http_response_size_bytes` | Histogram | method, path | Response body size |
| `lumikb_http_requests_inprogress` | Gauge | method, path | In-flight requests |

#### Document Processing Metrics
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `lumikb_document_processing_queue_depth` | Gauge | queue_name | Queue depth |
| `lumikb_document_processing_duration_seconds` | Histogram | doc_type, status | Processing time |
| `lumikb_document_processing_total` | Counter | doc_type, status | Total processed |

#### LLM/Search Metrics
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `lumikb_llm_request_duration_seconds` | Histogram | model, operation | LLM call latency |
| `lumikb_llm_request_total` | Counter | model, operation, status | LLM call count |
| `lumikb_search_request_duration_seconds` | Histogram | search_type | Search latency |

#### Embedding Metrics
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `lumikb_embedding_batch_size` | Histogram | - | Chunks per batch |
| `lumikb_embedding_duration_seconds` | Histogram | - | Embedding time |

### Recording Metrics in Code

```python
from app.api.v1.metrics import (
    record_document_processing,
    record_llm_request,
    record_search_duration,
    set_queue_depth,
)

# Record document processing
record_document_processing(
    doc_type="pdf",
    status="success",
    duration_seconds=5.5,
)

# Record LLM request
record_llm_request(
    model="gpt-4",
    operation="synthesis",
    status="success",
    duration_seconds=2.3,
)

# Record search duration
record_search_duration(
    search_type="semantic",
    duration_seconds=0.5,
)

# Set queue depth
set_queue_depth(queue_name="document_processing", depth=10)
```

## Grafana Dashboards

### Pre-configured Dashboards

1. **API Latency Dashboard** (`api-latency.json`)
   - P50, P95, P99 latency percentiles
   - Request rate over time
   - In-progress request count

2. **Error Rates Dashboard** (`error-rates.json`)
   - Error rate gauge with 5% threshold
   - Error counts by endpoint
   - Status code distribution

3. **Queue Depth Dashboard** (`queue-depth.json`)
   - Document processing queue depth
   - Processing duration by document type
   - Embedding batch metrics

### Accessing Grafana

```bash
# Production
http://localhost:3001

# Default credentials (change in production!)
Username: admin
Password: ${GRAFANA_ADMIN_PASSWORD}
```

### Creating Custom Dashboards

1. Log into Grafana
2. Click "+" → "New Dashboard"
3. Add panels using Prometheus as data source
4. Use PromQL queries, e.g.:
   ```promql
   # P95 latency
   histogram_quantile(0.95, rate(lumikb_http_request_duration_seconds_bucket[5m]))

   # Error rate
   sum(rate(lumikb_http_request_duration_seconds_count{status=~"5.."}[5m]))
   / sum(rate(lumikb_http_request_duration_seconds_count[5m]))
   ```

## AlertManager

### Alert Rules

Pre-configured alerts in `infrastructure/prometheus/rules/alerts.yml`:

| Alert | Condition | Severity | Description |
|-------|-----------|----------|-------------|
| `HighErrorRate` | Error rate > 5% for 5min | critical | AC-7.5.3 requirement |
| `HighLatency` | P95 > 2s for 5min | warning | Slow responses |
| `APIDown` | No metrics for 2min | critical | Service unavailable |
| `DocumentQueueBacklog` | Queue > 100 for 10min | warning | Processing backlog |
| `LLMHighErrorRate` | LLM errors > 10% for 5min | critical | LLM failures |
| `SlowSearchResponses` | Search P95 > 3s for 5min | warning | Slow search |

### Notification Configuration

Edit `infrastructure/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        send_resolved: true
    webhook_configs:
      - url: '${PAGERDUTY_WEBHOOK_URL}'

  - name: 'warning-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SMTP_SMARTHOST` | SMTP server:port |
| `SMTP_FROM` | Sender email address |
| `SMTP_USERNAME` | SMTP authentication |
| `SMTP_PASSWORD` | SMTP password |
| `PAGERDUTY_WEBHOOK_URL` | PagerDuty integration |
| `SLACK_WEBHOOK_URL` | Slack webhook URL |

## Structured Logging

### Configuration

Logging is configured in `app/core/logging.py`:

```python
from app.core.logging import configure_logging, get_logger

# Configure at startup (in main.py)
configure_logging(
    json_logs=True,      # JSON format for production
    log_level="INFO",    # DEBUG, INFO, WARNING, ERROR
)

# Get a logger with request context
logger = get_logger(__name__)
logger.info("Operation completed", user_id="123", duration=0.5)
```

### Log Format

JSON output includes:
```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "info",
  "logger": "app.services.search",
  "event": "Search completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/v1/search",
  "user_id": "user-123",
  "duration_ms": 145
}
```

### Request Correlation

The `RequestContextMiddleware` automatically:
1. Generates unique `request_id` (UUID) or uses `X-Request-ID` header
2. Binds context to all logs within the request
3. Returns `X-Request-ID` header in response

Trace requests across services:
```bash
# Request with custom trace ID
curl -H "X-Request-ID: my-trace-123" http://localhost:8000/api/v1/search

# Response header
X-Request-ID: my-trace-123

# Find in logs
grep "my-trace-123" /var/log/lumikb/*.log
```

## Production Deployment

### Docker Compose

The monitoring stack is included in `infrastructure/docker/docker-compose.prod.yml`:

```bash
# Start all services including monitoring
docker compose -f infrastructure/docker/docker-compose.prod.yml \
  --env-file .env.prod up -d

# View monitoring services
docker compose -f infrastructure/docker/docker-compose.prod.yml ps | grep -E "prometheus|grafana|alertmanager"
```

### Required Environment Variables

Add to `.env.prod`:
```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<secure-password>
GRAFANA_ROOT_URL=https://grafana.example.com

# AlertManager
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=<smtp-password>
PAGERDUTY_WEBHOOK_URL=https://events.pagerduty.com/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Ports (optional, defaults shown)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
ALERTMANAGER_PORT=9093
```

### Health Checks

All monitoring services include health checks:

```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3001/api/health

# AlertManager
curl http://localhost:9093/-/healthy
```

## Runbook

### High Error Rate Alert

**Trigger**: Error rate > 5% for 5 minutes

**Investigation**:
1. Check Grafana Error Rates dashboard
2. Identify affected endpoints
3. Check application logs for error details:
   ```bash
   docker logs lumikb-api-prod 2>&1 | grep -i error | tail -50
   ```
4. Check dependent services (Postgres, Redis, Qdrant)

**Resolution**:
- If database issues: Check connection pool, restart if needed
- If memory issues: Scale up or restart containers
- If code bug: Roll back to previous version

### Queue Backlog Alert

**Trigger**: Queue depth > 100 for 10 minutes

**Investigation**:
1. Check Grafana Queue Depth dashboard
2. Check Celery worker status:
   ```bash
   docker exec lumikb-celery-worker-prod celery -A app.workers.celery_app inspect active
   ```
3. Check for stuck tasks or errors

**Resolution**:
- Scale up workers: Increase `--concurrency` or add worker replicas
- Clear failed tasks if recoverable
- Check for resource constraints

### Service Down Alert

**Trigger**: No metrics for 2 minutes

**Investigation**:
1. Check container status:
   ```bash
   docker ps | grep lumikb
   ```
2. Check container logs:
   ```bash
   docker logs lumikb-api-prod --tail 100
   ```
3. Check resource usage:
   ```bash
   docker stats lumikb-api-prod
   ```

**Resolution**:
- Restart container if OOM or deadlock
- Check disk space if logs filling up
- Scale resources if consistently hitting limits
