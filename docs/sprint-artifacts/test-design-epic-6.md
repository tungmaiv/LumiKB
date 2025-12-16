# Test Design: Epic 6 - Document Lifecycle Management

**Date:** 2025-12-07
**Author:** Murat (Master Test Architect)
**Status:** Draft
**Epic ID:** epic-6

---

## Executive Summary

**Scope:** Full test design for Epic 6 (Document Lifecycle Management - Archive, Restore, Purge, Clear Failed, Duplicate Detection, Replace)

**Risk Summary:**

- Total risks identified: 12
- High-priority risks (score ≥6): 5
- Critical categories: DATA, SEC, OPS, TECH, BUS

**Coverage Summary:**

- P0 scenarios: 28 (56 hours)
- P1 scenarios: 38 (38 hours)
- P2/P3 scenarios: 26 (13 hours)
- **Total effort**: 107 hours (~14 days)

**Stories Covered:**
- Story 6.1: Archive Document Backend (3 pts)
- Story 6.2: Restore Document Backend (3 pts)
- Story 6.3: Purge Document Backend (5 pts)
- Story 6.4: Clear Failed Document Backend (3 pts)
- Story 6.5: Duplicate Detection & Auto-Clear Backend (5 pts)
- Story 6.6: Replace Document Backend (5 pts)
- Story 6.7: Archive Management UI (5 pts)
- Story 6.8: Document List Archive/Clear Actions UI (3 pts)
- Story 6.9: Duplicate Upload & Replace UI (3 pts)

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R6-001 | DATA | Purge operation fails to delete all artifacts (MinIO, Qdrant, PostgreSQL) leaving orphaned data | 2 | 3 | 6 | Transactional purge with rollback, comprehensive artifact tracking, cleanup verification | Dev | Before 6.3 |
| R6-002 | DATA | Restore fails when original Qdrant collection modified, embeddings lost permanently | 2 | 3 | 6 | Store embedding IDs, re-embedding fallback, verify vector integrity on restore | Dev | Before 6.2 |
| R6-003 | SEC | Non-owner users can archive/purge documents they shouldn't have access to | 2 | 3 | 6 | KB permission checks on all operations, role-based access validation | Dev | Before 6.1 |
| R6-004 | OPS | Bulk archive/purge of 100+ documents causes timeout or partial completion | 3 | 2 | 6 | Background task queue, progress tracking, partial success handling | Dev | Before 6.7 |
| R6-005 | BUS | Accidental purge of critical documents with no recovery option | 2 | 3 | 6 | Soft delete first (archive), confirmation modal with type-to-confirm, audit logging | QA | Before 6.3 |

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R6-006 | TECH | Duplicate detection hash collision causes false positives | 2 | 2 | 4 | SHA256 + file size comparison, content sampling for large files | Dev |
| R6-007 | DATA | Name collision on restore when active document has same name | 2 | 2 | 4 | Automatic rename with suffix, user choice dialog | Dev |
| R6-008 | PERF | Archive stats query slow with 10K+ archived documents | 2 | 2 | 4 | Indexed queries, materialized views, Redis caching | Dev |
| R6-009 | UX | Replace operation UX confusing, users unsure about data preservation | 2 | 2 | 4 | Clear confirmation dialogs, preview what will be replaced | QA |
| R6-010 | TECH | Auto-clear of failed documents removes documents user wanted to retry | 2 | 2 | 4 | 24-hour grace period before auto-clear, opt-in setting | Dev |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R6-011 | UX | Archive management page empty state confusing | 1 | 1 | 1 | Monitor |
| R6-012 | OPS | Bulk operations don't show progress | 1 | 2 | 2 | Add progress indicator |

### Risk Category Legend

