# Story 5.13: Celery Beat Filesystem Fix (Technical Debt)

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5.13
**Status:** done
**Created:** 2025-12-03
**Story Points:** 2
**Priority:** Medium
**Type:** Technical Debt - Infrastructure

---

## Story Statement

**As a** DevOps engineer,
**I want** Celery Beat to write its schedule file to a writable directory with proper volume persistence,
**So that** scheduled tasks (reconciliation, outbox processing, cleanup) execute reliably without filesystem permission errors across container restarts.

---

## Context

This story addresses a technical debt item where the Celery Beat scheduler cannot persist its schedule file (`celerybeat-schedule`) due to the backend directory being mounted as read-only in Docker.

**Current Issue:**
- The `celery-beat` service in `docker-compose.yml` mounts `../../backend:/app:ro` (read-only)
- Celery Beat attempts to write `celerybeat-schedule` database file to `/app/` directory
- This fails with permission errors because the mount is read-only
- Without the schedule file, Beat cannot track which periodic tasks have run

**Scheduled Tasks Affected:**
From [backend/app/workers/celery_app.py](../../backend/app/workers/celery_app.py):
- `process-outbox-events`: Every 10 seconds - Process outbox for document pipeline
- `reconcile-data-consistency`: Every hour - Ensure data consistency
- `cleanup-processed-outbox-events`: Daily at 3 AM UTC - Clean up processed outbox entries

**Source Documents:**
- [docs/sprint-artifacts/tech-spec-epic-5.md](tech-spec-epic-5.md) - AC-5.13.1 through AC-5.13.5
- [infrastructure/docker/docker-compose.yml](../../infrastructure/docker/docker-compose.yml) - Celery Beat service (lines 178-196)
- [backend/app/workers/celery_app.py](../../backend/app/workers/celery_app.py) - Beat schedule configuration (lines 50-64)

---

## Acceptance Criteria

### AC1: Celery Beat Schedule Directory Created (AC-5.13.1)

**Given** Celery Beat scheduler needs to persist its schedule
**When** the container starts
**Then**:
- Celery Beat writes `celerybeat-schedule` to `/app/celery-data/` directory
- Directory is writable by the celery process
- Schedule file is SQLite database format (Celery default)

**Verification:**
```bash
docker exec lumikb-celery-beat ls -la /app/celery-data/
# Expected: celerybeat-schedule file exists with write permissions
```

---

### AC2: Scheduled Tasks Execute Successfully (AC-5.13.2)

**Given** Celery Beat is running with proper filesystem access
**When** scheduled tasks trigger
**Then**:
- `process-outbox-events` executes every 10 seconds without errors
- `reconcile-data-consistency` executes every hour without errors
- `cleanup-processed-outbox-events` executes daily at 3 AM UTC without errors
- No "Permission denied" or filesystem errors in celery-beat logs

**Verification:**
```bash
docker logs lumikb-celery-beat 2>&1 | grep -i "error\|permission"
# Expected: No permission errors
```

---

### AC3: Schedule File Persists Across Restarts (AC-5.13.3)

**Given** Celery Beat has written schedule data
**When** the container is restarted
**Then**:
- `celerybeat-schedule` file persists in the volume
- Beat resumes with existing schedule state
- No tasks are missed during restart window

**Verification:**
```bash
docker compose restart celery-beat
docker exec lumikb-celery-beat ls -la /app/celery-data/celerybeat-schedule
# Expected: File exists with modification time before restart
```

---

### AC4: Beat Scheduler Initializes Successfully (AC-5.13.4)

**Given** docker-compose starts all services
**When** celery-beat container starts
**Then**:
- Logs show "beat: Starting..."
- Logs show scheduled tasks registered
- No startup errors related to schedule file

**Verification:**
```bash
docker logs lumikb-celery-beat 2>&1 | head -50
# Expected: "beat: Starting..." and task registration messages
```

---

### AC5: No Root-Owned Files Created (AC-5.13.5)

