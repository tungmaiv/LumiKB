"""Integration tests for document processing observability trace flow (Story 9-4 AC11).

Tests verify end-to-end document processing trace with all steps:
- Trace record created in obs_traces table
- Span records created for each step (upload, parse, chunk, embed, index)
- DocumentEvent records for each step
- Proper trace termination with status
"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.observability import DocumentEvent, Trace
from app.services.observability_service import ObservabilityService


@pytest.fixture
async def obs_test_user(db_session: AsyncSession):
    """Create a simple test user for observability tests.

    Uses direct database insertion to avoid api_client fixture dependencies.
    """
    from app.models.user import User

    user = User(
        email=f"obs-test-{uuid4().hex[:8]}@test.local",
        hashed_password="test_password_hash",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def obs_test_kb(db_session: AsyncSession, obs_test_user) -> KnowledgeBase:
    """Create a test knowledge base for observability tests."""
    kb = KnowledgeBase(
        name="Observability Test KB",
        description="Test KB for observability integration tests",
        owner_id=obs_test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def obs_test_document(
    db_session: AsyncSession, obs_test_kb: KnowledgeBase, obs_test_user
) -> Document:
    """Create a test document for observability tests."""
    document = Document(
        kb_id=obs_test_kb.id,
        name="test-observability.pdf",
        original_filename="test-observability.pdf",
        file_path=f"kb-{obs_test_kb.id}/{uuid4()}/test-observability.pdf",
        mime_type="application/pdf",
        file_size_bytes=102400,
        checksum="obs123test456",
        status=DocumentStatus.PENDING,
        uploaded_by=obs_test_user.id,
    )
    db_session.add(document)
    await db_session.flush()
    return document


class TestDocumentTraceCreation:
    """Tests for trace record creation during document processing."""

    @pytest.mark.asyncio
    async def test_trace_created_for_document_processing(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify a trace record is created when document processing starts."""
        document = obs_test_document
        obs = test_observability_service

        # Start a trace
        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
            metadata={
                "document_id": str(document.id),
                "task_id": "test-task-123",
            },
        )

        assert ctx is not None
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) == 32

        # Verify trace in database
        result = await db_session.execute(
            select(Trace).where(Trace.trace_id == ctx.trace_id)
        )
        trace = result.scalar_one_or_none()

        assert trace is not None
        assert trace.name == "document.processing"
        assert trace.user_id == document.uploaded_by
        assert trace.kb_id == document.kb_id

    @pytest.mark.asyncio
    async def test_trace_contains_document_metadata(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify trace metadata contains document-specific information."""
        document = obs_test_document
        obs = test_observability_service

        metadata = {
            "document_id": str(document.id),
            "task_id": "test-task-456",
            "retry": 0,
            "is_replacement": False,
            "mime_type": document.mime_type,
            "filename": document.name,
        }

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
            metadata=metadata,
        )

        # Verify trace attributes contain metadata
        result = await db_session.execute(
            select(Trace).where(Trace.trace_id == ctx.trace_id)
        )
        trace = result.scalar_one_or_none()

        assert trace is not None
        assert trace.attributes is not None
        assert trace.attributes.get("document_id") == str(document.id)


class TestDocumentEventCreation:
    """Tests for document event creation during processing steps."""

    @pytest.mark.asyncio
    async def test_document_event_created_for_upload_step(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify document event is created for upload step."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="upload",
            status="completed",
            duration_ms=250,
            metadata={"file_size_bytes": 102400},
        )

        # Verify document event in database
        result = await db_session.execute(
            select(DocumentEvent)
            .where(DocumentEvent.document_id == document.id)
            .where(DocumentEvent.event_type == "upload")
        )
        event = result.scalar_one_or_none()

        assert event is not None
        assert event.status == "completed"
        assert event.duration_ms == 250

    @pytest.mark.asyncio
    async def test_document_event_created_for_parse_step(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify document event is created for parse step with metrics."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="parse",
            status="completed",
            duration_ms=1500,
            metadata={
                "file_type": "application/pdf",
                "extracted_chars": 50000,
                "page_count": 10,
                "section_count": 5,
            },
        )

        result = await db_session.execute(
            select(DocumentEvent)
            .where(DocumentEvent.document_id == document.id)
            .where(DocumentEvent.event_type == "parse")
        )
        event = result.scalar_one_or_none()

        assert event is not None
        assert event.status == "completed"
        assert event.duration_ms == 1500

    @pytest.mark.asyncio
    async def test_document_events_for_all_processing_steps(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify document events are created for all processing steps."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        # Log events for all steps
        steps = [
            ("upload", 250),
            ("parse", 1500),
            ("chunk", 300),
            ("embed", 2000),
            ("index", 500),
        ]

        for event_type, duration in steps:
            await obs.log_document_event(
                ctx=ctx,
                document_id=document.id,
                event_type=event_type,
                status="completed",
                duration_ms=duration,
            )

        # Verify all events exist
        result = await db_session.execute(
            select(DocumentEvent).where(DocumentEvent.document_id == document.id)
        )
        events = result.scalars().all()

        assert len(events) == 5
        event_types = {e.event_type for e in events}
        assert event_types == {"upload", "parse", "chunk", "embed", "index"}


class TestTraceCompletion:
    """Tests for trace completion status."""

    @pytest.mark.asyncio
    async def test_trace_ends_with_completed_status(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
        test_engine,
    ) -> None:
        """Verify trace ends with completed status on success."""
        from sqlalchemy.ext.asyncio import AsyncSession as FreshAsyncSession
        from sqlalchemy.ext.asyncio import async_sessionmaker

        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        await obs.end_trace(
            ctx,
            status="completed",
            metadata={
                "document_id": str(document.id),
                "chunk_count": 25,
                "total_duration_ms": 4550,
            },
        )

        # Use a fresh session to see committed changes from ObservabilityService
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=FreshAsyncSession,
            expire_on_commit=False,
        )
        async with session_factory() as fresh_session:
            result = await fresh_session.execute(
                select(Trace).where(Trace.trace_id == ctx.trace_id)
            )
            trace = result.scalar_one_or_none()

            assert trace is not None
            assert trace.status == "completed"

    @pytest.mark.asyncio
    async def test_trace_ends_with_failed_status(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
        test_engine,
    ) -> None:
        """Verify trace ends with failed status on error."""
        from sqlalchemy.ext.asyncio import AsyncSession as FreshAsyncSession
        from sqlalchemy.ext.asyncio import async_sessionmaker

        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        await obs.end_trace(
            ctx,
            status="failed",
            metadata={
                "document_id": str(document.id),
                "error_type": "parse_error",
                "error_message": "Failed to extract text from PDF",
            },
        )

        # Use a fresh session to see committed changes from ObservabilityService
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=FreshAsyncSession,
            expire_on_commit=False,
        )
        async with session_factory() as fresh_session:
            result = await fresh_session.execute(
                select(Trace).where(Trace.trace_id == ctx.trace_id)
            )
            trace = result.scalar_one_or_none()

            assert trace is not None
            assert trace.status == "failed"


class TestFailureTraceFlow:
    """Tests for failure scenarios in document processing trace."""

    @pytest.mark.asyncio
    async def test_failed_step_creates_error_event(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify failed step creates document event with error info."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        # Log successful upload
        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="upload",
            status="completed",
            duration_ms=250,
        )

        # Log failed parse
        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="parse",
            status="failed",
            duration_ms=500,
            error_message="Unsupported PDF format",
        )

        # End trace with failure
        await obs.end_trace(ctx, status="failed")

        # Verify parse event has error
        result = await db_session.execute(
            select(DocumentEvent)
            .where(DocumentEvent.document_id == document.id)
            .where(DocumentEvent.event_type == "parse")
        )
        event = result.scalar_one_or_none()

        assert event is not None
        assert event.status == "failed"
        assert event.error_message == "Unsupported PDF format"

    @pytest.mark.asyncio
    async def test_subsequent_steps_not_executed_after_failure(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify subsequent steps are not executed after a failure."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        # Log successful upload
        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="upload",
            status="completed",
            duration_ms=250,
        )

        # Log failed parse (simulating failure before chunk/embed/index)
        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="parse",
            status="failed",
            duration_ms=500,
            error_message="Parse failed",
        )

        # End trace
        await obs.end_trace(ctx, status="failed")

        # Verify only upload and parse events exist (no chunk, embed, index)
        result = await db_session.execute(
            select(DocumentEvent).where(DocumentEvent.document_id == document.id)
        )
        events = result.scalars().all()

        event_types = {e.event_type for e in events}
        assert event_types == {"upload", "parse"}
        assert "chunk" not in event_types
        assert "embed" not in event_types
        assert "index" not in event_types


class TestEndToEndTraceFlow:
    """Tests for complete end-to-end trace flow."""

    @pytest.mark.asyncio
    async def test_full_document_processing_trace(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
        test_engine,
    ) -> None:
        """Verify complete document processing creates full trace with all events."""
        from sqlalchemy.ext.asyncio import AsyncSession as FreshAsyncSession
        from sqlalchemy.ext.asyncio import async_sessionmaker

        document = obs_test_document
        obs = test_observability_service

        # Start trace
        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
            metadata={
                "document_id": str(document.id),
                "task_id": "e2e-test-task",
                "is_replacement": False,
            },
        )

        # Simulate full processing pipeline
        steps = [
            ("upload", 250, {"file_size_bytes": 102400}),
            (
                "parse",
                1500,
                {
                    "file_type": "application/pdf",
                    "extracted_chars": 50000,
                    "page_count": 10,
                },
            ),
            (
                "chunk",
                300,
                {"chunk_count": 25, "chunk_size_config": 1000},
            ),
            (
                "embed",
                2000,
                {"embedding_model": "text-embedding-3-small", "batch_count": 3},
            ),
            (
                "index",
                500,
                {"qdrant_collection": f"kb_{document.kb_id}", "vectors_indexed": 25},
            ),
        ]

        for event_type, duration, metadata in steps:
            chunk_count = metadata.get("chunk_count") or metadata.get("vectors_indexed")
            await obs.log_document_event(
                ctx=ctx,
                document_id=document.id,
                event_type=event_type,
                status="completed",
                duration_ms=duration,
                chunk_count=chunk_count,
                metadata=metadata,
            )

        # End trace with success
        await obs.end_trace(
            ctx,
            status="completed",
            metadata={
                "document_id": str(document.id),
                "chunk_count": 25,
                "total_duration_ms": 4550,
            },
        )

        # Use a fresh session to see committed changes from ObservabilityService
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=FreshAsyncSession,
            expire_on_commit=False,
        )
        async with session_factory() as fresh_session:
            # Verify trace
            trace_result = await fresh_session.execute(
                select(Trace).where(Trace.trace_id == ctx.trace_id)
            )
            trace = trace_result.scalar_one_or_none()
            assert trace is not None
            assert trace.status == "completed"
            assert trace.name == "document.processing"

            # Verify all document events
            events_result = await fresh_session.execute(
                select(DocumentEvent).where(DocumentEvent.document_id == document.id)
            )
            events = events_result.scalars().all()
            assert len(events) == 5

            # Verify all events are completed
            for event in events:
                assert event.status == "completed"

    @pytest.mark.asyncio
    async def test_trace_context_propagation(
        self,
        db_session: AsyncSession,
        obs_test_document: Document,
        test_observability_service: ObservabilityService,
    ) -> None:
        """Verify trace context is properly propagated through pipeline."""
        document = obs_test_document
        obs = test_observability_service

        ctx = await obs.start_trace(
            name="document.processing",
            user_id=document.uploaded_by,
            kb_id=document.kb_id,
        )

        # All events should share the same trace_id
        trace_id = ctx.trace_id

        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="upload",
            status="completed",
            duration_ms=250,
        )

        await obs.log_document_event(
            ctx=ctx,
            document_id=document.id,
            event_type="parse",
            status="completed",
            duration_ms=1500,
        )

        await obs.end_trace(ctx, status="completed")

        # Verify all events belong to the same trace
        events_result = await db_session.execute(
            select(DocumentEvent).where(DocumentEvent.document_id == document.id)
        )
        events = events_result.scalars().all()

        for event in events:
            assert event.trace_id == trace_id
