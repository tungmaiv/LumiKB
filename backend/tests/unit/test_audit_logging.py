"""Unit tests for audit logging service generation methods."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.audit_service import AuditService


@pytest.fixture
def audit_service():
    """Create AuditService instance for testing."""
    return AuditService()


@pytest.fixture
def mock_audit_repo():
    """Mock AuditRepository for testing."""
    mock_repo = AsyncMock()
    mock_repo.create_event = AsyncMock()
    return mock_repo


@pytest.mark.asyncio
async def test_log_generation_request_creates_audit_event(
    audit_service, mock_audit_repo
):
    """Test log_generation_request creates correct event structure."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_generation_request(
                user_id=user_id,
                kb_id=kb_id,
                document_type="rfp_response",
                context="Need RFP response for banking project...",
                selected_source_count=5,
                request_id=request_id,
                template_id="rfp_response",
            )

    # Verify create_event was called with correct parameters
    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "generation.request"
    assert call_args.kwargs["resource_type"] == "draft"
    assert call_args.kwargs["user_id"] == user_id
    details = call_args.kwargs["details"]
    assert details["request_id"] == request_id
    assert details["kb_id"] == str(kb_id)
    assert details["document_type"] == "rfp_response"
    assert details["selected_source_count"] == 5
    assert details["template_id"] == "rfp_response"


@pytest.mark.asyncio
async def test_log_generation_complete_includes_metrics(audit_service, mock_audit_repo):
    """Test log_generation_complete includes all required metrics."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_generation_complete(
                user_id=user_id,
                request_id=request_id,
                kb_id=kb_id,
                document_type="rfp_response",
                citation_count=12,
                source_document_ids=["doc1", "doc2", "doc3"],
                generation_time_ms=3450,
                output_word_count=850,
                confidence_score=0.87,
            )

    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "generation.complete"
    details = call_args.kwargs["details"]
    assert details["request_id"] == request_id
    assert details["citation_count"] == 12
    assert details["source_document_ids"] == ["doc1", "doc2", "doc3"]
    assert details["generation_time_ms"] == 3450
    assert details["output_word_count"] == 850
    assert details["confidence_score"] == 0.87
    assert details["success"] is True


@pytest.mark.asyncio
async def test_log_generation_failed_includes_error_details(
    audit_service, mock_audit_repo
):
    """Test log_generation_failed includes error message and type."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_generation_failed(
                user_id=user_id,
                request_id=request_id,
                kb_id=kb_id,
                document_type="rfp_response",
                error_message="LLM service timeout after 30 seconds",
                error_type="TimeoutError",
                generation_time_ms=30100,
                failure_stage="llm_generation",
            )

    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "generation.failed"
    details = call_args.kwargs["details"]
    assert details["error_message"] == "LLM service timeout after 30 seconds"
    assert details["error_type"] == "TimeoutError"
    assert details["generation_time_ms"] == 30100
    assert details["failure_stage"] == "llm_generation"
    assert details["success"] is False


@pytest.mark.asyncio
async def test_log_feedback_links_to_draft(audit_service, mock_audit_repo):
    """Test log_feedback links to draft_id."""
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    related_request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_feedback(
                user_id=user_id,
                draft_id=draft_id,
                feedback_type="not_relevant",
                feedback_comments="This doesn't address our specific requirements.",
                related_request_id=related_request_id,
            )

    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "generation.feedback"
    assert call_args.kwargs["resource_type"] == "draft"
    assert call_args.kwargs["resource_id"] == draft_id
    details = call_args.kwargs["details"]
    assert details["feedback_type"] == "not_relevant"
    assert (
        details["feedback_comments"]
        == "This doesn't address our specific requirements."
    )
    assert details["related_request_id"] == related_request_id


@pytest.mark.asyncio
async def test_log_export_includes_file_size(audit_service, mock_audit_repo):
    """Test log_export includes file size and format."""
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    related_request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_export(
                user_id=user_id,
                draft_id=draft_id,
                export_format="docx",
                citation_count=15,
                file_size_bytes=245678,
                related_request_id=related_request_id,
            )

    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "document.export"
    assert call_args.kwargs["resource_type"] == "document"
    assert call_args.kwargs["resource_id"] == draft_id
    details = call_args.kwargs["details"]
    assert details["export_format"] == "docx"
    assert details["citation_count"] == 15
    assert details["file_size_bytes"] == 245678
    assert details["related_request_id"] == related_request_id


