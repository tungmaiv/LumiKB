"""Document service for upload and management business logic."""

import os
from datetime import UTC
from io import BytesIO
from uuid import UUID

import structlog
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.minio_client import compute_checksum, minio_service
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.outbox import Outbox
from app.models.permission import PermissionLevel
from app.models.user import User
from app.schemas.document import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
)
from app.services.audit_service import audit_service
from app.services.kb_service import KBService

logger = structlog.get_logger(__name__)


class DocumentValidationError(Exception):
    """Raised when document validation fails."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class DocumentService:
    """Service for document operations.

    Handles business logic for document upload, validation,
    and coordination with MinIO storage and outbox events.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize DocumentService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session
        self._kb_service: KBService | None = None

    @property
    def kb_service(self) -> KBService:
        """Lazy initialization of KBService."""
        if self._kb_service is None:
            self._kb_service = KBService(self.session)
        return self._kb_service

    async def upload(
        self,
        kb_id: UUID,
        file: UploadFile,
        user: User,
    ) -> Document:
        """Upload a document to a Knowledge Base.

        Validates the upload, stores in MinIO, creates document record,
        and queues for processing.

        Args:
            kb_id: The Knowledge Base UUID.
            file: The uploaded file.
            user: The user uploading the document.

        Returns:
            The created Document record.

        Raises:
            DocumentValidationError: If validation fails.
        """
        # 1. Check KB exists and user has WRITE permission
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            # AC6, AC7: Return 404 to not leak KB existence
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # 2. Read file content for validation
        content = await file.read()
        file_size = len(content)

        # 3. Validate file
        await self._validate_file(file, file_size)

        # 4. Compute checksum
        file_stream = BytesIO(content)
        checksum = compute_checksum(file_stream)
        file_stream.seek(0)

        # 5. Generate document record (get ID for storage path)
        document = Document(
            kb_id=kb_id,
            name=self._generate_document_name(file.filename or "untitled"),
            original_filename=file.filename or "untitled",
            mime_type=file.content_type or "application/octet-stream",
            file_size_bytes=file_size,
            checksum=checksum,
            status=DocumentStatus.PENDING,
            uploaded_by=user.id,
        )
        self.session.add(document)
        await self.session.flush()  # Get the document ID

        # 6. Upload to MinIO
        # Path format: {doc_id}/{original_filename}
        object_path = f"{document.id}/{file.filename}"
        try:
            full_path = await minio_service.upload_file(
                kb_id=kb_id,
                object_path=object_path,
                file=file_stream,
                content_type=file.content_type or "application/octet-stream",
            )
            document.file_path = full_path
        except Exception as e:
            logger.error(
                "document_upload_minio_failed",
                kb_id=str(kb_id),
                document_id=str(document.id),
                error=str(e),
            )
            raise DocumentValidationError(
                code="UPLOAD_FAILED",
                message="Failed to upload file to storage",
                status_code=500,
                details={"error": str(e)},
            ) from e

        # 7. Create outbox event for processing (same transaction)
        outbox_event = Outbox(
            event_type="document.process",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": full_path,
                "mime_type": file.content_type,
                "checksum": checksum,
            },
        )
        self.session.add(outbox_event)

        # 8. Audit log (async, fire-and-forget)
        await audit_service.log_event(
            action="document.uploaded",
            resource_type="document",
            user_id=user.id,
            resource_id=document.id,
            details={
                "kb_id": str(kb_id),
                "filename": file.filename,
                "mime_type": file.content_type,
                "file_size_bytes": file_size,
            },
        )

        logger.info(
            "document_uploaded",
            document_id=str(document.id),
            kb_id=str(kb_id),
            filename=file.filename,
            file_size=file_size,
            user_id=str(user.id),
        )

        return document

    async def _check_kb_permission(self, kb_id: UUID, user: User) -> bool:
        """Check if KB exists and user has WRITE permission.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user to check.

        Returns:
            True if KB exists and user has WRITE permission.
        """
        # Check KB exists
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Check WRITE permission
        return await self.kb_service.check_permission(
            kb_id, user, PermissionLevel.WRITE
        )

    async def _validate_file(
        self,
        file: UploadFile,
        file_size: int,
    ) -> None:
        """Validate file type and size.

        Args:
            file: The uploaded file.
            file_size: Size in bytes.

        Raises:
            DocumentValidationError: If validation fails.
        """
        # AC5: Check empty file
        if file_size == 0:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message="Empty file not allowed",
                status_code=400,
            )

        # AC4: Check file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                status_code=413,
                details={
                    "size_bytes": file_size,
                    "max_bytes": MAX_FILE_SIZE_BYTES,
                },
            )

        # AC3: Check MIME type
        content_type = file.content_type or ""
        filename = file.filename or ""
        extension = os.path.splitext(filename)[1].lower() if filename else ""

        # Validate by MIME type or extension
        is_valid_mime = content_type in ALLOWED_MIME_TYPES
        is_valid_ext = extension in ALLOWED_EXTENSIONS

        if not is_valid_mime and not is_valid_ext:
            raise DocumentValidationError(
                code="UNSUPPORTED_FILE_TYPE",
                message="File type not allowed",
                status_code=400,
                details={
                    "mime_type": content_type,
                    "extension": extension,
                    "allowed_mime_types": list(ALLOWED_MIME_TYPES.keys()),
                    "allowed_extensions": list(ALLOWED_EXTENSIONS),
                },
            )

    def _generate_document_name(self, filename: str) -> str:
        """Generate a display name from filename.

        Removes extension and cleans up the name.

        Args:
            filename: Original filename.

        Returns:
            Clean display name.
        """
        name = os.path.splitext(filename)[0]
        # Replace underscores and hyphens with spaces
        name = name.replace("_", " ").replace("-", " ")
        # Capitalize words
        return " ".join(word.capitalize() for word in name.split())

    async def get_status(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Get document status for polling.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting status.

        Returns:
            The Document record with status fields.

        Raises:
            DocumentValidationError: If document not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        return document

    async def retry(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Retry processing a failed document.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting retry.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not in FAILED status.
        """
        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Check document is in FAILED status
        if document.status != DocumentStatus.FAILED:
            raise DocumentValidationError(
                code="INVALID_STATUS",
                message="Only FAILED documents can be retried",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Reset document for retry
        document.status = DocumentStatus.PENDING
        document.retry_count = 0
        document.last_error = None
        document.processing_started_at = None
        document.processing_completed_at = None

        # Create outbox event for processing
        outbox_event = Outbox(
            event_type="document.process",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": document.file_path,
                "mime_type": document.mime_type,
                "checksum": document.checksum,
                "is_retry": True,
            },
        )
        self.session.add(outbox_event)

        # Audit log
        await audit_service.log_event(
            action="document.retry",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "previous_error": document.last_error,
            },
        )

        logger.info(
            "document_retry_initiated",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return document

    async def _check_kb_read_permission(self, kb_id: UUID, user: User) -> bool:
        """Check if KB exists and user has READ permission.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user to check.

        Returns:
            True if KB exists and user has READ permission.
        """
        # Check KB exists
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Check READ permission
        return await self.kb_service.check_permission(kb_id, user, PermissionLevel.READ)

    async def list_documents(
        self,
        kb_id: UUID,
        user: User,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        """List documents in a Knowledge Base with pagination and sorting.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user requesting the list.
            page: Page number (1-indexed).
            limit: Documents per page (max 100).
            sort_by: Field to sort by (name, created_at, file_size_bytes, status).
            sort_order: Sort direction (asc, desc).

        Returns:
            Tuple of (list of document dicts with uploader info, total count).

        Raises:
            DocumentValidationError: If KB not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # Validate and clamp limit
        limit = min(max(1, limit), 100)
        page = max(1, page)
        offset = (page - 1) * limit

        # Build base query - exclude deleted documents
        base_query = select(Document).where(
            Document.kb_id == kb_id,
            Document.deleted_at.is_(None),
        )

        # Get total count
        count_query = select(func.count(Document.id)).where(
            Document.kb_id == kb_id,
            Document.deleted_at.is_(None),
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Document, sort_by, Document.created_at)
        sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()

        # Apply pagination and execute
        query = base_query.order_by(sort_column).offset(offset).limit(limit)
        result = await self.session.execute(query)
        documents = result.scalars().all()

        # Build result with uploader info
        document_list = []
        for doc in documents:
            # Fetch uploader email if uploaded_by is set
            uploader_email = None
            if doc.uploaded_by:
                uploader_result = await self.session.execute(
                    select(User.email).where(User.id == doc.uploaded_by)
                )
                uploader_email = uploader_result.scalar_one_or_none()

            document_list.append(
                {
                    "id": doc.id,
                    "name": doc.name,
                    "original_filename": doc.original_filename,
                    "mime_type": doc.mime_type,
                    "file_size_bytes": doc.file_size_bytes,
                    "status": doc.status,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                    "uploaded_by": doc.uploaded_by,
                    "uploader_email": uploader_email,
                }
            )

        return document_list, total

    async def delete(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> None:
        """Delete (soft) a document from a Knowledge Base.

        Sets document status to ARCHIVED, sets deleted_at timestamp,
        and creates an outbox event for cleanup of vectors and files.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting deletion.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is in PROCESSING status.
        """
        from datetime import datetime

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Check document is not in PROCESSING status (AC6)
        if document.status == DocumentStatus.PROCESSING:
            raise DocumentValidationError(
                code="PROCESSING_IN_PROGRESS",
                message="Cannot delete while processing. Please wait.",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Check document is not already ARCHIVED
        if document.status == DocumentStatus.ARCHIVED:
            raise DocumentValidationError(
                code="ALREADY_DELETED",
                message="Document has already been deleted",
                status_code=400,
            )

        # Soft delete: Set status to ARCHIVED and deleted_at timestamp
        document.status = DocumentStatus.ARCHIVED
        document.deleted_at = datetime.now(UTC)

        # Create outbox event for cleanup (AC2, AC3)
        outbox_event = Outbox(
            event_type="document.delete",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": document.file_path,
            },
        )
        self.session.add(outbox_event)

        # Audit log (AC2) - fire-and-forget
        await audit_service.log_event(
            action="document.deleted",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": document.name,
            },
        )

        logger.info(
            "document_deleted",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

    async def get_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> dict:
        """Get full document details with uploader info.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting the document.

        Returns:
            Document dict with all fields and uploader email.

        Raises:
            DocumentValidationError: If document not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Fetch uploader email if uploaded_by is set
        uploader_email = None
        if document.uploaded_by:
            uploader_result = await self.session.execute(
                select(User.email).where(User.id == document.uploaded_by)
            )
            uploader_email = uploader_result.scalar_one_or_none()

        return {
            "id": document.id,
            "kb_id": document.kb_id,
            "name": document.name,
            "original_filename": document.original_filename,
            "mime_type": document.mime_type,
            "file_size_bytes": document.file_size_bytes,
            "file_path": document.file_path,
            "checksum": document.checksum,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "processing_started_at": document.processing_started_at,
            "processing_completed_at": document.processing_completed_at,
            "last_error": document.last_error,
            "retry_count": document.retry_count,
            "uploaded_by": document.uploaded_by,
            "uploader_email": uploader_email,
            "version_number": document.version_number,
            "version_history": document.version_history,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }

    async def check_duplicate(
        self,
        kb_id: UUID,
        filename: str,
        user: User,
    ) -> dict:
        """Check if a document with the same filename exists in the KB.

        Args:
            kb_id: The Knowledge Base UUID.
            filename: The filename to check.
            user: The user checking.

        Returns:
            Dict with exists=True/False and document info if found.

        Raises:
            DocumentValidationError: If KB not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # Search for existing document with same filename
        result = await self.session.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.original_filename == filename,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            return {"exists": False}

        return {
            "exists": True,
            "document_id": document.id,
            "uploaded_at": document.created_at,
            "file_size": document.file_size_bytes,
        }

    async def replace_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        file: UploadFile,
        user: User,
    ) -> Document:
        """Replace an existing document with a new file version.

        Archives the current version metadata, uploads new file,
        and queues for reprocessing with atomic vector switch.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID to replace.
            file: The new file.
            user: The user replacing the document.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or MIME type mismatch.
        """
        from datetime import datetime

        # 1. Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # 2. Get existing document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # 3. Read and validate new file
        content = await file.read()
        file_size = len(content)

        # Check empty file
        if file_size == 0:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message="Empty file not allowed",
                status_code=400,
            )

        # Check file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                status_code=413,
                details={
                    "size_bytes": file_size,
                    "max_bytes": MAX_FILE_SIZE_BYTES,
                },
            )

        # 4. Check MIME type matches original (AC6 from story)
        new_content_type = file.content_type or "application/octet-stream"
        if new_content_type != document.mime_type:
            raise DocumentValidationError(
                code="MIME_TYPE_MISMATCH",
                message="File type must match original document",
                status_code=400,
                details={
                    "original_mime_type": document.mime_type,
                    "new_mime_type": new_content_type,
                },
            )

        # 5. Compute new checksum
        file_stream = BytesIO(content)
        new_checksum = compute_checksum(file_stream)
        file_stream.seek(0)

        # 6. Archive current version metadata to version_history (AC7)
        from app.schemas.document import VersionHistoryEntry

        current_version_entry = VersionHistoryEntry(
            version_number=document.version_number,
            file_size=document.file_size_bytes,
            checksum=document.checksum,
            replaced_at=datetime.now(UTC),
            replaced_by=user.id,
        )

        # Append to existing version history
        version_history = list(document.version_history or [])
        version_history.append(current_version_entry.model_dump(mode="json"))

        # 7. Upload new file to MinIO (overwrite same path)
        object_path = f"{document.id}/{document.original_filename}"
        try:
            full_path = await minio_service.upload_file(
                kb_id=kb_id,
                object_path=object_path,
                file=file_stream,
                content_type=new_content_type,
            )
        except Exception as e:
            logger.error(
                "document_replace_minio_failed",
                kb_id=str(kb_id),
                document_id=str(doc_id),
                error=str(e),
            )
            raise DocumentValidationError(
                code="UPLOAD_FAILED",
                message="Failed to upload replacement file to storage",
                status_code=500,
                details={"error": str(e)},
            ) from e

        # 8. Update document metadata
        old_version = document.version_number
        old_checksum = document.checksum
        old_size = document.file_size_bytes

        document.file_size_bytes = file_size
        document.checksum = new_checksum
        document.version_number = old_version + 1
        document.version_history = version_history
        document.status = DocumentStatus.PENDING
        document.last_error = None
        document.processing_started_at = None
        document.processing_completed_at = None

        # 9. Create outbox event for reprocessing with replacement flag (AC2)
        outbox_event = Outbox(
            event_type="document.reprocess",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": full_path,
                "mime_type": document.mime_type,
                "checksum": new_checksum,
                "reason": "replacement",
                "is_replacement": True,
            },
        )
        self.session.add(outbox_event)

        # 10. Audit log with action="document.replaced" (AC2)
        await audit_service.log_event(
            action="document.replaced",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "previous_version": old_version,
                "new_version": document.version_number,
                "previous_checksum": old_checksum,
                "new_checksum": new_checksum,
                "previous_size": old_size,
                "new_size": file_size,
            },
        )

        logger.info(
            "document_replaced",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            old_version=old_version,
            new_version=document.version_number,
            user_id=str(user.id),
        )

        return document
