# Story 8-9: Document Processing Graph Integration

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-9
**Priority:** HIGH
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Integrate entity extraction into the existing document processing pipeline. When a document is processed and chunked, entity extraction runs as an additional step if the KB has a linked domain.

---

## Acceptance Criteria

### AC1: Pipeline Extension
**Given** the document processing pipeline (Epic 2)
**When** a document finishes chunking and embedding
**Then** if the KB has linked domains:
  - Entity extraction is triggered
  - Each chunk is processed for entities
  - Progress is tracked in document status
**And** if no domains are linked, extraction is skipped

### AC2: Celery Task for Extraction
**Given** extraction is triggered
**When** the Celery worker processes extraction
**Then** it:
  - Loads the KB's linked domain schemas
  - Processes chunks in batches
  - Stores entities and relationships in Neo4j
  - Updates document status on completion
  - Handles failures gracefully with retry

### AC3: Processing Status Extension
**Given** the document has extraction in progress
**When** status is queried
**Then** the response includes:
  - `extraction_status`: pending | in_progress | completed | failed | skipped
  - `entities_extracted`: count of entities found
  - `relationships_extracted`: count of relationships found
  - `extraction_errors`: list of any errors

### AC4: Batch Processing for Efficiency
**Given** a document has many chunks
**When** extraction runs
**Then** chunks are processed in configurable batches
**And** batch size defaults to 10 chunks
**And** parallelization is supported (concurrent LLM calls)
**And** rate limiting prevents LLM overload

### AC5: Re-extraction Trigger
**Given** a domain is linked to a KB with existing documents
**When** re-extraction is requested
**Then** a bulk job queues all documents
**And** existing entities for those documents are cleared first
**And** progress is trackable via admin UI

### AC6: Error Handling and Recovery
**Given** extraction fails for a chunk
**When** failure is detected
**Then** the chunk is marked as failed
**And** other chunks continue processing
**And** failed chunks can be retried individually
**And** partial results are preserved

---

## Technical Notes

### Celery Task Definition

```python
# backend/app/workers/extraction_tasks.py
from celery import shared_task

@shared_task(
    bind=True,
    autoretry_for=(ExternalServiceError,),
    retry_backoff=True,
    max_retries=3
)
def extract_entities_for_document(
    self,
    document_id: str,
    kb_id: str,
    domain_ids: List[str]
):
    """Extract entities from all chunks of a document."""
    from app.services.entity_extraction_service import EntityExtractionService
    from app.services.graph_storage_service import GraphStorageService

    try:
        extraction_service = EntityExtractionService()
        storage_service = GraphStorageService()

        # Load domain schemas
        domains = load_domains(domain_ids)

        # Get document chunks from Qdrant
        chunks = get_document_chunks(document_id)

        # Update status to in_progress
        update_document_extraction_status(document_id, "in_progress")

        total_entities = 0
        total_relationships = 0
        errors = []

        # Process in batches
        for batch in batched(chunks, batch_size=10):
            results = []

            # Parallel extraction within batch
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(
                        extraction_service.extract_from_chunk,
                        chunk, domains
                    )
                    for chunk in batch
                ]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        errors.append(str(e))

            # Store results
            for result in results:
                storage_service.store_entities(
                    kb_id, document_id, result.chunk_id, result.entities
                )
                storage_service.store_relationships(
                    kb_id, document_id, result.chunk_id, result.relationships
                )

                total_entities += len(result.entities)
                total_relationships += len(result.relationships)

        # Update final status
        update_document_extraction_status(
            document_id,
            "completed" if not errors else "completed_with_errors",
            entities_extracted=total_entities,
            relationships_extracted=total_relationships,
            errors=errors
        )

    except Exception as e:
        update_document_extraction_status(document_id, "failed", errors=[str(e)])
        raise
```

### Pipeline Integration Point

```python
# backend/app/workers/document_tasks.py
@shared_task
def process_document(document_id: str, kb_id: str):
    """Main document processing task."""
    # Existing steps...
    parse_document(document_id)
    chunk_document(document_id)
    embed_chunks(document_id)

    # NEW: Check for linked domains and trigger extraction
    domains = get_kb_linked_domains(kb_id)
    if domains:
        extract_entities_for_document.delay(
            document_id=document_id,
            kb_id=kb_id,
            domain_ids=[str(d.id) for d in domains]
        )
    else:
        # Mark extraction as skipped
        update_document_extraction_status(document_id, "skipped")

    # Update document status
    update_document_status(document_id, "ready")
```

### Document Model Extension

```python
# Add to Document model
extraction_status: Mapped[Optional[str]] = mapped_column(
    String(50),
    default=None  # None = not applicable, "pending", "in_progress", "completed", "failed", "skipped"
)
entities_extracted: Mapped[int] = mapped_column(Integer, default=0)
relationships_extracted: Mapped[int] = mapped_column(Integer, default=0)
extraction_errors: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
extraction_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
extraction_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
```

### Bulk Re-extraction Endpoint

```python
@router.post("/{kb_id}/reextract")
async def trigger_bulk_reextraction(
    kb_id: UUID,
    domain_ids: Optional[List[UUID]] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger entity re-extraction for all documents in KB."""
    kb = await get_kb_with_permission(kb_id, current_user, "admin")

    # Get domains to use
    if domain_ids:
        domains = domain_ids
    else:
        domains = [d.id for d in kb.domains]

    if not domains:
        raise HTTPException(400, "No domains linked to KB")

    # Queue all documents
    documents = await get_kb_documents(kb_id, status="ready")
    job_id = str(uuid4())

    for doc in documents:
        # Clear existing entities for this document
        await clear_document_entities(doc.id)

        # Queue extraction
        extract_entities_for_document.delay(
            document_id=str(doc.id),
            kb_id=str(kb_id),
            domain_ids=[str(d) for d in domains],
            job_id=job_id
        )

    return {
        "job_id": job_id,
        "documents_queued": len(documents),
        "domains": domains
    }
```

---

## Definition of Done

- [ ] Celery task for entity extraction
- [ ] Pipeline integration after embedding
- [ ] Domain check before extraction
- [ ] Batch processing with configurable size
- [ ] Parallel LLM calls within batch
- [ ] Document model extended with extraction fields
- [ ] Status tracking (pending, in_progress, completed, failed, skipped)
- [ ] Error capture and partial completion
- [ ] Re-extraction endpoint for admins
- [ ] Existing entity cleanup before re-extraction
- [ ] Unit tests for extraction task
- [ ] Integration test for full pipeline
- [ ] Performance test (documents/minute)

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-8 (Entity Extraction Service), Epic 2 (Document Processing)
**Next Story:** Story 8-10 (Graph Query Service)