@pytest.mark.asyncio
async def test_log_export_failed_includes_error_details(audit_service, mock_audit_repo):
    """Test log_export_failed includes error message and format (AC-7.19.3)."""
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    kb_id = uuid.uuid4()

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_export_failed(
                user_id=user_id,
                draft_id=draft_id,
                export_format="pdf",
                error_message="PDF generation failed: missing fonts",
                kb_id=kb_id,
            )

    mock_audit_repo.create_event.assert_called_once()
    call_args = mock_audit_repo.create_event.call_args
    assert call_args.kwargs["action"] == "document.export_failed"
    assert call_args.kwargs["resource_type"] == "document"
    assert call_args.kwargs["resource_id"] == draft_id
    details = call_args.kwargs["details"]
    assert details["export_format"] == "pdf"
    assert details["error"] == "PDF generation failed: missing fonts"
    assert details["kb_id"] == str(kb_id)


@pytest.mark.asyncio
async def test_log_export_failed_truncates_long_errors(audit_service, mock_audit_repo):
    """Test log_export_failed truncates error messages to 500 chars (AC-7.19.3)."""
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    long_error = "e" * 1000  # 1000 character string

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_export_failed(
                user_id=user_id,
                draft_id=draft_id,
                export_format="docx",
                error_message=long_error,
            )

    call_args = mock_audit_repo.create_event.call_args
    details = call_args.kwargs["details"]
    assert len(details["error"]) == 500
    assert details["error"] == "e" * 500


@pytest.mark.asyncio
async def test_context_truncation_to_500_chars(audit_service, mock_audit_repo):
    """Test context is truncated to 500 characters."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    long_context = "a" * 1000  # 1000 character string

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_generation_request(
                user_id=user_id,
                kb_id=kb_id,
                document_type="test",
                context=long_context,
            )

    call_args = mock_audit_repo.create_event.call_args
    details = call_args.kwargs["details"]
    assert len(details["context"]) == 500
    assert details["context"] == "a" * 500


@pytest.mark.asyncio
async def test_error_message_sanitization(audit_service, mock_audit_repo):
    """Test error messages are truncated to 500 chars (PII sanitization)."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    request_id = str(uuid.uuid4())
    long_error = "x" * 1000

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            await audit_service.log_generation_failed(
                user_id=user_id,
                request_id=request_id,
                kb_id=kb_id,
                document_type="test",
                error_message=long_error,
                error_type="ValueError",
                generation_time_ms=100,
                failure_stage="unknown",
            )

    call_args = mock_audit_repo.create_event.call_args
    details = call_args.kwargs["details"]
    assert len(details["error_message"]) == 500
    assert details["error_message"] == "x" * 500


@pytest.mark.asyncio
async def test_request_id_linking(audit_service, mock_audit_repo):
    """Test request_id is consistent across events."""
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    request_id = str(uuid.uuid4())

    with patch("app.services.audit_service.async_session_factory") as mock_session:
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_ctx
        mock_session_ctx.__aexit__.return_value = None
        mock_session.return_value = mock_session_ctx

        with patch(
            "app.services.audit_service.AuditRepository",
            return_value=mock_audit_repo,
        ):
            # Log request
            await audit_service.log_generation_request(
                user_id=user_id,
                kb_id=kb_id,
                document_type="test",
                context="test",
                request_id=request_id,
            )

            # Log completion
            await audit_service.log_generation_complete(
                user_id=user_id,
                request_id=request_id,
                kb_id=kb_id,
                document_type="test",
                citation_count=5,
                source_document_ids=["doc1"],
                generation_time_ms=1000,
                output_word_count=100,
                confidence_score=0.8,
            )

    # Verify both calls used same request_id
    assert mock_audit_repo.create_event.call_count == 2
    first_call = mock_audit_repo.create_event.call_args_list[0]
    second_call = mock_audit_repo.create_event.call_args_list[1]
    assert first_call.kwargs["details"]["request_id"] == request_id
    assert second_call.kwargs["details"]["request_id"] == request_id