**Given** the container runs with non-root user (if configured)
**When** celery-beat writes to the data directory
**Then**:
- Files in `/app/celery-data/` are owned by the celery process user
- No root-owned files created in working directory
- File permissions allow read/write by the container process

**Verification:**
```bash
docker exec lumikb-celery-beat stat /app/celery-data/celerybeat-schedule
# Expected: File owned by celery user (or container default user)
```

---

## Technical Design

### Solution Overview

1. **Add Named Volume** for celery-beat data persistence
2. **Update Dockerfile** to create `/app/celery-data/` directory
3. **Update celery-beat command** to specify schedule file location
4. **Mount volume** at `/app/celery-data/` instead of relying on read-only mount

### Docker Compose Changes

```yaml
# In docker-compose.yml - Update celery-beat service

celery-beat:
  build:
    context: ../../backend
    dockerfile: Dockerfile
  container_name: lumikb-celery-beat
  command: >
    celery -A app.workers.celery_app beat
    --loglevel=info
    --schedule=/app/celery-data/celerybeat-schedule
  environment:
    LUMIKB_DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-lumikb}:${POSTGRES_PASSWORD:-lumikb_dev_password}@postgres:5432/${POSTGRES_DB:-lumikb}
    LUMIKB_REDIS_URL: redis://redis:6379/0
    LUMIKB_CELERY_BROKER_URL: redis://redis:6379/0
    LUMIKB_CELERY_RESULT_BACKEND: redis://redis:6379/0
  volumes:
    - ../../backend:/app:ro
    - celery_beat_data:/app/celery-data  # NEW: Writable volume for schedule file
  networks:
    - lumikb-network
  depends_on:
    redis:
      condition: service_healthy
  restart: unless-stopped

# Add to volumes section:
volumes:
  # ... existing volumes ...
  celery_beat_data:
    name: lumikb-celery-beat-data
```

### Dockerfile Changes

```dockerfile
# In backend/Dockerfile - Add celery-data directory

# ... existing content ...

# Create directory for Celery Beat schedule file
RUN mkdir -p /app/celery-data && chmod 777 /app/celery-data

# ... rest of Dockerfile ...
```

### Alternative: Use Redis for Beat Schedule

If volume-based persistence is problematic, Celery Beat can use Redis for schedule storage:

```python
# In celery_app.py - Alternative using Redis scheduler
celery_app.conf.update(
    beat_scheduler='celery.beat:PersistentScheduler',
    beat_schedule_filename='/app/celery-data/celerybeat-schedule',
)
```

However, the file-based approach is simpler and recommended for development environments.

---

## Tasks / Subtasks

### Task 1: Update Dockerfile (AC: #1, #5)

- [ ] Add `RUN mkdir -p /app/celery-data` to backend Dockerfile
- [ ] Set appropriate permissions: `chmod 755 /app/celery-data`
- [ ] Ensure directory created in runtime stage (not just builder)
- [ ] **Estimated Time:** 15 minutes

### Task 2: Update docker-compose.yml (AC: #1, #3)

- [ ] Add `celery_beat_data` named volume to volumes section
- [ ] Update `celery-beat` service volumes to mount `celery_beat_data:/app/celery-data`
- [ ] Update `command` to specify `--schedule=/app/celery-data/celerybeat-schedule`
- [ ] **Estimated Time:** 15 minutes

### Task 3: Rebuild and Test (AC: #2, #4)

- [ ] Rebuild celery-beat container: `docker compose build celery-beat`
- [ ] Restart services: `docker compose up -d celery-beat`
- [ ] Verify schedule file created: `docker exec lumikb-celery-beat ls -la /app/celery-data/`
- [ ] Check logs for successful initialization: `docker logs lumikb-celery-beat`
- [ ] **Estimated Time:** 15 minutes

### Task 4: Test Persistence Across Restarts (AC: #3)

- [ ] Note modification time of schedule file
- [ ] Restart celery-beat: `docker compose restart celery-beat`
- [ ] Verify schedule file persists
- [ ] Verify no task execution gaps in logs
- [ ] **Estimated Time:** 10 minutes

### Task 5: Verify No Permission Errors (AC: #2, #5)

