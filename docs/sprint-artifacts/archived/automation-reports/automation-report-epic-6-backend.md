# Epic 6: Document Lifecycle Management - Backend Test Automation Report

**Date:** 2025-12-07
**Epic:** 6 - Document Lifecycle Management
**Scope:** Stories 6-1 through 6-6 (Backend API Integration Tests)
**Status:** Test Files Created - Ready for Code Review

---

## Executive Summary

This report documents the automated integration tests created for Epic 6 backend stories. All 6 stories have corresponding test files covering their acceptance criteria. Tests are designed for execution with testcontainers (PostgreSQL, Qdrant, MinIO) in Docker.

| Story | Test File | Tests | Status |
|-------|-----------|-------|--------|
| 6-1 Archive Document | `test_archive_api.py` | 23 | Created |
| 6-2 Restore Document | `test_restore_api.py` | 15 | Created |
| 6-3 Purge Document | `test_purge_api.py` | 15 | Created |
| 6-4 Clear Failed Document | `test_clear_failed_api.py` | 15 | Created |
| 6-5 Duplicate Detection | `test_duplicate_detection_api.py` | 12 | Created |
| 6-6 Replace Document | `test_replace_document_api.py` | 18 | Created |

**Total Tests Created:** ~98 integration tests

---

## Story 6-1: Archive Document Backend

**Test File:** `backend/tests/integration/test_archive_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.1.1 | Archive endpoint sets `archived_at` | `TestArchiveEndpoint` | 5 |
| AC-6.1.2 | Only READY documents can be archived | `TestArchiveStatusValidation` | 5 |
| AC-6.1.3 | Qdrant vectors marked `archived=true` | `TestQdrantArchivePayload` | 2 |
| AC-6.1.4 | Bulk archive endpoint | `TestBulkArchive` | 2 (skipped) |
| AC-6.1.5 | Permission check (403/404) | `TestArchivePermissions` | 5 |
| AC-6.1.6 | Audit logging | `TestArchiveAuditLogging` | 2 |

### Key Test Scenarios

```python
# Endpoint behavior
test_archive_ready_document_returns_200
test_archive_sets_archived_at_timestamp
test_archive_response_contains_required_fields
test_archive_nonexistent_document_returns_404

# Status validation
test_archive_pending_document_returns_400
test_archive_processing_document_returns_400
test_archive_failed_document_returns_400
test_archive_already_archived_returns_400
test_archive_same_document_twice_returns_400

# Qdrant integration
test_archive_updates_qdrant_payload
test_archived_document_excluded_from_search

# Permissions
test_archive_without_authentication_returns_401
test_archive_without_kb_access_returns_404
test_archive_with_read_only_permission_returns_404
test_archive_with_write_permission_succeeds
test_kb_owner_can_archive

# Audit
test_archive_creates_audit_log_entry
test_archive_audit_contains_required_fields
```

---

## Story 6-2: Restore Document Backend

**Test File:** `backend/tests/integration/test_restore_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.2.1 | Restore endpoint clears `archived_at` | `TestRestoreEndpoint` | 4 |
| AC-6.2.2 | Only archived documents can be restored | `TestRestoreStatusValidation` | 3 |
| AC-6.2.3 | Name collision detection (409) | `TestRestoreNameCollision` | 2 |
| AC-6.2.4 | Qdrant vectors marked `archived=false` | `TestRestoreQdrantPayload` | 1 |
| AC-6.2.5 | Permission check | `TestRestorePermissions` | 3 |
| AC-6.2.6 | Audit logging | `TestRestoreAuditLogging` | 1 |

### Key Test Scenarios

```python
# Endpoint behavior
test_restore_archived_document_returns_200
test_restore_clears_archived_at
test_restore_response_contains_document_info
test_restore_nonexistent_document_returns_404

# Status validation
test_restore_ready_document_returns_400
test_restore_pending_document_returns_400
test_restore_already_restored_returns_400

# Name collision
test_restore_with_name_collision_returns_409
test_restore_without_collision_succeeds

# Qdrant integration
test_restore_updates_qdrant_payload

# Permissions
test_restore_without_authentication_returns_401
test_restore_without_kb_access_returns_404
test_restore_with_write_permission_succeeds
```

---

## Story 6-3: Purge Document Backend

**Test File:** `backend/tests/integration/test_purge_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.3.1 | Purge deletes archived document permanently | `TestPurgeEndpoint` | 3 |
| AC-6.3.2 | Only archived documents can be purged | `TestPurgeStatusValidation` | 3 |
| AC-6.3.3 | Multi-layer cleanup (PG, Qdrant, MinIO) | `TestPurgeStorageCleanup` | 2 |
| AC-6.3.4 | Permission check | `TestPurgePermissions` | 3 |
| AC-6.3.5 | Bulk purge endpoint | `TestBulkPurge` | 2 (skipped) |
| AC-6.3.6 | Graceful missing artifact handling | `TestPurgeGracefulHandling` | 1 |

### Key Test Scenarios

```python
# Endpoint behavior
test_purge_archived_document_returns_200
test_purge_removes_document_from_database
test_purge_nonexistent_document_returns_404