- **DATA**: Data Integrity (orphaned artifacts, lost embeddings, incomplete purge)
- **SEC**: Security (permission bypass, unauthorized access)
- **PERF**: Performance (bulk operations, query timeouts)
- **OPS**: Operations (background tasks, partial failures)
- **BUS**: Business Impact (accidental data loss, user confusion)
- **TECH**: Technical (hash collisions, race conditions)
- **UX**: User Experience (confusing workflows, unclear feedback)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks MVP delivery + High risk (≥6) + Data integrity critical

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 6.1: Archive sets document status correctly | API | R6-003 | 4 | QA | Status transition, permission checks |
| Story 6.2: Restore returns document to active | API | R6-002 | 4 | QA | Status transition, embedding verification |
| Story 6.3: Purge deletes all artifacts | API | R6-001, R6-005 | 6 | QA | MinIO, Qdrant, PostgreSQL cleanup |
| Story 6.4: Clear failed removes partial data | API | - | 3 | QA | Artifact cleanup for failed docs |
| Story 6.5: Duplicate detection accuracy | API | R6-006 | 5 | QA | Hash matching, name matching, false positives |
| Story 6.6: Replace preserves document identity | API | R6-002 | 4 | QA | Same ID, metadata preserved, old archived |
| Story 6.7: Archive page permission checks | E2E | R6-003 | 2 | QA | KB owner/admin only |

**Total P0**: 28 tests, 56 hours (2h each for complex data integrity tests)

### P1 (High) - Run on PR to main

**Criteria**: Important workflows + Medium risk (3-5) + Common user actions

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 6.1: Archive preserves searchability (excluded) | Integration | - | 2 | QA | Archived docs not in search |
| Story 6.2: Name collision handling | API | R6-007 | 3 | QA | Rename, replace, cancel options |
| Story 6.3: Purge confirmation flow | E2E | R6-005 | 2 | QA | Type-to-confirm dialog |
| Story 6.4: Failed document error display | E2E | - | 2 | QA | Error reason visible |
| Story 6.5: Auto-clear timing | Integration | R6-010 | 2 | QA | 24-hour grace period |
| Story 6.6: Version history tracking | API | - | 2 | QA | Audit trail for replacements |
| Story 6.7: Archive filtering & search | E2E | - | 4 | QA | Status, date, name filters |
| Story 6.7: Bulk operations | E2E | R6-004 | 4 | QA | Multi-select, progress |
| Story 6.8: Document list actions | E2E | - | 5 | QA | Archive, clear buttons |
| Story 6.9: Duplicate upload flow | E2E | - | 6 | QA | Detection, options, replace |
| Story 6.9: Replace confirmation UI | E2E | R6-009 | 4 | QA | Preview, confirm dialog |

**Total P1**: 38 tests, 38 hours (1h average)

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 6.1: Archive audit logging | API | - | 2 | QA | Audit events captured |
| Story 6.2: Restore re-indexing | Integration | - | 2 | QA | Qdrant vectors restored |
| Story 6.3: Purge audit trail | API | - | 2 | QA | Permanent record of deletion |
| Story 6.5: Similar content detection | API | R6-006 | 3 | QA | Content similarity matching |
| Story 6.7: Archive pagination | E2E | R6-008 | 2 | QA | Large archive lists |
| Story 6.7: Mobile responsive | E2E | - | 2 | QA | Archive page on mobile |
| Story 6.8: Keyboard shortcuts | E2E | - | 2 | QA | Archive with keyboard |
| Story 6.9: Drag-and-drop replace | E2E | - | 2 | QA | Drop file to replace |

**Total P2**: 17 tests, 8.5 hours (0.5h average)

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Bulk purge 1000 documents | Performance | 2 | QA | < 5 minutes |
| Archive stats dashboard | Component | 2 | DEV | Charts render |
| Empty archive state | Component | 2 | DEV | Helpful message |
| Browser back/forward | E2E | 3 | QA | History works |

**Total P3**: 9 tests, 4.5 hours (0.5h average)

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch integration-breaking issues

- [ ] Archive a document via API (Story 6.1, 1min)
- [ ] Restore a document via API (Story 6.2, 1min)
- [ ] Archive management page loads (Story 6.7, 1min)
- [ ] Document list shows archive button (Story 6.8, 1min)

**Total**: 4 scenarios

### P0 Tests (<60 min)

**Purpose**: Critical path validation for data integrity

