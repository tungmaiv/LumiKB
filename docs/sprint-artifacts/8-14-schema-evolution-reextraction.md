# Story 8-14: Schema Evolution & Re-extraction

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-14
**Priority:** MEDIUM
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Implement schema versioning and controlled re-extraction when domain schemas change. When entity types or relationships are added/modified, administrators can selectively re-extract entities from documents to apply the new schema.

---

## Acceptance Criteria

### AC1: Schema Version Tracking
**Given** a domain is modified
**When** entity types or relationships change
**Then** the schema version is incremented
**And** the change is logged with:
  - Previous version
  - New version
  - Change type (add/modify/remove)
  - Changed elements
  - User who made the change
  - Timestamp

### AC2: Document Schema Version Tracking
**Given** entities are extracted from a document
**When** extraction completes
**Then** the document records:
  - Domain ID used
  - Schema version at extraction time
  - Extraction timestamp

### AC3: Schema Drift Detection
**Given** a KB has documents with extracted entities
**When** the domain schema changes
**Then** the system identifies:
  - Documents extracted with outdated schema
  - Count of affected documents
  - Which entity types/relationships changed

### AC4: Selective Re-extraction UI
**Given** schema drift is detected
**When** an admin views affected documents
**Then** they can:
  - View which documents need re-extraction
  - Select all or specific documents
  - Trigger re-extraction for selected documents
  - Choose to keep or clear existing entities

### AC5: Re-extraction Job Management
**Given** re-extraction is triggered
**When** the job runs
**Then**:
  - Progress is trackable (X of Y documents)
  - Individual document status is visible
  - Job can be cancelled
  - Failures don't stop entire job
  - Completion notification is sent

### AC6: Entity Cleanup Options
**Given** re-extraction is about to run
**When** the admin configures the job
**Then** they choose:
  - **Append**: Keep existing entities, add new ones
  - **Replace**: Clear existing, extract fresh
  - **Merge**: Keep existing, update matches, add new

---

## Technical Notes

### Schema Version Model

```python
# Add version tracking to Domain model
class Domain(Base):
    # ... existing fields ...
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    last_schema_change: Mapped[Optional[datetime]] = mapped_column(DateTime)

# Schema change log
class DomainSchemaChange(Base):
    __tablename__ = "domain_schema_changes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"))

    previous_version: Mapped[int] = mapped_column(Integer)
    new_version: Mapped[int] = mapped_column(Integer)

    change_type: Mapped[str] = mapped_column(String(20))  # add, modify, remove
    element_type: Mapped[str] = mapped_column(String(20))  # entity_type, relationship_type
    element_id: Mapped[Optional[UUID]] = mapped_column(UUID)
    element_name: Mapped[str] = mapped_column(String(100))

    change_details: Mapped[Dict] = mapped_column(JSONB)  # Before/after values
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### Document Extraction Tracking

```python
# Extend Document model
class Document(Base):
    # ... existing fields ...

    # Schema tracking for re-extraction
    extraction_domain_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("domains.id"))
    extraction_schema_version: Mapped[Optional[int]] = mapped_column(Integer)
    extraction_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
```

### Schema Drift Detection Service

```python
# backend/app/services/schema_drift_service.py
class SchemaDriftService:
    async def get_outdated_documents(
        self,
        kb_id: UUID,
        domain_id: UUID
    ) -> List[OutdatedDocument]:
        """Find documents extracted with an older schema version."""
        current_version = await self._get_current_schema_version(domain_id)

        query = """
        SELECT d.id, d.name, d.extraction_schema_version, d.extraction_completed_at
        FROM documents d
        WHERE d.kb_id = :kb_id
          AND d.extraction_domain_id = :domain_id
          AND (d.extraction_schema_version IS NULL
               OR d.extraction_schema_version < :current_version)
          AND d.status = 'ready'
        ORDER BY d.extraction_completed_at ASC
        """

        results = await self.db.execute(query, {
            'kb_id': kb_id,
            'domain_id': domain_id,
            'current_version': current_version
        })

        return [
            OutdatedDocument(
                document_id=row.id,
                document_name=row.name,
                extracted_version=row.extraction_schema_version,
                current_version=current_version,
                extracted_at=row.extraction_completed_at
            )
            for row in results
        ]

    async def get_schema_changes_since(
        self,
        domain_id: UUID,
        since_version: int
    ) -> List[SchemaChange]:
        """Get all schema changes since a specific version."""
        query = """
        SELECT * FROM domain_schema_changes
        WHERE domain_id = :domain_id
          AND new_version > :since_version
        ORDER BY new_version ASC
        """

        results = await self.db.execute(query, {
            'domain_id': domain_id,
            'since_version': since_version
        })

        return [SchemaChange(**row) for row in results]

    async def get_drift_summary(
        self,
        kb_id: UUID
    ) -> DriftSummary:
        """Get summary of schema drift for all domains linked to KB."""
        domains = await self._get_kb_domains(kb_id)
        summaries = []

        for domain in domains:
            outdated = await self.get_outdated_documents(kb_id, domain.id)
            changes = await self.get_schema_changes_since(
                domain.id,
                min(d.extracted_version for d in outdated) if outdated else domain.schema_version
            )

            summaries.append(DomainDriftSummary(
                domain_id=domain.id,
                domain_name=domain.name,
                current_version=domain.schema_version,
                outdated_document_count=len(outdated),
                changes_since_oldest=len(changes)
            ))

        return DriftSummary(domains=summaries)
