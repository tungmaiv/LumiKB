"""Integration tests for Document status and retry API endpoints.

Tests cover:
- GET /knowledge-bases/{kb_id}/documents/{doc_id}/status endpoint
- POST /knowledge-bases/{kb_id}/documents/{doc_id}/retry endpoint
- Permission enforcement (READ for status, WRITE for retry)
- Status transitions and outbox event creation
"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.document import Document, DocumentStatus
from app.models.outbox import Outbox
from tests.factories import (
    create_document,
    create_kb_data,
    create_registration_data,
)

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def doc_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data."""
    return create_registration_data()


@pytest.fixture
async def registered_user(doc_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered test user."""
    response = await doc_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert response.status_code == 201
    return {**test_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_client(
    doc_client: AsyncClient, registered_user: dict
) -> AsyncClient:
    """Client with authenticated session."""
    response = await doc_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 204
    return doc_client


@pytest.fixture
async def test_kb(authenticated_client: AsyncClient) -> dict:
    """Create a test Knowledge Base."""
    kb_data = create_kb_data()
    response = await authenticated_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def test_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
    db_session: AsyncSession,
    registered_user: dict,
) -> Document:
    """Create a test document in the database."""
    kb_id = uuid.UUID(test_kb["id"])
    user_id = uuid.UUID(registered_user["user"]["id"])
    doc = await create_document(
        db_session,
        kb_id=kb_id,
        uploaded_by=user_id,
        status=DocumentStatus.PENDING,
    )
    await db_session.commit()
    return doc


@pytest.fixture
async def processing_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
    db_session: AsyncSession,
    registered_user: dict,
) -> Document:
    """Create a document in PROCESSING status."""
    kb_id = uuid.UUID(test_kb["id"])
    user_id = uuid.UUID(registered_user["user"]["id"])
    doc = await create_document(
        db_session,
        kb_id=kb_id,
        uploaded_by=user_id,
        status=DocumentStatus.PROCESSING,
        processing_started_at=datetime.now(UTC),
    )
    await db_session.commit()
    return doc


@pytest.fixture
async def ready_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
    db_session: AsyncSession,
    registered_user: dict,
) -> Document:
    """Create a document in READY status."""
    kb_id = uuid.UUID(test_kb["id"])
    user_id = uuid.UUID(registered_user["user"]["id"])
    doc = await create_document(
        db_session,
        kb_id=kb_id,
        uploaded_by=user_id,
        status=DocumentStatus.READY,
        chunk_count=47,
        processing_started_at=datetime.now(UTC),
        processing_completed_at=datetime.now(UTC),
    )
    await db_session.commit()
    return doc


@pytest.fixture
async def failed_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
    db_session: AsyncSession,
    registered_user: dict,
) -> Document:
    """Create a document in FAILED status."""
    kb_id = uuid.UUID(test_kb["id"])
    user_id = uuid.UUID(registered_user["user"]["id"])
    doc = await create_document(
        db_session,
        kb_id=kb_id,
        uploaded_by=user_id,
        status=DocumentStatus.FAILED,
        last_error="Parse error: Invalid PDF format",
        retry_count=2,
        processing_started_at=datetime.now(UTC),
    )
    await db_session.commit()
    return doc


@pytest.fixture
async def second_user(doc_client: AsyncClient) -> dict:
    """Create a second registered user for permission tests."""
    user_data = create_registration_data()
    response = await doc_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


# =============================================================================
# GET /status - Success Cases
# =============================================================================


class TestGetDocumentStatusSuccess:
    """Tests for successful document status retrieval."""

    async def test_get_pending_document_status(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: Document,
    ) -> None:
        """Test getting status of PENDING document."""
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{test_document.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["chunk_count"] == 0
        assert data["processing_started_at"] is None
        assert data["processing_completed_at"] is None
        assert data["last_error"] is None
        assert data["retry_count"] == 0

    async def test_get_processing_document_status(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        processing_document: Document,
    ) -> None:
        """Test getting status of PROCESSING document."""
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{processing_document.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PROCESSING"
        assert data["processing_started_at"] is not None
        assert data["processing_completed_at"] is None

    async def test_get_ready_document_status(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        ready_document: Document,
    ) -> None:
        """Test getting status of READY document with chunk count."""
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{ready_document.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "READY"
        assert data["chunk_count"] == 47
        assert data["processing_started_at"] is not None
        assert data["processing_completed_at"] is not None
        assert data["last_error"] is None

    async def test_get_failed_document_status(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        failed_document: Document,
    ) -> None:
        """Test getting status of FAILED document with error message."""
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{failed_document.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"
        assert data["last_error"] == "Parse error: Invalid PDF format"
        assert data["retry_count"] == 2


# =============================================================================
# GET /status - Error Cases
# =============================================================================


class TestGetDocumentStatusErrors:
    """Tests for document status error handling."""

    async def test_status_returns_404_for_non_existent_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ) -> None:
        """Test 404 for non-existent document."""
        fake_doc_id = uuid.uuid4()
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{fake_doc_id}/status"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_status_returns_404_for_non_existent_kb(
        self,
        authenticated_client: AsyncClient,
        test_document: Document,
    ) -> None:
        """Test 404 for non-existent KB."""
        fake_kb_id = uuid.uuid4()
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{test_document.id}/status"
        )

        assert response.status_code == 404

    async def test_status_returns_401_for_unauthenticated(
        self,
        doc_client: AsyncClient,
        test_kb: dict,
        test_document: Document,
    ) -> None:
        """Test 401 for unauthenticated request."""
        # Clear cookies to simulate unauthenticated request
        # (doc_client may have cookies from fixture setup that used authenticated_client)
        doc_client.cookies.clear()

        response = await doc_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{test_document.id}/status"
        )

        assert response.status_code == 401

    async def test_status_returns_404_for_no_permission(
        self,
        doc_client: AsyncClient,
        second_user: dict,
        test_kb: dict,
        test_document: Document,
    ) -> None:
        """Test 404 when user has no permission (security through obscurity)."""
        # Login as second user
        await doc_client.post(
            "/api/v1/auth/login",
            data={
                "username": second_user["email"],
                "password": second_user["password"],
            },
        )

        response = await doc_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{test_document.id}/status"
        )

        assert response.status_code == 404


# =============================================================================
# POST /retry - Success Cases
# =============================================================================


class TestRetryDocumentSuccess:
    """Tests for successful document retry."""

    async def test_retry_failed_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        failed_document: Document,
        db_session: AsyncSession,
    ) -> None:
        """Test retrying a FAILED document returns 202."""
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{failed_document.id}/retry"
        )

        assert response.status_code == 202
        data = response.json()
        assert "retry" in data["message"].lower()

    async def test_retry_resets_document_status(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        failed_document: Document,
        test_engine,
    ) -> None:
        """Test retry resets document to PENDING status."""
        doc_id = failed_document.id

        await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{doc_id}/retry"
        )

        # Query fresh data with new session (API committed its transaction)
        fresh_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with fresh_session_factory() as session:
            result = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = result.scalar_one()

            assert doc.status == DocumentStatus.PENDING
            assert doc.retry_count == 0
            assert doc.last_error is None
            assert doc.processing_started_at is None
            assert doc.processing_completed_at is None

    async def test_retry_creates_outbox_event(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        failed_document: Document,
        test_engine,
    ) -> None:
        """Test retry creates outbox event for processing."""
        doc_id = failed_document.id

        await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{doc_id}/retry"
        )

        # Query fresh data with new session (API committed its transaction)
        fresh_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with fresh_session_factory() as session:
            # Check outbox event was created
            result = await session.execute(
                select(Outbox).where(
                    Outbox.aggregate_id == doc_id,
                    Outbox.event_type == "document.process",
                    Outbox.processed_at.is_(None),
                )
            )
            event = result.scalar_one_or_none()

            assert event is not None
            assert event.payload["is_retry"] is True
            assert event.payload["document_id"] == str(doc_id)


# =============================================================================
# POST /retry - Error Cases
# =============================================================================


class TestRetryDocumentErrors:
    """Tests for document retry error handling."""

    async def test_retry_returns_400_for_pending_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: Document,
    ) -> None:
        """Test 400 when trying to retry PENDING document."""
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{test_document.id}/retry"
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_STATUS"

    async def test_retry_returns_400_for_processing_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        processing_document: Document,
    ) -> None:
        """Test 400 when trying to retry PROCESSING document."""
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{processing_document.id}/retry"
        )

        assert response.status_code == 400

    async def test_retry_returns_400_for_ready_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        ready_document: Document,
    ) -> None:
        """Test 400 when trying to retry READY document."""
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{ready_document.id}/retry"
        )

        assert response.status_code == 400

    async def test_retry_returns_404_for_non_existent_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ) -> None:
        """Test 404 for non-existent document."""
        fake_doc_id = uuid.uuid4()
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{fake_doc_id}/retry"
        )

        assert response.status_code == 404

    async def test_retry_returns_401_for_unauthenticated(
        self,
        doc_client: AsyncClient,
        test_kb: dict,
        failed_document: Document,
    ) -> None:
        """Test 401 for unauthenticated request."""
        # Clear cookies to simulate unauthenticated request
        # (doc_client may have cookies from fixture setup that used authenticated_client)
        doc_client.cookies.clear()

        response = await doc_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{failed_document.id}/retry"
        )

        assert response.status_code == 401

    async def test_retry_returns_404_for_no_write_permission(
        self,
        doc_client: AsyncClient,
        authenticated_client: AsyncClient,
        second_user: dict,
        test_kb: dict,
        failed_document: Document,
    ) -> None:
        """Test 404 when user has no WRITE permission."""
        # Grant READ permission to second user
        await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/permissions",
            json={
                "user_id": second_user["user"]["id"],
                "permission_level": "READ",
            },
        )

        # Logout first user by logging in second user
        await doc_client.post(
            "/api/v1/auth/login",
            data={
                "username": second_user["email"],
                "password": second_user["password"],
            },
        )

        response = await doc_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{failed_document.id}/retry"
        )

        # Returns 404 for security (not 403)
        assert response.status_code == 404