- [ ] Story 6.1: Archive document status transition (API, 5min)
- [ ] Story 6.1: Archive permission check - owner only (API, 3min)
- [ ] Story 6.2: Restore document to active (API, 5min)
- [ ] Story 6.2: Restore with embedding verification (API, 8min)
- [ ] Story 6.3: Purge deletes MinIO file (API, 5min)
- [ ] Story 6.3: Purge deletes Qdrant vectors (API, 5min)
- [ ] Story 6.3: Purge deletes PostgreSQL record (API, 3min)
- [ ] Story 6.3: Purge requires archived status (API, 3min)
- [ ] Story 6.4: Clear failed removes partial artifacts (API, 5min)
- [ ] Story 6.5: Exact hash duplicate detected (API, 3min)
- [ ] Story 6.5: Same name duplicate detected (API, 3min)
- [ ] Story 6.5: No false positive for different files (API, 3min)
- [ ] Story 6.6: Replace preserves document UUID (API, 5min)
- [ ] Story 6.6: Replace archives old version (API, 3min)

**Total**: 28 scenarios (~60 min execution)

### P1 Tests (<90 min)

**Purpose**: Important user workflow coverage

- [ ] Story 6.2: Name collision - rename option (API, 5min)
- [ ] Story 6.2: Name collision - replace option (API, 5min)
- [ ] Story 6.3: Type-to-confirm dialog (E2E, 5min)
- [ ] Story 6.5: Auto-clear respects grace period (Integration, 8min)
- [ ] Story 6.7: Filter by archived status (E2E, 3min)
- [ ] Story 6.7: Bulk archive (E2E, 5min)
- [ ] Story 6.7: Bulk restore (E2E, 5min)
- [ ] Story 6.7: Bulk purge (E2E, 8min)
- [ ] Story 6.8: Archive from document list (E2E, 3min)
- [ ] Story 6.8: Clear failed from document list (E2E, 3min)
- [ ] Story 6.9: Duplicate upload shows warning (E2E, 5min)
- [ ] Story 6.9: Replace existing document (E2E, 5min)
- [ ] Story 6.9: Skip duplicate upload (E2E, 3min)
- [+ 25 more P1 tests...]

**Total**: 38 scenarios (~90 min execution)

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage

- [ ] Story 6.1: Archive audit event logged (API, 2min)
- [ ] Story 6.2: Restore triggers re-indexing (Integration, 5min)
- [ ] Story 6.5: Similar content detection (API, 5min)
- [ ] Story 6.7: Archive pagination (E2E, 3min)
- [+ 22 more P2/P3 tests...]

**Total**: 26 scenarios (~60 min execution)

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 28 | 2.0 | 56 | Complex data integrity, multi-artifact cleanup |
| P1 | 38 | 1.0 | 38 | Standard API/E2E workflows |
| P2 | 17 | 0.5 | 8.5 | Edge cases, secondary features |
| P3 | 9 | 0.5 | 4.5 | Exploratory, performance |
| **Buffer (10%)** | - | - | **10.7** | **Unknown unknowns** |
| **Total** | **92** | **-** | **118** | **~15 days** |

### Prerequisites

**Test Data:**

- `archivedDocumentFactory()` - Documents in archived state with various timestamps
- `activeDocumentFactory()` - Completed documents ready for archiving
- `failedDocumentFactory()` - Failed documents with error reasons
- `duplicateFileFactory()` - Files with matching hashes/names for duplicate tests
- `bulkDocumentFactory()` - 100+ documents for bulk operation tests

**Tooling:**

- **Playwright** for E2E (archive page, confirmation dialogs, bulk operations)
- **Vitest** for component tests (archive cards, confirmation modals)
- **pytest** for API tests (archive endpoints, purge verification)
- **MinIO SDK** for storage verification (file existence checks)
- **Qdrant client** for vector verification (collection queries)

**Environment:**

- PostgreSQL with documents in all states (active, archived, failed)
- MinIO with test files uploaded
- Qdrant with indexed documents
- Test KB with owner and non-owner users

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Data integrity paths** (archive/restore/purge): ≥95%
- **Permission checks** (owner/admin validation): 100%
- **Bulk operations** (multi-document actions): ≥90%
- **UI workflows** (E2E critical paths): ≥90%

### Non-Negotiable Requirements

- [ ] All P0 data integrity tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Purge operation verified across all storage backends
- [ ] Permission checks pass 100%
- [ ] No orphaned artifacts after purge

---

## Mitigation Plans

### R6-001: Purge Fails to Delete All Artifacts (Score: 6 - CRITICAL)

