"""Integration tests for Document processing pipeline.

Tests cover:
- Outbox event triggers processing (AC: 1)
- Status transitions: PENDING → PROCESSING → (success path | FAILED) (AC: 1)
- Retry mechanism on transient failures (AC: 8)
- Max retries exhaustion marks FAILED (AC: 8)
- Cleanup of temporary files (AC: 9)

Note: These tests mock MinIO and unstructured to test the processing logic
without requiring external services for document parsing.

Worker tests use sync functions and mock _get_document/_update_document_status
since the Celery task is synchronous and runs in isolation.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from tests.factories import create_document, create_knowledge_base, create_outbox_event

pytestmark = pytest.mark.integration


def sync_run_async(coro):
    """Replacement run_async for tests - runs coro in fresh event loop."""
    return asyncio.run(coro)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Minimal PDF content for testing."""
    return b"%PDF-1.4\n%Test PDF content with sufficient text for parsing validation."


@pytest.fixture
def parsed_content_mock() -> MagicMock:
    """Mock ParsedContent for successful parsing."""
    from app.workers.parsing import ParsedContent, ParsedElement

    return ParsedContent(
        text="A" * 200,  # > 100 chars
        elements=[
            ParsedElement(text="A" * 200, element_type="NarrativeText", metadata={})
        ],
        metadata={
            "page_count": 1,
            "section_count": 0,
            "element_count": 1,
            "source_format": "pdf",
        },
    )


@pytest.fixture
def mock_document() -> Document:
    """Create a mock Document object for worker tests."""
    doc = MagicMock(spec=Document)
    doc.id = uuid.uuid4()
    doc.kb_id = uuid.uuid4()
    doc.name = "test.pdf"
    doc.original_filename = "test.pdf"
    doc.mime_type = "application/pdf"
    doc.file_size_bytes = 1024
    doc.file_path = f"kb-{doc.kb_id}/{doc.id}/test.pdf"
    doc.checksum = "abc123"
    doc.status = DocumentStatus.PENDING
    doc.retry_count = 0
    doc.processing_started_at = None
    doc.processing_completed_at = None
    doc.last_error = None
    return doc


# =============================================================================
# AC 1: Outbox Event Triggers Processing
# =============================================================================


async def test_outbox_processor_dispatches_document_event(
    db_session: AsyncSession,
) -> None:
    """Test outbox processor dispatches document.process events."""
    # Create KB and document
    kb = await create_knowledge_base(db_session)
    doc = await create_document(
        db_session,
        kb_id=kb.id,
        status=DocumentStatus.PENDING,
        file_path=f"kb-{kb.id}/{uuid.uuid4()}/test.pdf",
    )

    # Create outbox event
    outbox_event = await create_outbox_event(
        db_session,
        event_type="document.process",
        aggregate_id=doc.id,
        aggregate_type="document",
        payload={
            "document_id": str(doc.id),
            "kb_id": str(kb.id),
            "file_path": doc.file_path,
            "mime_type": "application/pdf",
            "checksum": doc.checksum,
        },
    )
    await db_session.commit()

    # Mock the document task to verify dispatch
    # Patch at the import location inside dispatch_event
    with patch("app.workers.document_tasks.process_document") as mock_task:
        mock_task.delay = MagicMock()

        from app.workers.outbox_tasks import dispatch_event

        dispatch_event(
            {
                "id": str(outbox_event.id),
                "event_type": "document.process",
                "aggregate_id": str(doc.id),
                "aggregate_type": "document",
                "payload": {
                    "document_id": str(doc.id),
                    "kb_id": str(kb.id),
                },
                "attempts": 0,
            }
        )

        mock_task.delay.assert_called_once_with(str(doc.id))


# =============================================================================
# AC 1: Status Transitions - Success Path
# =============================================================================


