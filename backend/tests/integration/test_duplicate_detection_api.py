"""Integration tests for duplicate detection API (Story 6-5).

Tests cover all 5 Acceptance Criteria:
- AC-6.5.1: Case-insensitive duplicate detection
- AC-6.5.2: 409 response for completed/archived duplicates
- AC-6.5.3: Auto-clear failed duplicates
- AC-6.5.4: Pending/processing duplicates blocked
- AC-6.5.5: Different KB allows same name

ATDD Checklist Reference: docs/sprint-artifacts/atdd-checklist-epic-6.md
"""

import io
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def duplicate_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with documents for duplicate detection testing.

    Returns:
        dict: {
            "kb_id": str,
            "completed_doc_name": str,    # Name of completed document
            "completed_doc_id": str,
            "archived_doc_name": str,     # Name of archived document
            "archived_doc_id": str,
            "pending_doc_name": str,      # Name of pending document
            "pending_doc_id": str,
            "processing_doc_name": str,   # Name of processing document
            "processing_doc_id": str,
            "failed_doc_name": str,       # Name of failed document
            "failed_doc_id": str,
            "owner_id": str,
        }
    """
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Duplicate Detection Test KB",
        description="KB for duplicate detection testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    docs = {}

    # Completed document
    completed_doc = Document(
        kb_id=kb.id,
        name="Completed Report.pdf",
        original_filename="completed_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/completed_report.pdf",
        checksum="a" * 64,
        status=DocumentStatus.READY,
        chunk_count=5,
        uploaded_by=test_user.id,
    )
    db_session.add(completed_doc)
    docs["completed"] = completed_doc

    # Archived document
    archived_doc = Document(
        kb_id=kb.id,
        name="Archived Report.pdf",
        original_filename="archived_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/archived_report.pdf",
        checksum="b" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    # Pending document
    pending_doc = Document(
        kb_id=kb.id,
        name="Pending Report.pdf",
        original_filename="pending_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/pending_report.pdf",
        checksum="c" * 64,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(pending_doc)
    docs["pending"] = pending_doc

    # Processing document
    processing_doc = Document(
        kb_id=kb.id,
        name="Processing Report.pdf",
        original_filename="processing_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/processing_report.pdf",
        checksum="d" * 64,
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(processing_doc)
    docs["processing"] = processing_doc

    # Failed document
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Report.pdf",
        original_filename="failed_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/failed_report.pdf",
        checksum="e" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Processing failed",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    await db_session.commit()

    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "completed_doc_name": docs["completed"].name,
        "completed_doc_id": str(docs["completed"].id),
        "archived_doc_name": docs["archived"].name,
        "archived_doc_id": str(docs["archived"].id),
        "pending_doc_name": docs["pending"].name,
        "pending_doc_id": str(docs["pending"].id),
        "processing_doc_name": docs["processing"].name,
        "processing_doc_id": str(docs["processing"].id),
        "failed_doc_name": docs["failed"].name,
        "failed_doc_id": str(docs["failed"].id),
        "owner_id": str(test_user.id),
    }


@pytest.fixture
async def second_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a second KB for cross-KB tests.

    Returns:
        dict: {"kb_id": str}
    """
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Second Test KB",
        description="Second KB for duplicate testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    await db_session.commit()
    await db_session.refresh(kb)

    return {"kb_id": str(kb.id)}


def create_test_file(filename: str, content: bytes = b"Test content") -> tuple:
    """Create a test file for upload."""
    return (filename, io.BytesIO(content), "application/pdf")


# =============================================================================
# AC-6.5.1: Case-Insensitive Duplicate Detection Tests
# =============================================================================