**Mitigation Strategy:**
1. **Transactional purge** - PostgreSQL transaction wraps all deletions
2. **Artifact tracking** - Store list of artifact locations (MinIO key, Qdrant IDs)
3. **Cleanup verification** - Post-purge check that all artifacts are gone
4. **Rollback on failure** - If any deletion fails, abort and log error
5. **Manual cleanup tool** - Admin script to find and remove orphaned artifacts

**Owner:** Dev
**Timeline:** Before Story 6.3 completion
**Status:** Planned
**Verification:**
- Purge test deletes document with 50 chunks
- Verify MinIO file gone
- Verify all Qdrant vectors removed
- Verify PostgreSQL record deleted
- Query for orphaned artifacts returns empty

---

### R6-002: Restore Fails When Embeddings Lost (Score: 6)

**Mitigation Strategy:**
1. **Store embedding IDs** - Archive includes Qdrant point IDs
2. **Vector integrity check** - On restore, verify vectors exist in Qdrant
3. **Re-embedding fallback** - If vectors missing, trigger re-processing
4. **User notification** - Alert user if restore requires re-processing
5. **Test with deleted collection** - Verify graceful handling

**Owner:** Dev
**Timeline:** Before Story 6.2 completion
**Status:** Planned
**Verification:**
- Archive document with embeddings
- Delete Qdrant vectors manually
- Restore document
- Verify re-embedding triggered
- Verify document searchable after re-processing

---

### R6-003: Permission Bypass on Archive/Purge (Score: 6)

**Mitigation Strategy:**
1. **KB permission check** - All operations verify user is KB owner or admin
2. **Document ownership** - Verify document belongs to user's accessible KB
3. **Comprehensive auth tests**:
   - KB owner can archive/restore/purge
   - KB reader cannot archive/restore/purge
   - Non-member cannot access operations
   - Admin can perform all operations
4. **Audit logging** - Log all archive/purge with user ID

**Owner:** Dev + QA
**Timeline:** Before Story 6.1 completion
**Status:** Planned
**Verification:**
- 8 authorization test scenarios
- Penetration test for permission escalation
- Audit log review

---

### R6-004: Bulk Operations Timeout (Score: 6)

**Mitigation Strategy:**
1. **Background task queue** - Bulk operations via Celery
2. **Progress tracking** - Real-time progress updates
3. **Partial success handling** - Complete what's possible, report failures
4. **Batch size limits** - Max 100 documents per bulk operation
5. **Timeout configuration** - 5-minute timeout with retry

**Owner:** Dev
**Timeline:** Before Story 6.7 completion
**Status:** Planned
**Verification:**
- Bulk archive 100 documents completes
- Progress indicator updates
- Partial failures reported to user
- No orphaned operations

---

### R6-005: Accidental Purge of Critical Documents (Score: 6)

**Mitigation Strategy:**
1. **Soft delete first** - Documents must be archived before purge
2. **Type-to-confirm** - User types "DELETE" to confirm purge
3. **Audit trail** - Permanent record of all purge operations
4. **Recovery window** - 30-day retention of purge audit entries
5. **Admin notification** - Email admin on bulk purge

**Owner:** QA
**Timeline:** Before Story 6.3 completion
**Status:** Planned
**Verification:**
- Cannot purge active document (400 error)
- Type-to-confirm dialog enforced
- Audit event created on purge
- Admin notification sent for bulk purge

---

## Test Scenario Details

### Story 6.1: Archive Document Backend

**P0 Scenarios (4):**

1. **Archive sets document status to archived**
   - Test Level: API
   - Risk: -
   - Steps:
     1. Create completed document
     2. POST `/api/v1/documents/{id}/archive`
     3. GET document status
   - Validation: status = "archived", archived_at timestamp set

2. **Archive sets archived_by to current user**
   - Test Level: API
   - Risk: -
   - Steps:
     1. Archive document as user A
     2. GET document
   - Validation: archived_by = user A's ID

3. **Archive requires KB owner or admin permission**
   - Test Level: API
   - Risk: R6-003
   - Steps:
     1. Login as KB reader (not owner)
     2. Try to archive document
   - Validation: 403 Forbidden

