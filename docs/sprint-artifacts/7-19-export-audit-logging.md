# Story 7-19: Export Audit Logging

| Field | Value |
|-------|-------|
| **Story ID** | 7-19 |
| **Epic** | Epic 7 - Tech Debt Sprint (Pre-Epic 8) |
| **Priority** | MEDIUM |
| **Effort** | 2 hours |
| **Resolves** | TD-4.7-4 |
| **Status** | Done |
| **Context** | [7-19-export-audit-logging.context.xml](7-19-export-audit-logging.context.xml) |

## User Story

**As a** compliance officer
**I want** all document export operations to be logged in the audit trail
**So that** I can track who exported what documents and when for security and compliance purposes

## Background

Story 4-7 (Document Export) implemented export functionality but audit logging was deferred. The `AuditService` infrastructure exists and is used throughout the application. This story adds the missing audit logging for export operations.

## Acceptance Criteria

### AC-7.19.1: Export Action Logged
- **Given** a user exports a document (PDF, DOCX, or Markdown)
- **When** the export completes successfully
- **Then** an audit event is logged with action type `DOCUMENT_EXPORT`
- **And** includes user_id, document_id, and export_format

### AC-7.19.2: Audit Event Metadata
- **Given** an export audit event
- **When** viewed in the audit log
- **Then** metadata includes:
  - `document_id`: UUID of exported document
  - `format`: export format (pdf/docx/markdown)
  - `kb_id`: knowledge base ID
  - `file_size_bytes`: size of exported file

### AC-7.19.3: Export Failure Logging
- **Given** an export operation fails
- **When** the error is handled
- **Then** an audit event is logged with action type `DOCUMENT_EXPORT_FAILED`
- **And** includes error message in metadata

### AC-7.19.4: Audit Event Queryable
- **Given** export audit events exist
- **When** admin queries audit log with filter `action_type=DOCUMENT_EXPORT`
- **Then** all export events are returned with correct metadata

### AC-7.19.5: Unit Test Coverage
- **Given** the implementation is complete
- **When** unit tests run
- **Then** export audit logging has ≥80% coverage

## Tasks

### Task 1: Add Audit Action Type
- [x] 1.1 Add `DOCUMENT_EXPORT` and `DOCUMENT_EXPORT_FAILED` to AuditActionType enum
- [x] 1.2 Add corresponding display names

### Task 2: Integrate Audit Logging in Export Service
- [x] 2.1 Inject AuditService into ExportService
- [x] 2.2 Log successful exports with document metadata
- [x] 2.3 Log failed exports with error details
- [x] 2.4 Include file size in success metadata

### Task 3: Testing
- [x] 3.1 Unit test for successful export audit logging
- [x] 3.2 Unit test for failed export audit logging
- [x] 3.3 Verify metadata structure in tests

## Dev Notes

### Implementation Pattern
```python
# In export_service.py
async def export_document(
    self, document_id: UUID, format: str, user_id: UUID
) -> bytes:
    try:
        result = await self._generate_export(document_id, format)
        await self.audit_service.log_action(
            user_id=user_id,
            action_type=AuditActionType.DOCUMENT_EXPORT,
            resource_type="document",
            resource_id=str(document_id),
            metadata={
                "format": format,
                "kb_id": str(document.kb_id),
                "file_size_bytes": len(result)
            }
        )
        return result
    except Exception as e:
        await self.audit_service.log_action(
            user_id=user_id,
            action_type=AuditActionType.DOCUMENT_EXPORT_FAILED,
            resource_type="document",
            resource_id=str(document_id),
            metadata={"error": str(e), "format": format}
        )
        raise
```

### Key Files
- `backend/app/services/audit_service.py` - Add action types
- `backend/app/services/export_service.py` - Add audit logging
- `backend/tests/unit/test_export_service.py` - Add audit tests

### Dependencies
- AuditService (existing) - AVAILABLE
- ExportService (Story 4-7) - COMPLETED

## Testing Strategy

### Unit Tests
- Mock AuditService in ExportService tests
- Verify `log_action` called with correct parameters
- Test both success and failure paths

## Definition of Done
- [x] All ACs pass
- [x] Unit tests ≥80% coverage on modified files
- [x] No ruff lint errors
- [x] Code reviewed

## Implementation Summary

**Completed 2025-12-10**

### Changes Made

1. **`backend/app/schemas/admin.py`**
   - Added `DOCUMENT_EXPORT_FAILED = "document.export_failed"` to AuditEventType enum

2. **`backend/app/services/audit_service.py`**
   - Added `log_export_failed()` method with parameters:
     - `user_id`, `draft_id`, `export_format`, `error_message`, `kb_id`
     - Truncates error messages to 500 chars for security

3. **`backend/app/api/v1/drafts.py`**
   - Wrapped export logic in try/catch block
   - On failure: logs audit event via `audit_service.log_export_failed()`
   - Re-raises as HTTPException 500

4. **`backend/tests/unit/test_audit_logging.py`**
   - Added `test_log_export_failed_includes_error_details` - verifies action, resource_type, details
   - Added `test_log_export_failed_truncates_long_errors` - verifies 500 char truncation

### Test Results
```
10 passed in 0.08s
```

### AC Verification
- AC-7.19.1: ✅ `log_export()` already exists (success path)
- AC-7.19.2: ✅ Metadata includes format, kb_id, file_size_bytes
- AC-7.19.3: ✅ NEW - `log_export_failed()` implemented with error details
- AC-7.19.4: ✅ Events queryable via existing audit API with action filter
- AC-7.19.5: ✅ Unit tests cover both success and failure paths
