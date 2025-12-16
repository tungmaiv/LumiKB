"""Unit tests for document archive functionality (Story 6-1)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.services.document_service import DocumentService, DocumentValidationError


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_superuser = False
    return user


@pytest.fixture
def mock_admin_user() -> User:
    """Create a mock admin user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.is_superuser = True
    return user


@pytest.fixture
def ready_document() -> Document:
    """Create a mock READY document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "test_document.pdf"
    doc.status = DocumentStatus.READY
    doc.archived_at = None
    doc.deleted_at = None
    return doc


@pytest.fixture
def archived_document() -> Document:
    """Create a mock already archived document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "archived_document.pdf"
    doc.status = DocumentStatus.READY
    doc.archived_at = datetime.now(UTC)
    doc.deleted_at = None
    return doc


@pytest.fixture
def pending_document() -> Document:
    """Create a mock PENDING document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "pending_document.pdf"
    doc.status = DocumentStatus.PENDING
    doc.archived_at = None
    doc.deleted_at = None
    return doc


@pytest.fixture
def processing_document() -> Document:
    """Create a mock PROCESSING document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "processing_document.pdf"
    doc.status = DocumentStatus.PROCESSING
    doc.archived_at = None
    doc.deleted_at = None
    return doc


@pytest.fixture
def failed_document() -> Document:
    """Create a mock FAILED document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "failed_document.pdf"
    doc.status = DocumentStatus.FAILED
    doc.archived_at = None
    doc.deleted_at = None
    return doc


class TestArchiveDocument:
    """Test cases for DocumentService.archive() method."""

    @pytest.mark.asyncio
    async def test_archive_ready_document_success(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Successfully archive a READY document."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        # Mock permission check
        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            result = await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_user,
            )

            assert result.archived_at is not None
            mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_requires_write_permission(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Archive requires WRITE permission on KB."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with patch.object(
            service, "_check_kb_permission", new_callable=AsyncMock
        ) as mock_perm:
            mock_perm.return_value = False

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=ready_document.kb_id,
                    doc_id=ready_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_archive_only_ready_documents(
        self,
        pending_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Only READY documents can be archived."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = pending_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=pending_document.kb_id,
                    doc_id=pending_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "INVALID_STATUS"
            assert "READY" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_archive_processing_document_fails(
        self,
        processing_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: PROCESSING documents cannot be archived."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = processing_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=processing_document.kb_id,
                    doc_id=processing_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_archive_failed_document_fails(
        self,
        failed_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: FAILED documents cannot be archived."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = failed_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=failed_document.kb_id,
                    doc_id=failed_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_archive_already_archived_fails(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Already archived documents cannot be archived again."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=archived_document.kb_id,
                    doc_id=archived_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "ALREADY_ARCHIVED"

    @pytest.mark.asyncio
    async def test_archive_document_not_found(
        self,
        mock_user: User,
    ) -> None:
        """Archive returns 404 for non-existent document."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = uuid4()
        doc_id = uuid4()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.archive(
                    kb_id=kb_id,
                    doc_id=doc_id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_archive_sets_timestamp(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Archive sets archived_at timestamp."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            before_archive = datetime.now(UTC)
            result = await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_user,
            )
            after_archive = datetime.now(UTC)

            assert result.archived_at is not None
            # Verify timestamp is within expected range
            assert before_archive <= result.archived_at <= after_archive

    @pytest.mark.asyncio
    async def test_archive_updates_qdrant_payload(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Archive updates Qdrant payload with archived=true."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_user,
            )

            # Verify Qdrant set_payload was called
            mock_qdrant.client.set_payload.assert_called_once()
            call_kwargs = mock_qdrant.client.set_payload.call_args
            assert call_kwargs.kwargs["payload"] == {"archived": True}
            assert call_kwargs.kwargs["collection_name"] == f"kb_{ready_document.kb_id}"

    @pytest.mark.asyncio
    async def test_archive_logs_audit_event(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC5: Archive logs audit event."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_user,
            )

            mock_audit.log_event.assert_called_once()
            call_kwargs = mock_audit.log_event.call_args.kwargs
            assert call_kwargs["action"] == "document.archived"
            assert call_kwargs["resource_type"] == "document"
            assert call_kwargs["user_id"] == mock_user.id
            assert call_kwargs["resource_id"] == ready_document.id

    @pytest.mark.asyncio
    async def test_archive_qdrant_failure_does_not_block(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Qdrant failure is logged but doesn't block archive."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.logger") as mock_logger,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            # Simulate Qdrant failure
            mock_qdrant.client.set_payload.side_effect = Exception("Qdrant down")

            # Should still succeed
            result = await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_user,
            )

            assert result.archived_at is not None
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "qdrant_archive_payload_failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_archive_admin_can_archive_any_kb(
        self,
        ready_document: Document,
        mock_admin_user: User,
    ) -> None:
        """Superusers can archive documents in any KB."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
        ):
            # Admin always has permission
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            result = await service.archive(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                user=mock_admin_user,
            )

            assert result.archived_at is not None