4. **Archived document excluded from search**
   - Test Level: Integration
   - Risk: -
   - Steps:
     1. Archive document with unique content
     2. Search for that content
   - Validation: Document not in search results

**P1 Scenarios (3):**

5. **Archive audit event logged**
   - Test Level: API
   - Validation: audit.events contains archive action

6. **Cannot archive already archived document**
   - Test Level: API
   - Validation: 400 Bad Request

7. **Cannot archive processing document**
   - Test Level: API
   - Validation: 400 Bad Request, must be completed first

---

### Story 6.2: Restore Document Backend

**P0 Scenarios (4):**

8. **Restore sets status to completed**
   - Test Level: API
   - Risk: -
   - Steps:
     1. Archive document
     2. POST `/api/v1/documents/{id}/restore`
     3. GET document
   - Validation: status = "completed", archived_at = null

9. **Restore clears archived_by**
   - Test Level: API
   - Validation: archived_by = null after restore

10. **Restore requires KB permission**
    - Test Level: API
    - Risk: R6-003
    - Validation: 403 for non-owner

11. **Restored document appears in search**
    - Test Level: Integration
    - Risk: R6-002
    - Steps:
      1. Archive document
      2. Restore document
      3. Search for content
    - Validation: Document in search results

**P1 Scenarios (4):**

12. **Name collision - automatic rename**
    - Test Level: API
    - Risk: R6-007
    - Steps:
      1. Archive "report.pdf"
      2. Upload new "report.pdf"
      3. Restore original
    - Validation: Restored as "report (1).pdf" or user prompted

13. **Name collision - user chooses replace**
    - Test Level: API
    - Validation: Original replaces new, new archived

14. **Name collision - user cancels**
    - Test Level: API
    - Validation: Restore cancelled, document stays archived

15. **Restore audit event logged**
    - Test Level: API
    - Validation: audit.events contains restore action

---

### Story 6.3: Purge Document Backend

**P0 Scenarios (6):**

16. **Purge deletes MinIO file**
    - Test Level: API
    - Risk: R6-001
    - Steps:
      1. Archive document
      2. Note MinIO key
      3. POST `/api/v1/documents/{id}/purge`
      4. Check MinIO
    - Validation: File not found in MinIO

17. **Purge deletes Qdrant vectors**
    - Test Level: API
    - Risk: R6-001
    - Steps:
      1. Archive document with chunks
      2. Note Qdrant point IDs
      3. Purge document
      4. Query Qdrant
    - Validation: Points not found

18. **Purge deletes PostgreSQL record**
    - Test Level: API
    - Risk: R6-001
    - Steps:
      1. Purge document
      2. Query documents table
    - Validation: Document row deleted

19. **Purge requires archived status**
    - Test Level: API
    - Risk: R6-005
    - Steps:
      1. Try to purge active document
    - Validation: 400 Bad Request, "must be archived first"

20. **Purge requires confirmation (type DELETE)**
    - Test Level: API
    - Risk: R6-005
    - Steps:
      1. POST purge without confirmation body
    - Validation: 400 Bad Request, "confirmation required"

21. **Purge creates audit trail**
    - Test Level: API
    - Risk: R6-005
    - Steps:
      1. Purge document
      2. Query audit.events
    - Validation: Purge event with document details preserved

**P1 Scenarios (3):**

22. **Bulk purge via task queue**
    - Test Level: Integration
    - Risk: R6-004
    - Validation: 100 documents purged, progress tracked

23. **Purge permission check**
    - Test Level: API
    - Risk: R6-003
    - Validation: Only KB owner/admin can purge

24. **Partial purge failure handling**
    - Test Level: Integration
    - Validation: Some docs purged, failures reported

---

### Story 6.4: Clear Failed Document Backend

**P0 Scenarios (3):**

25. **Clear removes failed document**
    - Test Level: API
    - Steps:
      1. Upload document that fails processing
      2. POST `/api/v1/documents/{id}/clear`
    - Validation: Document deleted from database

26. **Clear removes partial MinIO upload**
    - Test Level: API
    - Steps:
      1. Document fails after MinIO upload
      2. Clear document
      3. Check MinIO
    - Validation: Partial file removed

27. **Clear only works on failed documents**
    - Test Level: API
    - Steps:
      1. Try to clear completed document
    - Validation: 400 Bad Request

