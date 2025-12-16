# Sprint Change Proposal: KB Delete and Archive Feature

**Date:** 2025-12-10
**Requested By:** Tung Vu
**Change Trigger:** User Feedback
**Status:** APPROVED

---

## Executive Summary

This proposal introduces distinct **Delete** and **Archive** operations for Knowledge Bases:

- **Delete KB**: Only permitted for empty Knowledge Bases (0 documents). Performs hard delete of KB record and Qdrant collection.
- **Archive KB**: Cascades to all documents, marking them archived and filtering from search results. KB can be restored.

**Total Effort:** 11 story points (3 new stories)

---

## Change Analysis

### Impact Assessment

| Dimension | Impact Level | Notes |
|-----------|--------------|-------|
| PRD | Medium | New FRs required (FR11a-FR11d) |
| Architecture | Low | Add `archived_at` column, document cascade pattern |
| Epic 2 | High | Modify Story 2.1, add Stories 2.13-2.15 |
| Dependencies | None | Reuses Epic 6 patterns |
| Risk | Low | Well-understood patterns from Epic 6 |

### Alignment Check

- **PRD FR11**: Currently ambiguous - "archive or delete" needs separation
- **Epic 6 Patterns**: Archive/restore patterns proven in document lifecycle
- **Architecture**: Cascade operations align with transactional outbox pattern

---

## Proposed Changes

### 1. PRD Modifications

**Current FR11:**
> "Administrators can archive or delete Knowledge Bases."

**Proposed FR11 (Modified):**
> "Administrators can manage Knowledge Base lifecycle through distinct delete and archive operations."

**New Functional Requirements:**

| FR | Description |
|----|-------------|
| FR11a | **Delete KB** - Permanently remove empty Knowledge Bases (0 documents). Returns 400 if documents exist. Removes Qdrant collection. |
| FR11b | **Archive KB** - Set KB to archived status, cascade to all documents (set `archived_at`), exclude from listings and search. |
| FR11c | **Restore KB** - Restore archived KB and all its documents to active status. |
| FR11d | **Archive Cascade** - When archiving a KB, all documents inherit archive status; Qdrant payloads updated to `is_archived: true`. |

---

### 2. Epic 2 Story Modifications

#### Story 2.1: KB CRUD Backend (MODIFY)

**Current DELETE Acceptance Criteria:**
```
Given I have ADMIN permission on a KB
When I call DELETE /api/v1/knowledge-bases/{id}
Then the KB status is set to ARCHIVED
And it no longer appears in normal listings
And the Qdrant collection is deleted
```

**Proposed DELETE Acceptance Criteria:**
```
Given I have ADMIN permission on a KB
And the KB has 0 documents
When I call DELETE /api/v1/knowledge-bases/{id}
Then the KB is permanently deleted from database
And the Qdrant collection is deleted
And the action is logged to audit.events

Given I have ADMIN permission on a KB
And the KB has 1+ documents
When I call DELETE /api/v1/knowledge-bases/{id}
Then I receive 400 Bad Request
And error message states: "Cannot delete KB with documents. Archive or remove documents first."
```

---

### 3. New Stories

#### Story 2.13: KB Archive Backend

**Points:** 5

**User Story:**
As an **administrator**,
I want **to archive a Knowledge Base and all its documents**,
So that **content is preserved but hidden from normal operations**.

**Acceptance Criteria:**

```gherkin
Given I have ADMIN permission on a KB
When I call POST /api/v1/knowledge-bases/{id}/archive
Then the KB status is set to ARCHIVED
And KB.archived_at is set to current timestamp
And all documents in KB have archived_at set
And an outbox event is created for Qdrant payload updates
And the action is logged to audit.events

Given a KB is being archived
When the outbox worker processes the archive event
Then all Qdrant points for KB documents have payload updated to is_archived: true
And archived points are excluded from search queries

Given a KB is archived
When I call GET /api/v1/knowledge-bases
Then the archived KB does not appear in default listing
And it appears when include_archived=true query param is set

Given a KB is archived
When I try to upload documents to it
Then I receive 400 Bad Request
And error message states: "Cannot upload to archived KB"
```

**Technical Notes:**
- Reuse Epic 6 document archive pattern for cascade
- Batch Qdrant payload updates (100 points per batch)
- Use transactional outbox for consistency
- Add `archived_at` column to `knowledge_bases` table

**Prerequisites:** Story 2.1, Story 6.1 (pattern reference)

---

#### Story 2.14: KB Restore Backend

**Points:** 3

**User Story:**
As an **administrator**,
I want **to restore an archived Knowledge Base**,
So that **it becomes active and searchable again**.

**Acceptance Criteria:**