def test_processing_updates_status_to_processing(
    sample_pdf_content: bytes,
    parsed_content_mock: MagicMock,
    mock_document: Document,
) -> None:
    """Test document status updates to PROCESSING when task starts."""
    status_updates = []

    async def mock_update_status(
        doc_id,
        status,
        error=None,
        processing_started=False,
        processing_completed=False,
        retry_count=None,
        chunk_count=None,
    ):
        status_updates.append(
            {
                "doc_id": doc_id,
                "status": status,
                "error": error,
                "processing_started": processing_started,
                "processing_completed": processing_completed,
                "retry_count": retry_count,
                "chunk_count": chunk_count,
            }
        )

    async def mock_get_document(doc_id):
        return mock_document

    async def mock_chunk_embed_index(
        doc_id, kb_id, document_name, is_replacement=False
    ):
        return 10  # Mock 10 chunks

    # Compute checksum for test data
    import hashlib

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks.minio_service.download_file",
                    new_callable=AsyncMock,
                    return_value=sample_pdf_content,
                ):
                    with patch(
                        "app.workers.document_tasks.parse_document",
                        return_value=parsed_content_mock,
                    ):
                        with patch(
                            "app.workers.document_tasks.store_parsed_content",
                            new_callable=AsyncMock,
                        ):
                            with patch(
                                "app.workers.document_tasks._chunk_embed_index",
                                mock_chunk_embed_index,
                            ):
                                with patch(
                                    "app.workers.document_tasks.delete_parsed_content",
                                    AsyncMock(),
                                ):
                                    with patch(
                                        "app.workers.document_tasks._mark_outbox_processed",
                                        AsyncMock(),
                                    ):
                                        from app.workers.document_tasks import (
                                            process_document,
                                        )

                                        result = process_document(str(mock_document.id))

    # Verify PROCESSING status was set
    assert len(status_updates) >= 1
    first_update = status_updates[0]
    assert first_update["status"] == DocumentStatus.PROCESSING
    assert first_update["processing_started"] is True
    assert result["status"] == "success"


def test_processing_validates_checksum(
    mock_document: Document,
) -> None:
    """Test document processing validates file checksum."""
    mock_document.checksum = "expected_checksum_hash"
    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append(
            {
                "status": status,
                "error": error,
            }
        )

    async def mock_get_document(doc_id):
        return mock_document

    # Return different content (wrong checksum)
    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks.minio_service.download_file",
                    new_callable=AsyncMock,
                    return_value=b"different content",
                ):
                    from app.workers.document_tasks import process_document

                    # Mock retry to raise so we can check failure handling
                    with patch.object(
                        process_document, "retry", side_effect=Exception("retry")
                    ):
                        try:
                            process_document(str(mock_document.id))
                        except Exception:
                            pass

    # Verify FAILED status was set with checksum error
    failed_updates = [u for u in status_updates if u["status"] == DocumentStatus.FAILED]
    assert len(failed_updates) >= 1
    assert "checksum" in failed_updates[0]["error"].lower()


# =============================================================================
# AC 5, 6, 7: Failure Modes
# =============================================================================


def test_insufficient_content_marks_failed(
    sample_pdf_content: bytes,
    mock_document: Document,
) -> None:
    """Test document with <100 chars extracted is marked FAILED."""
    import hashlib

    from app.workers.parsing import InsufficientContentError

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()
    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append({"status": status, "error": error})

    async def mock_get_document(doc_id):
        return mock_document

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            side_effect=InsufficientContentError(
                                "No text content found (extracted 50 chars, minimum 100)"
                            ),
                        ):
                            from app.workers.document_tasks import process_document

                            result = process_document(str(mock_document.id))

    # Find FAILED status update
    failed_updates = [u for u in status_updates if u["status"] == DocumentStatus.FAILED]
    assert len(failed_updates) >= 1
    assert "50 chars" in failed_updates[0]["error"]
    assert result["status"] == "failed"
    assert result["reason"] == "insufficient_content"


