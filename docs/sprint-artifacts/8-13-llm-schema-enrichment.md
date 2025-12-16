# Story 8-13: LLM Schema Enrichment Suggestions

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-13
**Priority:** MEDIUM
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Enable LLM-powered suggestions to enrich domain schemas over time. As documents are processed and entities extracted, the system identifies potential new entity types or relationships not in the current schema and suggests them to administrators.

---

## Acceptance Criteria

### AC1: Unrecognized Entity Detection
**Given** entity extraction runs on documents
**When** the LLM identifies potential entities not matching the schema
**Then** these are captured as "unrecognized entities"
**And** they are stored with the extracted name and context
**And** frequency is tracked across documents

### AC2: Enrichment Suggestion Generation
**Given** unrecognized entities accumulate
**When** an admin views schema enrichment suggestions
**Then** they see:
  - Suggested new entity types (grouped by pattern)
  - Frequency count (how often seen)
  - Sample contexts from documents
  - Confidence score for the suggestion

### AC3: Relationship Gap Detection
**Given** entities are extracted and connected
**When** relationship patterns emerge not in the schema
**Then** the system suggests:
  - New relationship types between existing entity types
  - Relationships involving suggested new entity types
  - Evidence from document contexts

### AC4: Admin Review Interface
**Given** suggestions are generated
**When** an admin reviews them
**Then** they can:
  - Accept: Add to domain schema
  - Reject: Mark as ignored (won't suggest again)
  - Defer: Keep for later review
  - Customize: Accept with modifications

### AC5: Accepted Suggestion Integration
**Given** an admin accepts a suggestion
**When** the entity type or relationship is added
**Then** it's added to the domain schema
**And** optionally triggers re-extraction for affected documents
**And** the suggestion is marked as resolved

### AC6: Suggestion Digest Notification
**Given** significant new suggestions accumulate
**When** threshold is reached (e.g., 10+ high-confidence suggestions)
**Then** admin receives a notification (in-app)
**And** notification links to enrichment review page

---

## Technical Notes

### Unrecognized Entity Storage

```python
# Add to extraction process
class UnrecognizedEntity(Base):
    __tablename__ = "unrecognized_entities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kb_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_bases.id"))
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"))

    suggested_type: Mapped[str] = mapped_column(String(100))
    extracted_name: Mapped[str] = mapped_column(String(255))
    context_snippet: Mapped[str] = mapped_column(Text)  # Surrounding text

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"))
    chunk_id: Mapped[str] = mapped_column(String(100))

    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, rejected

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### Suggestion Aggregation Service

```python
# backend/app/services/schema_enrichment_service.py
class SchemaEnrichmentService:
    async def get_entity_type_suggestions(
        self,
        domain_id: UUID,
        min_frequency: int = 3,
        min_confidence: float = 0.7
    ) -> List[EntityTypeSuggestion]:
        """Aggregate unrecognized entities into suggestions."""
        query = """
        SELECT
            suggested_type,
            COUNT(*) as frequency,
            AVG(confidence) as avg_confidence,
            ARRAY_AGG(DISTINCT extracted_name) as sample_names,
            ARRAY_AGG(DISTINCT context_snippet) as sample_contexts
        FROM unrecognized_entities
        WHERE domain_id = :domain_id
          AND status = 'pending'
        GROUP BY suggested_type
        HAVING COUNT(*) >= :min_frequency
           AND AVG(confidence) >= :min_confidence
        ORDER BY COUNT(*) DESC
        """

        results = await self.db.execute(query, {
            'domain_id': domain_id,
            'min_frequency': min_frequency,
            'min_confidence': min_confidence
        })

        return [
            EntityTypeSuggestion(
                suggested_type=row.suggested_type,
                frequency=row.frequency,
                avg_confidence=row.avg_confidence,
                sample_names=row.sample_names[:5],  # Limit samples
                sample_contexts=row.sample_contexts[:3]
            )
            for row in results
        ]

    async def get_relationship_suggestions(
        self,
        domain_id: UUID
    ) -> List[RelationshipSuggestion]:
        """Analyze extracted entities for potential new relationships."""
        # Query Neo4j for co-occurrence patterns not in schema
        cypher = """
        MATCH (a)-[r]->(b)
        WHERE a.kb_id IN $kb_ids AND b.kb_id IN $kb_ids
          AND NOT type(r) IN $known_relationship_types
        RETURN type(r) as rel_type,
               labels(a)[0] as from_type,
               labels(b)[0] as to_type,
               COUNT(*) as frequency
        ORDER BY frequency DESC
        LIMIT 20
        """

        # Get KBs using this domain and known relationship types
        kb_ids = await self._get_domain_kb_ids(domain_id)
        known_types = await self._get_domain_relationship_types(domain_id)

        results = await self.neo4j.run(cypher, {
            'kb_ids': kb_ids,
            'known_relationship_types': known_types
        })

        return [
            RelationshipSuggestion(
                name=row['rel_type'],
                from_entity_type=row['from_type'],
                to_entity_type=row['to_type'],
                frequency=row['frequency']
            )
            for row in results
        ]

    async def accept_suggestion(
        self,
        domain_id: UUID,
        suggestion_type: str,
        suggested_value: str,
        customization: Optional[Dict] = None,
        trigger_reextraction: bool = False
    ) -> EntityType | RelationshipType:
        """Accept a suggestion and add to domain schema."""
        if suggestion_type == "entity_type":
            new_entity_type = await self._create_entity_type(
                domain_id, suggested_value, customization
            )

            # Mark related unrecognized entities as accepted
            await self._mark_suggestions_resolved(
                domain_id, "entity_type", suggested_value, "accepted"
            )

            if trigger_reextraction:
                await self._queue_reextraction(domain_id)

            return new_entity_type

        elif suggestion_type == "relationship_type":
            # Similar logic for relationships
            pass

    async def reject_suggestion(
        self,
        domain_id: UUID,
        suggestion_type: str,
        suggested_value: str
    ):
        """Reject a suggestion - won't be suggested again."""
        await self._mark_suggestions_resolved(
            domain_id, suggestion_type, suggested_value, "rejected"
        )
```

### API Endpoints

```python
# backend/app/api/v1/domains.py

@router.get("/{domain_id}/enrichment/suggestions")
async def get_enrichment_suggestions(
    domain_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get schema enrichment suggestions for a domain."""
    service = SchemaEnrichmentService(db, get_neo4j())

    entity_suggestions = await service.get_entity_type_suggestions(domain_id)
    relationship_suggestions = await service.get_relationship_suggestions(domain_id)

    return {
        "entity_types": entity_suggestions,
        "relationship_types": relationship_suggestions,
        "total_suggestions": len(entity_suggestions) + len(relationship_suggestions)
    }

@router.post("/{domain_id}/enrichment/accept")
async def accept_suggestion(
    domain_id: UUID,
    request: AcceptSuggestionRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept an enrichment suggestion."""
    service = SchemaEnrichmentService(db, get_neo4j())

    result = await service.accept_suggestion(
        domain_id=domain_id,
        suggestion_type=request.suggestion_type,
        suggested_value=request.suggested_value,
        customization=request.customization,
        trigger_reextraction=request.trigger_reextraction
    )

    return {"status": "accepted", "created": result}

@router.post("/{domain_id}/enrichment/reject")
async def reject_suggestion(
    domain_id: UUID,
    request: RejectSuggestionRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject an enrichment suggestion."""
    service = SchemaEnrichmentService(db, get_neo4j())

    await service.reject_suggestion(
        domain_id=domain_id,
        suggestion_type=request.suggestion_type,
        suggested_value=request.suggested_value
    )

    return {"status": "rejected"}
```

### Frontend Enrichment Panel

```typescript
// src/components/domains/EnrichmentSuggestionsPanel.tsx
function EnrichmentSuggestionsPanel({ domainId }: { domainId: string }) {
  const { data: suggestions } = useEnrichmentSuggestions(domainId);
  const acceptMutation = useAcceptSuggestion();
  const rejectMutation = useRejectSuggestion();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Schema Enrichment Suggestions</CardTitle>
        <CardDescription>
          Based on extracted entities, consider adding these to your schema
        </CardDescription>
      </CardHeader>
      <CardContent>
        {suggestions?.entity_types.map(suggestion => (
          <SuggestionCard
            key={suggestion.suggested_type}
            type="entity_type"
            suggestion={suggestion}
            onAccept={(customization) => acceptMutation.mutate({
              domainId,
              suggestionType: 'entity_type',
              suggestedValue: suggestion.suggested_type,
              customization
            })}
            onReject={() => rejectMutation.mutate({
              domainId,
              suggestionType: 'entity_type',
              suggestedValue: suggestion.suggested_type
            })}
          />
        ))}
      </CardContent>
    </Card>
  );
}
```

---

## Definition of Done

- [ ] UnrecognizedEntity model and migration
- [ ] Capture unrecognized entities during extraction
- [ ] Aggregation logic for entity type suggestions
- [ ] Relationship pattern detection
- [ ] Accept/Reject/Defer workflow
- [ ] Optional re-extraction trigger
- [ ] Admin enrichment review UI
- [ ] Suggestion count notification
- [ ] Unit tests for aggregation logic
- [ ] Integration tests for accept workflow
- [ ] Documentation for enrichment process

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-8 (Entity Extraction), Story 8-5 (Domain Management API)
**Next Story:** Story 8-14 (Schema Evolution & Re-extraction)