```gherkin
Given I have ADMIN permission on an archived KB
When I call POST /api/v1/knowledge-bases/{id}/restore
Then the KB status is set to ACTIVE
And KB.archived_at is set to null
And all documents in KB have archived_at set to null
And an outbox event is created for Qdrant payload updates
And the action is logged to audit.events

Given a KB is being restored
When the outbox worker processes the restore event
Then all Qdrant points for KB documents have payload updated to is_archived: false
And restored points are included in search queries

Given a KB is restored
When I call GET /api/v1/knowledge-bases
Then the KB appears in default listing
And document upload is permitted again
```

**Technical Notes:**
- Mirror archive logic with inverse operation
- Batch Qdrant payload updates
- Use transactional outbox for consistency

**Prerequisites:** Story 2.13

---

#### Story 2.15: KB Delete/Archive UI

**Points:** 3

**User Story:**
As an **administrator**,
I want **UI controls for KB delete, archive, and restore**,
So that **I can manage KB lifecycle without API calls**.

**Acceptance Criteria:**

```gherkin
Given I have ADMIN permission on an active KB
When I view KB settings/actions menu
Then I see "Archive KB" option
And I see "Delete KB" option (enabled only if document_count = 0)

Given KB has documents
When I hover over disabled "Delete KB" button
Then tooltip shows: "Remove all documents before deleting"

Given I click "Archive KB"
When confirmation dialog appears
Then it warns: "This will archive X documents. Archived KBs are hidden from search."
And I can confirm or cancel

Given I click "Delete KB" on empty KB
When confirmation dialog appears
Then it warns: "This will permanently delete the KB. This cannot be undone."
And I must type KB name to confirm

Given I view archived KBs list
When I click "Restore" on an archived KB
Then confirmation dialog appears
And KB is restored on confirmation
```

**Technical Notes:**
- Add "Archived" filter toggle to KB list
- Destructive actions require explicit confirmation
- Show document count in archive warning

**Prerequisites:** Story 2.13, Story 2.14

---

### 4. Architecture Updates

#### Database Schema

Add column to `knowledge_bases` table:

```sql
ALTER TABLE knowledge_bases
ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
```

**Index:** `CREATE INDEX idx_kb_archived ON knowledge_bases(archived_at) WHERE archived_at IS NOT NULL;`

#### KB Archive Cascade Pattern

Document in architecture (similar to Epic 6 patterns):

```
KB Archive Flow:
1. Set KB.archived_at = now()
2. UPDATE documents SET archived_at = now() WHERE kb_id = {id}
3. Create outbox event: KB_ARCHIVE with kb_id
4. Outbox worker: Batch update Qdrant payloads (is_archived: true)
5. Log to audit.events

KB Restore Flow:
1. Set KB.archived_at = null
2. UPDATE documents SET archived_at = null WHERE kb_id = {id}
3. Create outbox event: KB_RESTORE with kb_id
4. Outbox worker: Batch update Qdrant payloads (is_archived: false)
5. Log to audit.events

KB Delete Flow (empty only):
1. Verify document_count = 0
2. DELETE FROM knowledge_bases WHERE id = {id}
3. Drop Qdrant collection kb_{id}
4. Log to audit.events
```

---

## Implementation Plan

### Recommended Sequence

1. **Migration**: Add `archived_at` to `knowledge_bases` table
2. **Story 2.1 Modification**: Update delete to check document count
3. **Story 2.13**: KB Archive Backend
4. **Story 2.14**: KB Restore Backend
5. **Story 2.15**: KB Delete/Archive UI

### Effort Summary

| Story | Points | Dependencies |
|-------|--------|--------------|
| 2.1 (modify) | 0 | None |
| 2.13 | 5 | Migration |
| 2.14 | 3 | 2.13 |
| 2.15 | 3 | 2.13, 2.14 |
| **Total** | **11** | |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cascade archive timeout | Low | Medium | Batch operations, outbox pattern |
| Orphaned Qdrant points | Low | Low | Reconciliation job detects |
| UI confusion | Low | Low | Clear warnings, confirmations |

---

## Approval Section

**Scope Classification:** MINOR (within single epic, 3 new stories)

**Approvals Required:**
- [ ] Product Owner: PRD changes (FR11a-FR11d)
- [ ] Tech Lead: Architecture changes
- [ ] Scrum Master: Sprint capacity

**Decision:**
- [x] APPROVED - Proceed with implementation (Stories added to Epic 7 as 7.24, 7.25, 7.26)
- [ ] APPROVED WITH MODIFICATIONS - (specify changes)
- [ ] DEFERRED - (specify reason)
- [ ] REJECTED - (specify reason)

---

## Handoff

Upon approval, this proposal routes to:

1. **Dev Agent**: Implement Story 2.1 modification and new stories 2.13-2.15
2. **Architect Agent**: Review cascade pattern documentation
3. **Sprint Status**: Add stories to backlog with priorities

---

*Generated by BMAD Correct-Course Workflow*
*SM Agent: Scrum Master*
*Date: 2025-12-10*
