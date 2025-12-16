"""Unit tests for document lifecycle functionality (Stories 6-2 through 6-6)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.services.document_service import DocumentService, DocumentValidationError

# ============================================================================
# Fixtures
# ============================================================================


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
    doc.original_filename = "test_document.pdf"
    doc.file_path = f"kbs/{doc.kb_id}/{doc.id}/test_document.pdf"
    doc.status = DocumentStatus.READY
    doc.archived_at = None
    doc.deleted_at = None
    doc.tags = ["test", "document"]
    doc.created_at = datetime.now(UTC)
    doc.updated_at = datetime.now(UTC)
    doc.mime_type = "application/pdf"
    doc.file_size_bytes = 1024
    doc.checksum = "abc123"
    return doc


@pytest.fixture
def archived_document() -> Document:
    """Create a mock already archived document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "archived_document.pdf"
    doc.original_filename = "archived_document.pdf"
    doc.file_path = f"kbs/{doc.kb_id}/{doc.id}/archived_document.pdf"
    doc.status = DocumentStatus.READY
    doc.archived_at = datetime.now(UTC)
    doc.deleted_at = None
    doc.tags = []
    doc.created_at = datetime.now(UTC)
    doc.updated_at = datetime.now(UTC)
    return doc


@pytest.fixture
def pending_document() -> Document:
    """Create a mock PENDING document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.kb_id = uuid4()
    doc.name = "pending_document.pdf"
    doc.original_filename = "pending_document.pdf"
    doc.file_path = f"kbs/{doc.kb_id}/{doc.id}/pending_document.pdf"
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
    doc.original_filename = "processing_document.pdf"
    doc.file_path = f"kbs/{doc.kb_id}/{doc.id}/processing_document.pdf"
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
    doc.original_filename = "failed_document.pdf"
    doc.file_path = f"kbs/{doc.kb_id}/{doc.id}/failed_document.pdf"
    doc.status = DocumentStatus.FAILED
    doc.archived_at = None
    doc.deleted_at = None
    return doc


# ============================================================================
# Story 6-2: Restore Document Tests
# ============================================================================


class TestRestoreDocument:
    """Test cases for DocumentService.restore() method (Story 6-2)."""

    @pytest.mark.asyncio
    async def test_restore_archived_document_success(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Successfully restore an archived document."""
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

            # First call returns the archived document, second returns None (no collision)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = archived_document
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = None
            mock_exec.side_effect = [mock_result1, mock_result2]

            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            await service.restore(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            # Verify archived_at was cleared
            assert archived_document.archived_at is None
            mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_requires_write_permission(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Restore requires WRITE permission on KB."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with patch.object(
            service, "_check_kb_permission", new_callable=AsyncMock
        ) as mock_perm:
            mock_perm.return_value = False

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.restore(
                    kb_id=archived_document.kb_id,
                    doc_id=archived_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_restore_non_archived_document_fails(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Cannot restore a document that is not archived."""
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
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.restore(
                    kb_id=ready_document.kb_id,
                    doc_id=ready_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "NOT_ARCHIVED"

    @pytest.mark.asyncio
    async def test_restore_updates_qdrant_payload(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Restore updates Qdrant payload with archived=false."""
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

            # First call returns the archived document, second returns None (no collision)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = archived_document
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = None
            mock_exec.side_effect = [mock_result1, mock_result2]

            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            await service.restore(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            # Verify Qdrant set_payload was called with archived=False
            mock_qdrant.client.set_payload.assert_called_once()
            call_kwargs = mock_qdrant.client.set_payload.call_args
            assert call_kwargs.kwargs["payload"] == {
                "archived": False,
                "status": "completed",
            }

    @pytest.mark.asyncio
    async def test_restore_logs_audit_event(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Restore logs audit event."""
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

            # First call returns the archived document, second returns None (no collision)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = archived_document
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = None
            mock_exec.side_effect = [mock_result1, mock_result2]

            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()

            await service.restore(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            mock_audit.log_event.assert_called_once()
            call_kwargs = mock_audit.log_event.call_args.kwargs
            assert call_kwargs["action"] == "document.restored"
            assert call_kwargs["resource_type"] == "document"

    @pytest.mark.asyncio
    async def test_restore_document_not_found(
        self,
        mock_user: User,
    ) -> None:
        """Restore returns 404 for non-existent document."""
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
                await service.restore(
                    kb_id=kb_id,
                    doc_id=doc_id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.code == "NOT_FOUND"


# ============================================================================
# Story 6-3: Purge Document Tests
# ============================================================================


class TestPurgeDocument:
    """Test cases for DocumentService.purge_document() method (Story 6-3)."""

    @pytest.mark.asyncio
    async def test_purge_archived_document_success(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Successfully purge an archived document."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock) as mock_delete,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.purge_document(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            # Verify document was deleted from session
            mock_delete.assert_called_once_with(archived_document)
            mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_non_archived_document_fails(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Cannot purge a document that is not archived."""
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
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.purge_document(
                    kb_id=ready_document.kb_id,
                    doc_id=ready_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "NOT_ARCHIVED"

    @pytest.mark.asyncio
    async def test_purge_deletes_qdrant_vectors(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Purge deletes vectors from Qdrant."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.purge_document(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            # Verify Qdrant delete was called
            mock_qdrant.client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_deletes_minio_file(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Purge deletes file from MinIO."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.purge_document(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            # Verify MinIO delete was called
            mock_minio.delete_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_logs_audit_event(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Purge logs audit event."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.purge_document(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                user=mock_user,
            )

            mock_audit.log_event.assert_called_once()
            call_kwargs = mock_audit.log_event.call_args.kwargs
            assert call_kwargs["action"] == "document.purged"


class TestBulkPurge:
    """Test cases for DocumentService.bulk_purge() method (Story 6-3)."""

    @pytest.mark.asyncio
    async def test_bulk_purge_multiple_documents(
        self,
        mock_user: User,
    ) -> None:
        """AC5: Bulk purge multiple archived documents."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = uuid4()

        # Create mock archived documents
        doc1 = MagicMock(spec=Document)
        doc1.id = uuid4()
        doc1.kb_id = kb_id
        doc1.archived_at = datetime.now(UTC)
        doc1.file_path = f"kbs/{kb_id}/{doc1.id}/doc1.pdf"

        doc2 = MagicMock(spec=Document)
        doc2.id = uuid4()
        doc2.kb_id = kb_id
        doc2.archived_at = datetime.now(UTC)
        doc2.file_path = f"kbs/{kb_id}/{doc2.id}/doc2.pdf"

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True

            # Return different documents for each query
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = doc1
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = doc2
            mock_exec.side_effect = [mock_result1, mock_result2]

            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            result = await service.bulk_purge(
                kb_id=kb_id,
                document_ids=[doc1.id, doc2.id],
                user=mock_user,
            )

            assert result["purged"] == 2
            assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_bulk_purge_skips_non_archived(
        self,
        mock_user: User,
    ) -> None:
        """AC6: Bulk purge skips non-archived documents."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = uuid4()

        # One archived, one not
        archived_doc = MagicMock(spec=Document)
        archived_doc.id = uuid4()
        archived_doc.kb_id = kb_id
        archived_doc.archived_at = datetime.now(UTC)
        archived_doc.file_path = f"kbs/{kb_id}/{archived_doc.id}/doc.pdf"

        non_archived_doc = MagicMock(spec=Document)
        non_archived_doc.id = uuid4()
        non_archived_doc.kb_id = kb_id
        non_archived_doc.archived_at = None  # Not archived

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True

            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = archived_doc
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = non_archived_doc
            mock_exec.side_effect = [mock_result1, mock_result2]

            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            result = await service.bulk_purge(
                kb_id=kb_id,
                document_ids=[archived_doc.id, non_archived_doc.id],
                user=mock_user,
            )

            assert result["purged"] == 1
            assert result["skipped"] == 1
            assert str(non_archived_doc.id) in result["skipped_ids"]


# ============================================================================
# Story 6-4: Clear Failed Document Tests
# ============================================================================


class TestClearFailedDocument:
    """Test cases for DocumentService.clear_failed_document() method (Story 6-4)."""

    @pytest.mark.asyncio
    async def test_clear_failed_document_success(
        self,
        failed_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Successfully clear a failed document."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock) as mock_delete,
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = failed_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.clear_failed_document(
                kb_id=failed_document.kb_id,
                doc_id=failed_document.id,
                user=mock_user,
            )

            mock_delete.assert_called_once_with(failed_document)
            mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_non_failed_document_fails(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Cannot clear a document that is not FAILED."""
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
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.clear_failed_document(
                    kb_id=ready_document.kb_id,
                    doc_id=ready_document.id,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "NOT_FAILED"

    @pytest.mark.asyncio
    async def test_clear_deletes_partial_vectors(
        self,
        failed_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Clear deletes any partial vectors from Qdrant."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = failed_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.clear_failed_document(
                kb_id=failed_document.kb_id,
                doc_id=failed_document.id,
                user=mock_user,
            )

            # Verify Qdrant delete was called
            mock_qdrant.client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_logs_audit_with_reason(
        self,
        failed_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Clear logs audit event with optional reason."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = failed_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()

            await service.clear_failed_document(
                kb_id=failed_document.kb_id,
                doc_id=failed_document.id,
                user=mock_user,
                reason="duplicate_upload",
            )

            mock_audit.log_event.assert_called_once()
            call_kwargs = mock_audit.log_event.call_args.kwargs
            # Auto-cleared when reason is duplicate_upload
            assert call_kwargs["action"] == "document.auto_cleared"
            assert "duplicate_upload" in str(call_kwargs.get("details", {}))


# ============================================================================
# Story 6-5: Duplicate Detection Tests
# ============================================================================


class TestDuplicateDetection:
    """Test cases for duplicate detection in upload (Story 6-5)."""

    @pytest.mark.asyncio
    async def test_upload_with_duplicate_failed_auto_clears(
        self,
        failed_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Uploading a file with same name as FAILED document auto-clears."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = failed_document.kb_id

        # Mock file upload
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = failed_document.original_filename
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(
                service, "clear_failed_document", new_callable=AsyncMock
            ) as mock_clear,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "add"),
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_audit.log_event = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/file")

            # First query returns failed document (duplicate check)
            # Second query returns None (checksum check)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = failed_document
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = None
            mock_exec.side_effect = [mock_result1, mock_result2]

            document, auto_cleared_id = await service.upload(
                kb_id=kb_id,
                file=mock_file,
                user=mock_user,
            )

            # Verify auto-clear was called
            mock_clear.assert_called_once()
            assert auto_cleared_id == failed_document.id

    @pytest.mark.asyncio
    async def test_upload_with_duplicate_processing_returns_409(
        self,
        processing_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Uploading a file with same name as PROCESSING document returns 409."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = processing_document.kb_id

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = processing_document.original_filename
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        mock_file.seek = AsyncMock()

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
                await service.upload(
                    kb_id=kb_id,
                    file=mock_file,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 409
            assert exc_info.value.code == "DUPLICATE_PROCESSING"

    @pytest.mark.asyncio
    async def test_upload_with_duplicate_ready_returns_409(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Uploading a file with same name as READY document returns 409."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = ready_document.kb_id

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = ready_document.original_filename
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.upload(
                    kb_id=kb_id,
                    file=mock_file,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 409
            assert exc_info.value.code == "DUPLICATE_DOCUMENT"

    @pytest.mark.asyncio
    async def test_duplicate_detection_case_insensitive(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Duplicate detection is case-insensitive."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        kb_id = ready_document.kb_id

        # Upload with different case
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = ready_document.original_filename.upper()  # Different case
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
        ):
            mock_perm.return_value = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result

            with pytest.raises(DocumentValidationError) as exc_info:
                await service.upload(
                    kb_id=kb_id,
                    file=mock_file,
                    user=mock_user,
                )

            # Should still detect as duplicate despite case difference
            assert exc_info.value.status_code == 409


# ============================================================================
# Story 6-6: Replace Document Tests
# ============================================================================


class TestReplaceDocument:
    """Test cases for DocumentService.replace_document() method (Story 6-6)."""

    @pytest.mark.asyncio
    async def test_replace_ready_document_success(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC1: Successfully replace a READY document."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            # Verify status set to PENDING
            assert ready_document.status == DocumentStatus.PENDING
            mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_replace_processing_document_fails(
        self,
        processing_document: Document,
        mock_user: User,
    ) -> None:
        """AC2: Cannot replace while processing."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

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
                await service.replace_document(
                    kb_id=processing_document.kb_id,
                    doc_id=processing_document.id,
                    file=mock_file,
                    user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "PROCESSING_IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_replace_preserves_document_id(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Replace preserves document ID."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        original_id = ready_document.id

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            result = await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            assert result.id == original_id

    @pytest.mark.asyncio
    async def test_replace_preserves_created_at(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Replace preserves created_at timestamp."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        original_created_at = ready_document.created_at

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            result = await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            assert result.created_at == original_created_at

    @pytest.mark.asyncio
    async def test_replace_preserves_tags(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC3: Replace preserves tags."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)
        original_tags = ready_document.tags.copy()

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            result = await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            assert result.tags == original_tags

    @pytest.mark.asyncio
    async def test_replace_deletes_old_vectors(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Replace deletes old Qdrant vectors."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            # Verify Qdrant delete was called
            mock_qdrant.client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_replace_deletes_old_file(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC4: Replace deletes old MinIO file."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            # Verify MinIO delete was called
            mock_minio.delete_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_replace_creates_outbox_event(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC5: Replace creates outbox event for processing."""
        mock_session = AsyncMock()
        mock_add = MagicMock()
        mock_session.add = mock_add
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            # Verify outbox event was added to session
            mock_add.assert_called()

    @pytest.mark.asyncio
    async def test_replace_clears_archived_at(
        self,
        archived_document: Document,
        mock_user: User,
    ) -> None:
        """AC6: Replace clears archived_at if document was archived."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = archived_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=archived_document.kb_id,
                doc_id=archived_document.id,
                file=mock_file,
                user=mock_user,
            )

            # Verify archived_at was cleared
            assert archived_document.archived_at is None

    @pytest.mark.asyncio
    async def test_replace_logs_audit_event(
        self,
        ready_document: Document,
        mock_user: User,
    ) -> None:
        """AC7: Replace logs audit event."""
        mock_session = AsyncMock()
        service = DocumentService(mock_session)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "new_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"new content")
        mock_file.seek = AsyncMock()

        with (
            patch.object(
                service, "_check_kb_permission", new_callable=AsyncMock
            ) as mock_perm,
            patch.object(mock_session, "execute", new_callable=AsyncMock) as mock_exec,
            patch.object(mock_session, "flush", new_callable=AsyncMock),
            patch.object(mock_session, "add"),
            patch("app.services.document_service.audit_service") as mock_audit,
            patch("app.integrations.qdrant_client.qdrant_service") as mock_qdrant,
            patch("app.services.document_service.minio_service") as mock_minio,
        ):
            mock_perm.return_value = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = ready_document
            mock_exec.return_value = mock_result
            mock_audit.log_event = AsyncMock()
            mock_qdrant.client = MagicMock()
            mock_minio.delete_file = AsyncMock()
            mock_minio.upload_file = AsyncMock(return_value="path/to/new/file")

            await service.replace_document(
                kb_id=ready_document.kb_id,
                doc_id=ready_document.id,
                file=mock_file,
                user=mock_user,
            )

            mock_audit.log_event.assert_called_once()
            call_kwargs = mock_audit.log_event.call_args.kwargs
            assert call_kwargs["action"] == "document_replaced"