def test_scanned_pdf_marks_failed(
    sample_pdf_content: bytes,
    mock_document: Document,
) -> None:
    """Test scanned PDF (no text) is marked FAILED with OCR message."""
    import hashlib

    from app.workers.parsing import ScannedDocumentError

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()
    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append({"status": status, "error": error})

    async def mock_get_document(doc_id):
        return mock_document

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            side_effect=ScannedDocumentError(
                                "Document appears to be scanned (OCR required - MVP 2)"
                            ),
                        ):
                            from app.workers.document_tasks import process_document

                            result = process_document(str(mock_document.id))

    failed_updates = [u for u in status_updates if u["status"] == DocumentStatus.FAILED]
    assert len(failed_updates) >= 1
    assert "OCR" in failed_updates[0]["error"]
    assert result["reason"] == "scanned_document"


def test_password_protected_pdf_marks_failed(
    sample_pdf_content: bytes,
    mock_document: Document,
) -> None:
    """Test password-protected PDF is marked FAILED."""
    import hashlib

    from app.workers.parsing import PasswordProtectedError

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()
    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append({"status": status, "error": error})

    async def mock_get_document(doc_id):
        return mock_document

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            side_effect=PasswordProtectedError(
                                "Password-protected PDF cannot be processed"
                            ),
                        ):
                            from app.workers.document_tasks import process_document

                            result = process_document(str(mock_document.id))

    failed_updates = [u for u in status_updates if u["status"] == DocumentStatus.FAILED]
    assert len(failed_updates) >= 1
    assert "Password-protected" in failed_updates[0]["error"]
    assert result["reason"] == "password_protected"


# =============================================================================
# AC 8: Retry Mechanism
# =============================================================================


def test_transient_error_triggers_retry(
    mock_document: Document,
) -> None:
    """Test transient errors trigger retry with backoff."""
    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append({"status": status, "retry_count": retry_count})

    async def mock_get_document(doc_id):
        return mock_document

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks.minio_service.download_file",
                    new_callable=AsyncMock,
                    side_effect=Exception("Network error"),
                ):
                    from app.workers.document_tasks import process_document

                    # Mock the task to capture retry calls
                    with patch.object(
                        process_document,
                        "retry",
                        side_effect=Exception("Retry triggered"),
                    ) as mock_retry:
                        try:
                            process_document(str(mock_document.id))
                        except Exception as e:
                            assert "Retry triggered" in str(e)

                        # Verify retry was called
                        assert mock_retry.called


def test_max_retries_marks_failed(
    mock_document: Document,
) -> None:
    """Test max retries exhaustion marks document FAILED."""
    from celery.exceptions import MaxRetriesExceededError

    status_updates = []

    async def mock_update_status(
        doc_id, status, error=None, processing_started=False, retry_count=None
    ):
        status_updates.append({"status": status, "retry_count": retry_count})

    async def mock_get_document(doc_id):
        return mock_document

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        side_effect=Exception("Persistent error"),
                    ):
                        from app.workers.document_tasks import process_document

                        # Mock retry to raise MaxRetriesExceededError
                        with patch.object(
                            process_document,
                            "retry",
                            side_effect=MaxRetriesExceededError(),
                        ):
                            result = process_document(str(mock_document.id))

    # Verify FAILED status was set
    failed_updates = [u for u in status_updates if u["status"] == DocumentStatus.FAILED]
    assert len(failed_updates) >= 1
    assert result["reason"] == "max_retries_exhausted"


# =============================================================================
# AC 9: Cleanup of Temporary Files
# =============================================================================