**P1 Scenarios (3):**

28. **Clear all failed in KB**
    - Test Level: API
    - Steps:
      1. KB has 5 failed documents
      2. POST `/api/v1/knowledge-bases/{kb_id}/clear-failed`
    - Validation: All 5 removed

29. **Clear shows failure reason first**
    - Test Level: E2E
    - Validation: Error displayed before clear option

30. **Clear audit logged**
    - Test Level: API
    - Validation: Audit event created

---

### Story 6.5: Duplicate Detection & Auto-Clear Backend

**P0 Scenarios (5):**

31. **Exact hash duplicate detected**
    - Test Level: API
    - Risk: R6-006
    - Steps:
      1. Upload file A
      2. Upload identical file A again
    - Validation: Duplicate warning returned, existing doc ID provided

32. **Same name duplicate detected**
    - Test Level: API
    - Risk: R6-006
    - Steps:
      1. Upload "report.pdf"
      2. Upload different "report.pdf"
    - Validation: Name collision warning

33. **Different files not flagged as duplicate**
    - Test Level: API
    - Risk: R6-006
    - Steps:
      1. Upload file A
      2. Upload file B (different content, different name)
    - Validation: No duplicate warning

34. **Auto-clear replaces failed with same name**
    - Test Level: Integration
    - Risk: R6-010
    - Steps:
      1. Upload "report.pdf", fails processing
      2. Upload new "report.pdf"
    - Validation: Failed doc auto-cleared, new upload proceeds

35. **Auto-clear respects grace period**
    - Test Level: Integration
    - Risk: R6-010
    - Steps:
      1. Upload, fails
      2. Immediately upload same name
      3. Check if grace period respected
    - Validation: Within 24 hours, prompt user; after 24 hours, auto-clear

**P1 Scenarios (3):**

36. **Duplicate resolution - skip**
    - Test Level: API
    - Validation: New upload cancelled

37. **Duplicate resolution - replace**
    - Test Level: API
    - Validation: Old doc archived, new uploaded

38. **Duplicate resolution - keep both**
    - Test Level: API
    - Validation: New doc renamed with suffix

---

### Story 6.6: Replace Document Backend

**P0 Scenarios (4):**

39. **Replace preserves document UUID**
    - Test Level: API
    - Steps:
      1. Note document ID
      2. POST `/api/v1/documents/{id}/replace` with new file
      3. GET document
    - Validation: Same UUID, new content

40. **Replace archives old version**
    - Test Level: API
    - Risk: R6-002
    - Steps:
      1. Replace document
      2. Check old version status
    - Validation: Old version in archived state with "replaced" reason

41. **Replace re-processes new content**
    - Test Level: Integration
    - Steps:
      1. Replace document
      2. Wait for processing
      3. Search for new content
    - Validation: New content searchable, old content not

42. **Replace creates version link**
    - Test Level: API
    - Steps:
      1. Replace document
      2. GET document metadata
    - Validation: replaced_by or replaces fields populated

**P1 Scenarios (3):**

43. **Replace requires edit permission**
    - Test Level: API
    - Validation: 403 for read-only users

44. **Replace preserves tags**
    - Test Level: API
    - Validation: Tags copied to new version

45. **Replace audit logged**
    - Test Level: API
    - Validation: Audit event with old/new versions

---

### Story 6.7: Archive Management UI

**P0 Scenarios (2):**

46. **Archive page requires owner/admin**
    - Test Level: E2E
    - Risk: R6-003
    - Steps:
      1. Login as KB reader
      2. Navigate to archive management
    - Validation: Access denied or redirect

47. **Archive page loads archived documents**
    - Test Level: E2E
    - Steps:
      1. Login as KB owner
      2. Navigate to archive management
    - Validation: Archived documents listed

**P1 Scenarios (8):**

48. **Filter by status (archived/active/all)**
    - Test Level: E2E
    - Validation: Filter dropdown works

49. **Search archived documents**
    - Test Level: E2E
    - Validation: Name search works

50. **Bulk select documents**
    - Test Level: E2E
    - Validation: Checkboxes, select all

51. **Bulk restore selected**
    - Test Level: E2E
    - Risk: R6-004
    - Validation: Multiple docs restored

