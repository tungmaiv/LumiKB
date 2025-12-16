# Story 8-7: KB-Domain Linking

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-7
**Priority:** HIGH
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Enable linking domains to Knowledge Bases during KB creation or editing. This establishes which entity types and relationships will be extracted from documents in each KB.

---

## Acceptance Criteria

### AC1: Domain Selection in KB Creation
**Given** a user creates a new Knowledge Base
**When** they reach the domain selection step
**Then** they can:
  - Skip domain selection (no GraphRAG)
  - Select an existing domain
  - Create a new domain (redirect to domain wizard)
  - Use LLM recommendations based on KB description

### AC2: Domain Selection in KB Edit
**Given** a user edits an existing Knowledge Base
**When** they access domain settings
**Then** they can:
  - View currently linked domain (if any)
  - Change to a different domain
  - Remove domain (disable GraphRAG)
**And** a warning shows if documents will need re-extraction

### AC3: Multiple Domain Support
**Given** a KB may benefit from multiple schemas
**When** linking domains
**Then** multiple domains can be linked to a single KB
**And** entity extraction uses all linked domain schemas
**And** entities from different domains are clearly labeled

### AC4: KB Creation API Update
**Given** the KB creation API
**When** domain_id is included in the request
**Then** the kb_domains junction is created
**And** the domain is validated to exist
**And** the user must have access to the domain

### AC5: Domain Linking API
**Given** an existing KB
**When** domain linking is managed
**Then** the following endpoints work:
  - `POST /api/v1/knowledge-bases/{kb_id}/domains/{domain_id}` - Link domain
  - `DELETE /api/v1/knowledge-bases/{kb_id}/domains/{domain_id}` - Unlink domain
  - `GET /api/v1/knowledge-bases/{kb_id}/domains` - List linked domains

### AC6: Re-extraction Trigger
**Given** a domain is linked to a KB with existing documents
**When** the link is created
**Then** the system offers to:
  - Skip re-extraction (new documents only)
  - Queue all documents for entity re-extraction
**And** the user's choice is recorded

---

## Technical Notes

### API Endpoints

```python
# backend/app/api/v1/knowledge_bases.py

@router.post("/{kb_id}/domains/{domain_id}")
async def link_domain(
    kb_id: UUID,
    domain_id: UUID,
    trigger_extraction: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Link a domain to a Knowledge Base."""
    kb_service = KBService(db)

    # Verify KB access
    kb = await kb_service.get_with_permission_check(kb_id, current_user, "write")

    # Verify domain access
    domain_service = DomainService(db)
    domain = await domain_service.get_accessible(domain_id, current_user.id)

    # Create link
    await kb_service.link_domain(kb_id, domain_id, current_user.id)

    # Optionally trigger extraction
    if trigger_extraction:
        await queue_entity_extraction_for_kb(kb_id, domain_id)

    return {"status": "linked", "extraction_queued": trigger_extraction}

@router.delete("/{kb_id}/domains/{domain_id}")
async def unlink_domain(
    kb_id: UUID,
    domain_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlink a domain from a Knowledge Base."""
    kb_service = KBService(db)
    kb = await kb_service.get_with_permission_check(kb_id, current_user, "write")

    await kb_service.unlink_domain(kb_id, domain_id)

    # Note: Extracted entities remain in Neo4j until explicit cleanup
    return {"status": "unlinked"}
```

### KB Creation Schema Update

```python
# backend/app/schemas/knowledge_base.py
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    permission_level: PermissionLevel = PermissionLevel.PRIVATE
    domain_ids: Optional[List[UUID]] = None  # NEW: Optional domain linking
```

### Frontend KB Creation Flow

```typescript
// Updated KB creation wizard steps
const KB_CREATION_STEPS = [
  { id: 'basics', title: 'Basic Info' },      // Name, description
  { id: 'domain', title: 'Knowledge Graph' },  // NEW: Domain selection
  { id: 'permissions', title: 'Permissions' }, // Access control
  { id: 'review', title: 'Review' }            // Confirmation
];

// Domain selection component
function DomainSelectionStep({ kbDescription, onDomainSelect }) {
  const { data: recommendations } = useDomainRecommendations({
    description: kbDescription
  });

  return (
    <div>
      <h3>Enable Knowledge Graph (Optional)</h3>
      <p>Knowledge graphs improve search quality by understanding entity relationships.</p>

      <RadioGroup defaultValue="none" onValueChange={handleChange}>
        <RadioGroupItem value="none">Skip (basic search only)</RadioGroupItem>
        <RadioGroupItem value="existing">Use existing domain</RadioGroupItem>
        <RadioGroupItem value="recommended">Use AI recommendation</RadioGroupItem>
        <RadioGroupItem value="new">Create new domain</RadioGroupItem>
      </RadioGroup>

      {/* Conditional content based on selection */}
    </div>
  );
}
```

---

## Definition of Done

- [ ] Domain selection UI in KB creation wizard
- [ ] Domain management in KB edit page
- [ ] Multiple domain linking support
- [ ] KB creation API updated with domain_ids
- [ ] Domain link/unlink endpoints implemented
- [ ] Re-extraction trigger option
- [ ] Access control validation
- [ ] Unit tests for linking service
- [ ] Integration tests for API endpoints
- [ ] Frontend tests for domain selection
- [ ] Documentation updated

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-5 (Domain Management API), Story 8-6 (Domain Management UI)
**Next Story:** Story 8-8 (Per-KB Entity Extraction Service)