# Status validation
test_purge_ready_document_returns_400
test_purge_pending_document_returns_400
test_purge_failed_document_returns_400

# Storage cleanup
test_purge_deletes_from_postgresql
test_purge_document_no_longer_accessible

# Permissions
test_purge_without_authentication_returns_401
test_purge_without_kb_access_returns_404
test_purge_with_write_permission_succeeds

# Graceful handling
test_purge_succeeds_even_if_qdrant_empty
```

---

## Story 6-4: Clear Failed Document Backend

**Test File:** `backend/tests/integration/test_clear_failed_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.4.1 | Clear endpoint removes failed document | `TestClearEndpoint` | 3 |
| AC-6.4.2 | Only FAILED documents can be cleared | `TestClearStatusValidation` | 3 |
| AC-6.4.3 | All partial artifacts removed | `TestClearArtifactCleanup` | 2 |
| AC-6.4.4 | Permission check | `TestClearPermissions` | 4 |
| AC-6.4.5 | Graceful missing artifact handling | `TestClearGracefulHandling` | 2 |

### Key Test Scenarios

```python
# Endpoint behavior
test_clear_failed_document_returns_200
test_clear_removes_document_from_database
test_clear_nonexistent_document_returns_404

# Status validation
test_clear_ready_document_returns_400
test_clear_pending_document_returns_400
test_clear_processing_document_returns_400

# Artifact cleanup
test_clear_removes_postgresql_record
test_cleared_document_no_longer_accessible

# Permissions
test_clear_without_authentication_returns_401
test_clear_without_kb_access_returns_404
test_clear_with_write_permission_succeeds
test_kb_owner_can_clear

# Graceful handling
test_clear_succeeds_with_no_qdrant_vectors
test_clear_succeeds_with_no_minio_file
```

---

## Story 6-5: Duplicate Detection & Auto-Clear Backend

**Test File:** `backend/tests/integration/test_duplicate_detection_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.5.1 | Case-insensitive duplicate detection | `TestCaseInsensitiveDuplicateDetection` | 3 |
| AC-6.5.2 | 409 for completed/archived duplicates | `TestCompletedArchivedDuplicates` | 2 |
| AC-6.5.3 | Auto-clear failed duplicates | `TestAutoClearFailedDuplicates` | 2 |
| AC-6.5.4 | Pending/processing duplicates blocked | `TestPendingProcessingDuplicates` | 2 |
| AC-6.5.5 | Different KB allows same name | `TestDifferentKBAllowsSameName` | 2 |

### Key Test Scenarios

```python
# Case-insensitive detection
test_duplicate_detected_same_case
test_duplicate_detected_different_case
test_duplicate_detected_mixed_case

# Completed/archived duplicates
test_completed_duplicate_returns_409_with_details
test_archived_duplicate_returns_409

# Auto-clear failed
test_failed_duplicate_auto_cleared_and_upload_succeeds
test_auto_clear_creates_audit_log

# Pending/processing blocked
test_pending_duplicate_returns_409
test_processing_duplicate_returns_409

# Cross-KB upload
test_same_name_different_kb_succeeds
test_unique_name_upload_succeeds
```

---

## Story 6-6: Replace Document Backend

**Test File:** `backend/tests/integration/test_replace_document_api.py`

### Acceptance Criteria Coverage

| AC | Description | Test Class | Tests |
|----|-------------|------------|-------|
| AC-6.6.1 | Replace endpoint exists | `TestReplaceEndpoint` | 4 |
| AC-6.6.3 | Replace preserves ID/metadata | `TestReplacePreservesMetadata` | 3 |
| AC-6.6.4 | Cannot replace while processing | `TestReplaceWhileProcessing` | 2 |
| AC-6.6.5 | Permission check | `TestReplacePermissions` | 3 |
| AC-6.6.6 | Replace triggers reprocessing | `TestReplaceTriggersReprocessing` | 3 |

### Key Test Scenarios

```python
# Endpoint behavior
test_replace_ready_document_returns_200
test_replace_failed_document_returns_200
test_replace_archived_document_returns_200
test_replace_nonexistent_document_returns_404

# Metadata preservation
test_replace_preserves_document_id
test_replace_preserves_created_at
test_replace_updates_name_to_new_filename

# Processing block
test_replace_processing_document_returns_400
test_replace_pending_document_returns_400

# Permissions
test_replace_without_authentication_returns_401
test_replace_without_kb_access_returns_404
test_replace_with_write_permission_succeeds