class TestCaseInsensitiveDuplicateDetection:
    """AC-6.5.1: Case-insensitive duplicate detection."""

    @pytest.mark.asyncio
    async def test_duplicate_detected_same_case(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given existing 'Report.pdf', When upload 'Report.pdf', Then duplicate detected."""
        kb_id = duplicate_test_kb["kb_id"]
        existing_name = duplicate_test_kb["completed_doc_name"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(existing_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_duplicate_detected_different_case(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given existing 'Completed Report.pdf', When upload 'COMPLETED REPORT.PDF', Then duplicate detected."""
        kb_id = duplicate_test_kb["kb_id"]
        existing_name = duplicate_test_kb["completed_doc_name"]
        uppercase_name = existing_name.upper()

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(uppercase_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_duplicate_detected_mixed_case(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given existing 'Completed Report.pdf', When upload 'cOmPlEtEd rEpOrT.PDF', Then duplicate detected."""
        kb_id = duplicate_test_kb["kb_id"]
        # Create mixed case version
        mixed_case_name = "cOmPlEtEd rEpOrT.PdF"

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(mixed_case_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409


# =============================================================================
# AC-6.5.2: 409 Response for Completed/Archived Duplicates
# =============================================================================


class TestCompletedArchivedDuplicates:
    """AC-6.5.2: 409 response for completed/archived duplicates."""

    @pytest.mark.asyncio
    async def test_completed_duplicate_returns_409_with_details(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given completed duplicate, When upload, Then returns 409 with document info."""
        kb_id = duplicate_test_kb["kb_id"]
        existing_name = duplicate_test_kb["completed_doc_name"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(existing_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        # Check for duplicate-related info in response
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            assert "existing_document_id" in detail or "error" in detail

    @pytest.mark.asyncio
    async def test_archived_duplicate_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given archived duplicate, When upload, Then returns 409."""
        kb_id = duplicate_test_kb["kb_id"]
        existing_name = duplicate_test_kb["archived_doc_name"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(existing_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409


# =============================================================================
# AC-6.5.3: Auto-Clear Failed Duplicates
# =============================================================================


class TestAutoClearFailedDuplicates:
    """AC-6.5.3: Auto-clear failed duplicates on upload."""

    @pytest.mark.asyncio
    async def test_failed_duplicate_auto_cleared_and_upload_succeeds(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given failed duplicate, When upload same name, Then old doc cleared and upload succeeds."""
        kb_id = duplicate_test_kb["kb_id"]
        failed_doc_name = duplicate_test_kb["failed_doc_name"]
        failed_doc_id = duplicate_test_kb["failed_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(failed_doc_name)},
            cookies=test_user_data["cookies"],
        )

        # Should succeed (201) or indicate auto-clear with 200/201
        assert response.status_code in (200, 201, 202)

        # Verify old failed document was cleared
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(failed_doc_id))
        )
        old_doc = result.scalar_one_or_none()
        assert old_doc is None, "Failed document should be auto-cleared"

    @pytest.mark.asyncio
    async def test_auto_clear_creates_audit_log(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given failed duplicate auto-cleared, When audit log queried, Then contains entry."""
        kb_id = duplicate_test_kb["kb_id"]
        failed_doc_name = duplicate_test_kb["failed_doc_name"]
        failed_doc_id = duplicate_test_kb["failed_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(failed_doc_name)},
            cookies=test_user_data["cookies"],
        )
        assert response.status_code in (200, 201, 202)

        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == failed_doc_id,
            )
        )
        audit_entries = result.scalars().all()

        # Should have auto-clear audit entry
        auto_clear_entries = [
            e
            for e in audit_entries
            if "auto" in e.action.lower() or "clear" in e.action.lower()
        ]
        assert len(auto_clear_entries) >= 1, "Should create audit log for auto-clear"


# =============================================================================
# AC-6.5.4: Pending/Processing Duplicates Blocked
# =============================================================================


class TestPendingProcessingDuplicates:
    """AC-6.5.4: Pending/processing duplicates blocked with 409."""

    @pytest.mark.asyncio
    async def test_pending_duplicate_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given pending document, When upload same name, Then returns 409."""
        kb_id = duplicate_test_kb["kb_id"]
        pending_doc_name = duplicate_test_kb["pending_doc_name"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(pending_doc_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        # Should indicate document is being processed
        detail = data.get("detail", "")
        if isinstance(detail, dict):
            assert (
                "processing" in str(detail).lower()
                or "pending" in str(detail).lower()
                or "existing" in str(detail).lower()
            )

    @pytest.mark.asyncio
    async def test_processing_duplicate_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given processing document, When upload same name, Then returns 409."""
        kb_id = duplicate_test_kb["kb_id"]
        processing_doc_name = duplicate_test_kb["processing_doc_name"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(processing_doc_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409


# =============================================================================
# AC-6.5.5: Different KB Allows Same Name
# =============================================================================


class TestDifferentKBAllowsSameName:
    """AC-6.5.5: Different KB allows same filename."""

    @pytest.mark.asyncio
    async def test_same_name_different_kb_succeeds(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
        second_kb: dict,
    ) -> None:
        """Given 'Report.pdf' in KB-A, When upload 'Report.pdf' to KB-B, Then succeeds."""
        kb_a_id = duplicate_test_kb["kb_id"]
        kb_b_id = second_kb["kb_id"]
        existing_name = duplicate_test_kb["completed_doc_name"]

        # Verify it exists in KB-A (should fail)
        response_a = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_a_id}/documents/",
            files={"file": create_test_file(existing_name)},
            cookies=test_user_data["cookies"],
        )
        assert response_a.status_code == 409

        # Upload to KB-B should succeed
        response_b = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_b_id}/documents/",
            files={"file": create_test_file(existing_name)},
            cookies=test_user_data["cookies"],
        )
        assert response_b.status_code in (200, 201, 202)

    @pytest.mark.asyncio
    async def test_unique_name_upload_succeeds(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        duplicate_test_kb: dict,
    ) -> None:
        """Given unique filename, When upload, Then succeeds."""
        kb_id = duplicate_test_kb["kb_id"]
        unique_name = f"Unique Document {uuid.uuid4()}.pdf"

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/",
            files={"file": create_test_file(unique_name)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code in (200, 201, 202)