```

### Re-extraction Job Service

```python
# backend/app/services/reextraction_job_service.py
class ReextractionJobService:
    async def create_job(
        self,
        kb_id: UUID,
        domain_id: UUID,
        document_ids: List[UUID],
        cleanup_mode: str,  # append, replace, merge
        created_by: UUID
    ) -> ReextractionJob:
        """Create a re-extraction job."""
        job = ReextractionJob(
            id=uuid4(),
            kb_id=kb_id,
            domain_id=domain_id,
            document_count=len(document_ids),
            cleanup_mode=cleanup_mode,
            status="pending",
            created_by=created_by
        )

        self.db.add(job)
        await self.db.commit()

        # Queue individual document tasks
        for doc_id in document_ids:
            reextract_document.delay(
                job_id=str(job.id),
                document_id=str(doc_id),
                domain_id=str(domain_id),
                cleanup_mode=cleanup_mode
            )

        return job

    async def get_job_status(self, job_id: UUID) -> JobStatus:
        """Get current status of a re-extraction job."""
        job = await self._get_job(job_id)

        # Count completed/failed/pending documents
        stats = await self._get_job_document_stats(job_id)

        return JobStatus(
            job_id=job.id,
            status=job.status,
            total_documents=job.document_count,
            completed=stats['completed'],
            failed=stats['failed'],
            pending=stats['pending'],
            started_at=job.started_at,
            completed_at=job.completed_at,
            errors=stats['errors']
        )

    async def cancel_job(self, job_id: UUID):
        """Cancel a running re-extraction job."""
        job = await self._get_job(job_id)

        if job.status not in ('pending', 'running'):
            raise ValueError("Job cannot be cancelled")

        # Mark job as cancelled
        job.status = "cancelled"
        job.cancelled_at = datetime.utcnow()

        # Revoke pending Celery tasks
        await self._revoke_pending_tasks(job_id)

        await self.db.commit()
```

### Celery Task for Re-extraction

```python
# backend/app/workers/extraction_tasks.py
@shared_task(bind=True)
def reextract_document(
    self,
    job_id: str,
    document_id: str,
    domain_id: str,
    cleanup_mode: str
):
    """Re-extract entities for a single document."""
    try:
        # Check if job is cancelled
        job = get_job(job_id)
        if job.status == "cancelled":
            return {"status": "cancelled"}

        # Cleanup existing entities based on mode
        if cleanup_mode == "replace":
            clear_document_entities(document_id)
        elif cleanup_mode == "merge":
            # Mark existing for potential update
            mark_entities_for_merge(document_id)

        # Run extraction
        result = extract_entities_for_document(document_id, domain_id)

        # If merge mode, reconcile entities
        if cleanup_mode == "merge":
            reconcile_merged_entities(document_id)

        # Update document schema version
        update_document_schema_version(document_id, domain_id)

        return {"status": "completed", "entities": result.entity_count}

    except Exception as e:
        log_reextraction_error(job_id, document_id, str(e))
        raise
```

### API Endpoints

```python
@router.get("/knowledge-bases/{kb_id}/schema-drift")
async def get_schema_drift(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get schema drift summary for a KB."""
    await verify_kb_access(kb_id, current_user, "read", db)

    service = SchemaDriftService(db)
    return await service.get_drift_summary(kb_id)

@router.post("/knowledge-bases/{kb_id}/reextract")
async def create_reextraction_job(
    kb_id: UUID,
    request: ReextractionRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a re-extraction job."""
    await verify_kb_access(kb_id, current_user, "admin", db)

    service = ReextractionJobService(db)
    job = await service.create_job(
        kb_id=kb_id,
        domain_id=request.domain_id,
        document_ids=request.document_ids,
        cleanup_mode=request.cleanup_mode,
        created_by=current_user.id
    )

    return {"job_id": job.id, "status": "created", "documents_queued": job.document_count}

@router.get("/reextraction-jobs/{job_id}")
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get re-extraction job status."""
    service = ReextractionJobService(db)
    return await service.get_job_status(job_id)

@router.post("/reextraction-jobs/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a re-extraction job."""
    service = ReextractionJobService(db)
    await service.cancel_job(job_id)
    return {"status": "cancelled"}
```

---

## Definition of Done

- [ ] Schema version tracking on domains
- [ ] Schema change logging
- [ ] Document extraction version tracking
- [ ] Schema drift detection service
- [ ] Re-extraction job model and service
- [ ] Cleanup modes (append/replace/merge)
- [ ] Celery task for document re-extraction
- [ ] Job status and progress tracking
- [ ] Job cancellation
- [ ] Admin UI for drift review
- [ ] Admin UI for job creation and monitoring
- [ ] Unit tests for drift detection
- [ ] Integration tests for re-extraction job
- [ ] Documentation for schema evolution

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-9 (Document Processing Integration), Story 8-5 (Domain Management API)
**Next Story:** Story 8-15 (Batch Re-processing Worker)