# Reprocessing trigger
test_replace_sets_status_to_pending
test_replace_response_indicates_pending_status
test_replace_clears_archived_at
```

---

## API Endpoints Under Test

| Method | Endpoint | Story |
|--------|----------|-------|
| POST | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive` | 6-1 |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore` | 6-2 |
| DELETE | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge` | 6-3 |
| DELETE | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear` | 6-4 |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents/` | 6-5 (upload with detection) |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace` | 6-6 |

---

## Test Fixtures Summary

All test files use consistent async fixtures:

### Common Fixtures

| Fixture | Purpose |
|---------|---------|
| `api_client` | AsyncClient for HTTP requests |
| `db_session` | AsyncSession for database operations |
| `test_user_data` | Primary test user with authentication cookies |
| `second_user_data` | Secondary user for permission testing |
| `test_qdrant_service` | Qdrant test service for vector operations |

### Story-Specific Fixtures

| Story | Fixture | Documents Created |
|-------|---------|-------------------|
| 6-1 | `archive_test_kb` | READY, PENDING, PROCESSING, FAILED, archived |
| 6-2 | `restore_test_kb` | archived, READY, PENDING, collision pair |
| 6-3 | `purge_test_kb` | 2x archived, READY, PENDING, FAILED |
| 6-4 | `clear_test_kb` | 2x FAILED, READY, PENDING, PROCESSING |
| 6-5 | `duplicate_test_kb` | READY, archived, PENDING, PROCESSING, FAILED |
| 6-6 | `replace_test_kb` | READY, FAILED, archived, PROCESSING, PENDING |

---

## Test Execution Instructions

### Prerequisites

1. Docker Desktop running
2. Python virtual environment activated
3. Dependencies installed

### Running Tests

```bash
cd backend

# Run all Epic 6 tests
DOCKER_HOST=unix:///home/tungmv/.docker/desktop/docker.sock \
TESTCONTAINERS_RYUK_DISABLED=true \
timeout 300 .venv/bin/pytest tests/integration/test_archive_api.py \
    tests/integration/test_restore_api.py \
    tests/integration/test_purge_api.py \
    tests/integration/test_clear_failed_api.py \
    tests/integration/test_duplicate_detection_api.py \
    tests/integration/test_replace_document_api.py \
    -v --tb=short

# Run individual story tests
DOCKER_HOST=unix:///home/tungmv/.docker/desktop/docker.sock \
TESTCONTAINERS_RYUK_DISABLED=true \
timeout 180 .venv/bin/pytest tests/integration/test_archive_api.py -v
```

---

## Dependencies

### Required Imports (Common)

```python
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from tests.factories import create_registration_data
```

### Additional Dependencies (Per Story)

- **6-1, 6-2:** `tests.helpers.qdrant_helpers.create_test_chunk`
- **6-5, 6-6:** `io.BytesIO` for file upload testing
- **All:** `app.models.audit.AuditEvent` for audit verification

---

## Notes for Code Review

### Implementation Requirements

1. **API Endpoints**: Ensure all endpoints listed above exist with correct HTTP methods
2. **Status Validation**: Each endpoint must validate document status before operation
3. **Error Responses**: Use standard error format:
   ```json
   {
     "detail": {
       "error": {
         "code": "ERROR_CODE",
         "message": "Human readable message",
         "details": {}
       }
     }
   }
   ```
4. **Audit Logging**: All actions must create audit log entries
5. **Permission Checks**: WRITE permission required for all mutating operations
6. **Multi-Layer Cleanup**: Purge/Clear must handle PostgreSQL, Qdrant, and MinIO

### Skipped Tests

The following tests are marked as `@pytest.mark.skip`:
- `TestBulkArchive.test_bulk_archive_multiple_documents` - Bulk endpoint not implemented
- `TestBulkArchive.test_bulk_archive_partial_failure` - Bulk endpoint not implemented
- `TestBulkPurge.test_bulk_purge_multiple_archived_documents` - Bulk endpoint not implemented
- `TestBulkPurge.test_bulk_purge_partial_success` - Bulk endpoint not implemented

Enable these tests when bulk operations are implemented.

### Expected Error Codes

| Code | Usage |
|------|-------|
| `INVALID_STATUS` | Document status doesn't allow operation |
| `ALREADY_ARCHIVED` | Document already archived |
| `NOT_ARCHIVED` | Document not archived (for restore/purge) |
| `NOT_FAILED` | Document not failed (for clear) |
| `PROCESSING_IN_PROGRESS` | Cannot modify processing document |
| `NAME_COLLISION` | Active document with same name exists |
| `DUPLICATE_DOCUMENT` | Duplicate detection triggered |

---

## Handover Checklist

- [x] Test files created for all 6 stories
- [x] Acceptance criteria mapped to test classes
- [x] Fixtures created for test data setup
- [x] Permission tests included
- [x] Audit logging tests included
- [x] Error response format tests included
- [x] Test execution instructions documented
- [ ] Tests executed and passing (pending E2E test run)
- [ ] Code review completed
- [ ] Backend endpoints implemented

---

*Generated by TEA (Test Engineer Agent) - 2025-12-07*