- [ ] Run celery-beat for 1+ minute
- [ ] Grep logs for permission errors: `docker logs lumikb-celery-beat 2>&1 | grep -i permission`
- [ ] Verify file ownership is non-root (if applicable)
- [ ] **Estimated Time:** 10 minutes

### Task 6: Update .gitignore (if needed)

- [ ] Ensure `celerybeat-schedule` is in `.gitignore` (already present)
- [ ] Verify no schedule files committed accidentally
- [ ] **Estimated Time:** 5 minutes

---

## Dev Notes

### Files to Modify

**Infrastructure:**
- `infrastructure/docker/docker-compose.yml` - Add volume, update celery-beat command
- `backend/Dockerfile` - Create `/app/celery-data/` directory

### Files to Verify

- `.gitignore` - Should already include `celerybeat-schedule` pattern

### Testing Commands

```bash
# Rebuild celery-beat image
cd /home/tungmv/Projects/LumiKB/infrastructure/docker
docker compose build celery-beat

# Start services
docker compose up -d

# Verify schedule file exists
docker exec lumikb-celery-beat ls -la /app/celery-data/

# Check logs for initialization
docker logs lumikb-celery-beat 2>&1 | head -50

# Check for permission errors
docker logs lumikb-celery-beat 2>&1 | grep -i "error\|permission\|denied"

# Test persistence
docker compose restart celery-beat
docker exec lumikb-celery-beat ls -la /app/celery-data/celerybeat-schedule

# Verify scheduled tasks are running (check worker logs)
docker logs lumikb-celery-worker 2>&1 | grep -i "process_outbox_events"
```

### Dependencies

- No new dependencies required
- Uses existing Celery configuration

### Rollback Plan

If issues arise:
1. Remove volume mount from docker-compose.yml
2. Remove `--schedule` flag from command
3. Celery Beat will use in-memory schedule (loses persistence but works)

### Considerations

1. **Volume Cleanup:** Named volume persists across `docker compose down`. Use `docker compose down -v` to remove volumes if needed for clean slate.

2. **Multi-Instance Beat:** Celery Beat should only run one instance. File-based schedule is appropriate for single-instance deployments.

3. **Production Deployment:** For Kubernetes/production, consider using Redis-based scheduler (`celery_beat:RedisScheduler`) for distributed persistence.

### Learnings from Previous Story (5-12)

Story 5-12 (ATDD Integration Tests Transition to GREEN) established test infrastructure patterns:

- **Test Helpers Created:** `backend/tests/helpers/qdrant_helpers.py` and `backend/tests/helpers/document_helpers.py` provide reusable fixtures
- **Testcontainer Patterns:** PostgresContainer, RedisContainer, QdrantContainer for isolated integration testing
- **Graceful Degradation:** Tests handle service unavailability gracefully (e.g., LLM skips)

For Story 5-13, manual Docker verification is the appropriate testing approach given the infrastructure focus. The testcontainer patterns from 5-12 are not directly applicable since this story modifies the Docker Compose configuration itself rather than application code.

[Source: docs/sprint-artifacts/5-12-atdd-integration-tests-transition-to-green.md - Dev Agent Record, File List section]

---

## Definition of Done

- [x] **Schedule Directory (AC1):**
  - [x] `/app/celery-data/` directory exists in container
  - [x] `celerybeat-schedule` file created successfully (16384 bytes SQLite database)
  - [x] Directory writable by celery process

- [x] **Tasks Execute (AC2):**
  - [x] `process-outbox-events` triggers every 10 seconds
  - [x] No permission errors in celery-beat logs
  - [x] Worker logs show tasks being processed

- [x] **Persistence (AC3):**
  - [x] Named volume `lumikb-celery-beat-data` created
  - [x] Schedule file persists across container restarts
  - [x] No data loss on restart

- [x] **Initialization (AC4):**
  - [x] "beat: Starting..." appears in logs
  - [x] Scheduled tasks registered in startup logs
  - [x] No startup errors