def test_temp_files_cleaned_on_success(
    sample_pdf_content: bytes,
    parsed_content_mock: MagicMock,
    mock_document: Document,
) -> None:
    """Test temporary files are cleaned up after successful processing."""
    import hashlib

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()

    async def mock_get_document(doc_id):
        return mock_document

    async def mock_update_status(*args, **kwargs):
        pass

    async def mock_chunk_embed_index(
        doc_id, kb_id, document_name, is_replacement=False
    ):
        return 10  # Mock 10 chunks

    cleanup_called = []

    def mock_cleanup(path):
        cleanup_called.append(path)

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            return_value=parsed_content_mock,
                        ):
                            with patch(
                                "app.workers.document_tasks.store_parsed_content",
                                new_callable=AsyncMock,
                            ):
                                with patch(
                                    "app.workers.document_tasks._chunk_embed_index",
                                    mock_chunk_embed_index,
                                ):
                                    with patch(
                                        "app.workers.document_tasks.delete_parsed_content",
                                        AsyncMock(),
                                    ):
                                        with patch(
                                            "app.workers.document_tasks._cleanup_temp_dir",
                                            mock_cleanup,
                                        ):
                                            from app.workers.document_tasks import (
                                                process_document,
                                            )

                                            process_document(str(mock_document.id))

                                            # Verify cleanup was called
                                            assert len(cleanup_called) >= 1


def test_temp_files_cleaned_on_failure(
    sample_pdf_content: bytes,
    mock_document: Document,
) -> None:
    """Test temporary files are cleaned up even on failure."""
    import hashlib

    from celery.exceptions import MaxRetriesExceededError

    from app.workers.parsing import ParsingError

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()

    async def mock_get_document(doc_id):
        return mock_document

    async def mock_update_status(*args, **kwargs):
        pass

    cleanup_called = []

    def mock_cleanup(path):
        cleanup_called.append(path)

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed", AsyncMock()
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            side_effect=ParsingError("Parse failed"),
                        ):
                            with patch(
                                "app.workers.document_tasks._cleanup_temp_dir",
                                mock_cleanup,
                            ):
                                from app.workers.document_tasks import process_document

                                with patch.object(
                                    process_document,
                                    "retry",
                                    side_effect=MaxRetriesExceededError(),
                                ):
                                    process_document(str(mock_document.id))

                                # Cleanup should still be called on failure
                                assert len(cleanup_called) >= 1


# =============================================================================
# Outbox Processing
# =============================================================================


def test_outbox_event_marked_processed_on_success(
    sample_pdf_content: bytes,
    parsed_content_mock: MagicMock,
    mock_document: Document,
) -> None:
    """Test outbox event is marked processed after successful parsing."""
    import hashlib

    mock_document.checksum = hashlib.sha256(sample_pdf_content).hexdigest()

    outbox_marked = []

    async def mock_get_document(doc_id):
        return mock_document

    async def mock_update_status(*args, **kwargs):
        pass

    async def mock_mark_outbox(aggregate_id):
        outbox_marked.append(aggregate_id)

    async def mock_chunk_embed_index(
        doc_id, kb_id, document_name, is_replacement=False
    ):
        return 10  # Mock 10 chunks

    with patch("app.workers.document_tasks.run_async", sync_run_async):
        with patch("app.workers.document_tasks._get_document", mock_get_document):
            with patch(
                "app.workers.document_tasks._update_document_status", mock_update_status
            ):
                with patch(
                    "app.workers.document_tasks._mark_outbox_processed",
                    mock_mark_outbox,
                ):
                    with patch(
                        "app.workers.document_tasks.minio_service.download_file",
                        new_callable=AsyncMock,
                        return_value=sample_pdf_content,
                    ):
                        with patch(
                            "app.workers.document_tasks.parse_document",
                            return_value=parsed_content_mock,
                        ):
                            with patch(
                                "app.workers.document_tasks.store_parsed_content",
                                new_callable=AsyncMock,
                            ):
                                with patch(
                                    "app.workers.document_tasks._chunk_embed_index",
                                    mock_chunk_embed_index,
                                ):
                                    with patch(
                                        "app.workers.document_tasks.delete_parsed_content",
                                        AsyncMock(),
                                    ):
                                        from app.workers.document_tasks import (
                                            process_document,
                                        )

                                        process_document(str(mock_document.id))

    # Verify outbox was marked processed
    assert str(mock_document.id) in outbox_marked