52. **Bulk purge selected**
    - Test Level: E2E
    - Risk: R6-004
    - Validation: Confirmation, multiple docs purged

53. **Single document restore**
    - Test Level: E2E
    - Validation: Restore button works

54. **Single document purge**
    - Test Level: E2E
    - Validation: Purge button with confirmation

55. **Archive stats display**
    - Test Level: E2E
    - Validation: Counts for archived/active/failed

---

### Story 6.8: Document List Archive/Clear Actions UI

**P1 Scenarios (5):**

56. **Archive button in document row**
    - Test Level: E2E
    - Steps:
      1. View document list
      2. Click archive on completed document
    - Validation: Confirmation dialog, document archived

57. **Clear button for failed documents**
    - Test Level: E2E
    - Validation: Only visible for failed status

58. **Archive button disabled for non-completed**
    - Test Level: E2E
    - Validation: Button disabled for processing/failed

59. **Confirmation dialog for archive**
    - Test Level: E2E
    - Validation: Modal appears, can cancel

60. **Success toast after archive**
    - Test Level: E2E
    - Validation: Toast notification

---

### Story 6.9: Duplicate Upload & Replace UI

**P1 Scenarios (6):**

61. **Duplicate warning modal on upload**
    - Test Level: E2E
    - Steps:
      1. Upload duplicate file
    - Validation: Modal shows existing doc info

62. **Skip option works**
    - Test Level: E2E
    - Validation: Upload cancelled, no changes

63. **Replace option works**
    - Test Level: E2E
    - Validation: Old archived, new uploaded

64. **Keep both option works**
    - Test Level: E2E
    - Validation: New uploaded with suffix

65. **Replace via document menu**
    - Test Level: E2E
    - Steps:
      1. Click "Replace" in document options menu
      2. Upload new file
    - Validation: Replace flow completes

66. **Replace confirmation shows preview**
    - Test Level: E2E
    - Risk: R6-009
    - Validation: Shows what will be replaced

---

## Validation Checklist

After completing all steps, verify:

- [x] Risk assessment complete with all categories
- [x] All risks scored (probability x impact)
- [x] High-priority risks (≥6) flagged with mitigation plans
- [x] Coverage matrix maps requirements to test levels
- [x] Priority levels assigned (P0-P3)
- [x] Execution order defined
- [x] Resource estimates provided
- [x] Quality gate criteria defined
- [x] Test scenarios detailed for P0 stories
- [x] Output file created and formatted correctly

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: __________ Date: __________
- [ ] Tech Lead: __________ Date: __________
- [ ] QA Lead: __________ Date: __________

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework (6 categories, scoring, gates)
- `probability-impact.md` - Risk scoring methodology (1-9 scale, thresholds)
- `test-levels-framework.md` - Test level selection (E2E, API, Component, Unit)
- `test-priorities-matrix.md` - P0-P3 prioritization (risk-based mapping)

### Related Documents

- **PRD**: [docs/prd.md](./prd.md)
- **Epic**: [docs/epics.md](./epics.md) - Epic 6 (Document Lifecycle Management)
- **Tech Spec**: [docs/sprint-artifacts/tech-spec-epic-6.md](sprint-artifacts/tech-spec-epic-6.md)
- **Architecture**: [docs/architecture.md](./architecture.md)
- **Page Objects**: `frontend/e2e/pages/archive.page.ts`, `frontend/e2e/pages/document.page.ts`
- **Factories**: `frontend/e2e/fixtures/document-actions.factory.ts`, `frontend/e2e/fixtures/duplicate-detection.factory.ts`

### New Test Infrastructure (Created 2025-12-07)

**Page Objects:**
- `ArchivePage` - Archive management operations, bulk actions, filtering
- `DocumentPage` - Document chunk viewer (also supports Epic 6 document actions)

**Factories:**
- `document-actions.factory.ts` - Archive/restore/purge state factories
- `duplicate-detection.factory.ts` - Duplicate scenarios, name collisions
- `chunk-viewer.factory.ts` - Chunk data for document viewer

---

**Generated by**: Murat (TEA - Master Test Architect)
**Workflow**: `.bmad/bmm/workflows/testarch/test-design`
**Version**: 6.1 (BMad v6)
**Date**: 2025-12-07