- [x] **File Ownership (AC5):**
  - [x] Files in `/app/celery-data/` owned by root (container default user)
  - [x] Files accessible by container process (0644 permissions)

- [x] **Code Quality:**
  - [x] docker-compose.yml changes follow existing patterns
  - [x] Dockerfile changes are minimal and clean
  - [x] No hardcoded paths outside of infrastructure files

---

## FR Traceability

**Functional Requirements Addressed:**

| FR | Requirement | How Satisfied |
|----|-------------|---------------|
| N/A | Technical debt | Enables reliable execution of scheduled tasks from Epic 2 |

**Non-Functional Requirements:**

- **Reliability:** Scheduled tasks run consistently without filesystem errors
- **Persistence:** Schedule state survives container restarts
- **Maintainability:** Uses Docker best practices for volume management

---

## Story Size Estimate

**Story Points:** 2

**Rationale:**
- Small scope: Only 2 files to modify (Dockerfile, docker-compose.yml)
- Low complexity: Standard Docker volume configuration
- Low risk: Changes are isolated to celery-beat service
- Quick verification: Docker commands to verify fix

**Estimated Effort:** 1-1.5 hours

**Breakdown:**
- Task 1: Dockerfile update (15m)
- Task 2: docker-compose.yml update (15m)
- Task 3: Rebuild and test (15m)
- Task 4: Test persistence (10m)
- Task 5: Verify permissions (10m)
- Task 6: Update .gitignore (5m)

---

## Change Log

| Date | Author | Change | Reason |
|------|--------|--------|--------|
| 2025-12-03 | SM Agent (Bob) | Story created | Initial draft from tech-spec-epic-5.md |
| 2025-12-03 | Dev Agent (Amelia) | Story completed | Implementation and verification complete |

---

**Story Created By:** SM Agent (Bob)

---

## References

- [docs/sprint-artifacts/tech-spec-epic-5.md](tech-spec-epic-5.md) - AC-5.13.1 through AC-5.13.5
- [docs/epics.md](../epics.md) - Story 5.13 definition (lines 2284-2347), root cause analysis, solution options
- [infrastructure/docker/docker-compose.yml](../../infrastructure/docker/docker-compose.yml) - Celery Beat service (lines 178-196)
- [backend/app/workers/celery_app.py](../../backend/app/workers/celery_app.py) - Beat schedule configuration (lines 50-64)
- [docs/architecture.md](../architecture.md) - Infrastructure overview, Transactional Outbox section

---

## Dev Agent Record

### Context Reference

- [5-13-celery-beat-filesystem-fix.context.xml](5-13-celery-beat-filesystem-fix.context.xml) - Generated 2025-12-03

### Agent Model Used

- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Docker overlay mount issue: Initial approach with read-only bind mount + volume overlay failed
- Solution: Removed read-only bind mount for celery-beat service (uses baked-in code from Dockerfile)

### Completion Notes List

1. **Issue Encountered**: Docker cannot overlay a named volume onto a read-only bind mount. The original design tried to mount `../../backend:/app:ro` and then overlay `celery_beat_data:/app/celery-data`, but Docker cannot create the mountpoint on a read-only filesystem.

2. **Solution Applied**: Removed the read-only bind mount from celery-beat service. The Dockerfile already copies the application code during build, so the bind mount is not needed for celery-beat (unlike celery-worker which benefits from hot-reload during development).

3. **Verification Results**:
   - AC1: `/app/celery-data/celerybeat-schedule` created successfully (16384 bytes SQLite database)
   - AC2: `process-outbox-events` executes every 10 seconds without errors
   - AC3: Schedule file persists across container restarts
   - AC4: "beat: Starting..." and task registration messages appear in logs
   - AC5: Files owned by root (container default user) with 0644 permissions

### File List

**Modified:**
- `infrastructure/docker/docker-compose.yml` - Removed read-only bind mount from celery-beat, added celery_beat_data volume
- `backend/Dockerfile` - Added `/app/celery-data/` directory creation with chmod 755

**Verified:**
- `.gitignore` - Contains `celerybeat-schedule` pattern (line 76)
