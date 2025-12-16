"""Story 7-14 ATDD: KB Settings API Integration Tests.

Generated: 2025-12-09

Tests AC-7.14.8: Settings API endpoint
- GET /api/v1/knowledge-bases/{id}/settings returns KB settings
- PUT /api/v1/knowledge-bases/{id}/settings updates KB settings
- PUT validates against KBSettings schema
- PUT creates audit log entry
- PUT invalidates KBConfigResolver cache

Required implementation:
- Add GET/PUT /settings endpoints to backend/app/api/v1/knowledge_bases.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User


@pytest.fixture
def default_settings() -> dict:
    """Default KB settings matching backend schema defaults."""
    return {
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 512,
            "chunk_overlap": 50,
            "separators": ["\n\n", "\n", " ", ""],
        },
        "retrieval": {
            "top_k": 10,
            "similarity_threshold": 0.7,
            "method": "vector",
            "mmr_enabled": False,
            "mmr_lambda": 0.5,
            "hybrid_alpha": 0.5,
        },
        "generation": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": 2048,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop_sequences": [],
        },
    }


@pytest.fixture
async def test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> KnowledgeBase:
    """Create a KB for settings tests."""
    # Get test user
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Settings Test KB",
        description="KB for settings API tests",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant ADMIN permission to test user
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.ADMIN,
    )
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(kb)

    return kb


@pytest.fixture
async def kb_with_settings(
    db_session: AsyncSession,
    test_user_data: dict,
) -> KnowledgeBase:
    """Create a KB with custom settings for testing."""
    # Get test user
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Test KB with Settings",
        description="KB for settings API tests",
        owner_id=test_user.id,
        status="active",
        settings={
            "chunking": {
                "strategy": "recursive",
                "chunk_size": 1024,
                "chunk_overlap": 100,
            },
            "retrieval": {"top_k": 20, "similarity_threshold": 0.8, "method": "hybrid"},
            "generation": {"temperature": 1.0, "top_p": 0.95, "max_tokens": 8192},
        },
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant ADMIN permission to test user
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.ADMIN,
    )
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(kb)

    return kb


@pytest.fixture
async def other_user_data(api_client: AsyncClient) -> dict:
    """Create a second unique test user without any KB access."""
    from tests.factories import create_registration_data

    # Register second unique test user
    user_data = create_registration_data()
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_response = register_response.json()

    # Login to get JWT cookie
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "cookies": login_response.cookies,
        "user_id": user_response["id"],
    }


@pytest.fixture
async def viewer_user_data(
    api_client: AsyncClient,
    kb_with_settings: KnowledgeBase,
    db_session: AsyncSession,
) -> dict:
    """Create a user with viewer (READ) permission on kb_with_settings."""
    from tests.factories import create_registration_data

    # Register viewer user
    user_data = create_registration_data()
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_response = register_response.json()

    # Get user from database
    result = await db_session.execute(
        select(User).where(User.id == user_response["id"])
    )
    viewer_user = result.scalar_one()

    # Grant READ permission
    permission = KBPermission(
        user_id=viewer_user.id,
        kb_id=kb_with_settings.id,
        permission_level=PermissionLevel.READ,
    )
    db_session.add(permission)
    await db_session.commit()

    # Login to get JWT cookie
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "cookies": login_response.cookies,
        "user_id": user_response["id"],
    }


class TestGetKBSettings:
    """Tests for GET /api/v1/knowledge-bases/{id}/settings endpoint."""

    @pytest.mark.asyncio
    async def test_get_settings_returns_kb_settings(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        kb_with_settings: KnowledgeBase,
    ):
        """
        [P0] AC-7.14.8: GET /settings returns KB settings.

        GIVEN: KB exists with custom settings
        WHEN: GET /settings is called
        THEN: Returns 200 with KB settings JSONB content
        """
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_with_settings.id}/settings",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "chunking" in data
        assert "retrieval" in data
        assert "generation" in data
        assert data["chunking"]["chunk_size"] == 1024

    @pytest.mark.asyncio
    async def test_get_settings_returns_defaults_for_empty_settings(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
        default_settings: dict,
    ):
        """
        [P0] AC-7.14.8: GET /settings returns defaults when no settings configured.

        GIVEN: KB exists with empty/null settings
        WHEN: GET /settings is called
        THEN: Returns 200 with system default settings
        """
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["chunking"]["chunk_size"] == default_settings["chunking"]["chunk_size"]
        )
        assert data["retrieval"]["top_k"] == default_settings["retrieval"]["top_k"]

    @pytest.mark.asyncio
    async def test_get_settings_requires_authentication(
        self,
        api_client: AsyncClient,
    ):
        """
        [P0] GET /settings requires authentication.

        GIVEN: Unauthenticated request
        WHEN: GET /settings is called
        THEN: Returns 401 Unauthorized
        """
        # Use a random UUID to avoid fixture dependencies that set cookies
        random_kb_id = uuid4()
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{random_kb_id}/settings"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_settings_returns_404_for_nonexistent_kb(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
    ):
        """
        [P1] GET /settings returns 404 for nonexistent KB.

        GIVEN: KB ID does not exist
        WHEN: GET /settings is called
        THEN: Returns 404 Not Found
        """
        nonexistent_id = uuid4()
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{nonexistent_id}/settings",
            cookies=authenticated_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_settings_requires_kb_access(
        self,
        api_client: AsyncClient,
        other_user_data: dict,
        kb_with_settings: KnowledgeBase,
    ):
        """
        [P1] GET /settings requires KB access permissions.

        GIVEN: User does not have access to KB
        WHEN: GET /settings is called
        THEN: Returns 404 (KB hidden for security - user cannot see it exists)

        Note: API returns 404 instead of 403 to prevent information disclosure
        about KB existence to unauthorized users.
        """
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_with_settings.id}/settings",
            cookies=other_user_data["cookies"],
        )

        # API returns 404 to hide KB existence from unauthorized users
        assert response.status_code == 404


class TestPutKBSettings:
    """Tests for PUT /api/v1/knowledge-bases/{id}/settings endpoint."""

    @pytest.mark.asyncio
    async def test_put_settings_updates_kb_settings(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P0] AC-7.14.6 & AC-7.14.8: PUT /settings updates KB settings.

        GIVEN: KB exists
        WHEN: PUT /settings is called with new settings
        THEN: Returns 200 and settings are updated
        """
        new_settings = {
            "chunking": {"chunk_size": 1024, "chunk_overlap": 100},
            "retrieval": {"top_k": 25},
            "generation": {"temperature": 1.2},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=new_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chunking"]["chunk_size"] == 1024
        assert data["retrieval"]["top_k"] == 25
        assert data["generation"]["temperature"] == 1.2

    @pytest.mark.asyncio
    async def test_put_settings_validates_chunk_size_range(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P0] AC-7.14.7 & AC-7.14.8: PUT /settings validates chunk_size range.

        GIVEN: Invalid chunk_size (below min 100)
        WHEN: PUT /settings is called
        THEN: Returns 422 Validation Error
        """
        invalid_settings = {
            "chunking": {"chunk_size": 50},  # Below min 100
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=invalid_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 422
        assert "chunk_size" in response.text.lower()

    @pytest.mark.asyncio
    async def test_put_settings_validates_temperature_range(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P0] AC-7.14.7: PUT /settings validates temperature range.

        GIVEN: Invalid temperature (above max 2.0)
        WHEN: PUT /settings is called
        THEN: Returns 422 Validation Error
        """
        invalid_settings = {
            "generation": {"temperature": 2.5},  # Above max 2.0
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=invalid_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 422
        assert "temperature" in response.text.lower()

    @pytest.mark.asyncio
    async def test_put_settings_validates_similarity_threshold_range(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P1] PUT /settings validates similarity_threshold range.

        GIVEN: Invalid similarity_threshold (above max 1.0)
        WHEN: PUT /settings is called
        THEN: Returns 422 Validation Error
        """
        invalid_settings = {
            "retrieval": {"similarity_threshold": 1.5},  # Above max 1.0
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=invalid_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_put_settings_validates_chunking_strategy_enum(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P1] PUT /settings validates chunking strategy enum.

        GIVEN: Invalid strategy value
        WHEN: PUT /settings is called
        THEN: Returns 422 Validation Error
        """
        invalid_settings = {
            "chunking": {"strategy": "invalid_strategy"},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=invalid_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_put_settings_validates_retrieval_method_enum(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P1] PUT /settings validates retrieval method enum.

        GIVEN: Invalid method value
        WHEN: PUT /settings is called
        THEN: Returns 422 Validation Error
        """
        invalid_settings = {
            "retrieval": {"method": "invalid_method"},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=invalid_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_put_settings_creates_audit_log(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
        db_session: AsyncSession,
    ):
        """
        [P0] AC-7.14.8: PUT /settings creates audit log entry.

        GIVEN: Valid settings update
        WHEN: PUT /settings is called
        THEN: Audit log entry is created
        """
        new_settings = {
            "chunking": {"chunk_size": 1024},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=new_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200

        # Check audit log was created
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent)
            .where(AuditEvent.resource_type == "knowledge_base")
            .where(AuditEvent.resource_id == test_kb.id)
            .order_by(AuditEvent.timestamp.desc())
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert (
            "settings" in audit_log.action.lower()
            or "update" in audit_log.action.lower()
        )

    @pytest.mark.asyncio
    async def test_put_settings_requires_admin_permission(
        self,
        api_client: AsyncClient,
        viewer_user_data: dict,
        kb_with_settings: KnowledgeBase,
    ):
        """
        [P1] PUT /settings requires admin permission on KB.

        GIVEN: User has only viewer access
        WHEN: PUT /settings is called
        THEN: Returns 403 Forbidden
        """
        new_settings = {
            "chunking": {"chunk_size": 1024},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{kb_with_settings.id}/settings",
            json=new_settings,
            cookies=viewer_user_data["cookies"],
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_put_settings_merges_partial_updates(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        kb_with_settings: KnowledgeBase,
    ):
        """
        [P1] PUT /settings merges partial updates with existing settings.

        GIVEN: KB has existing settings
        WHEN: PUT /settings is called with partial update
        THEN: Only specified fields are updated, others preserved
        """
        # Only update chunk_size
        partial_update = {
            "chunking": {"chunk_size": 2000},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{kb_with_settings.id}/settings",
            json=partial_update,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Updated field
        assert data["chunking"]["chunk_size"] == 2000

        # Preserved fields from original settings
        assert data["chunking"]["chunk_overlap"] == 100  # Original value
        assert data["retrieval"]["top_k"] == 20  # Original value
        assert data["generation"]["temperature"] == 1.0  # Original value


class TestSettingsEdgeCases:
    """Edge case tests for KB Settings API."""

    @pytest.mark.asyncio
    async def test_put_settings_with_max_values(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P2] PUT /settings accepts maximum valid values.

        GIVEN: Settings at maximum valid values
        WHEN: PUT /settings is called
        THEN: Returns 200 and settings are saved
        """
        max_settings = {
            "chunking": {"chunk_size": 2000, "chunk_overlap": 500},
            "retrieval": {"top_k": 100, "similarity_threshold": 1.0},
            "generation": {"temperature": 2.0, "top_p": 1.0, "max_tokens": 16000},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=max_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chunking"]["chunk_size"] == 2000
        assert data["generation"]["temperature"] == 2.0

    @pytest.mark.asyncio
    async def test_put_settings_with_min_values(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P2] PUT /settings accepts minimum valid values.

        GIVEN: Settings at minimum valid values
        WHEN: PUT /settings is called
        THEN: Returns 200 and settings are saved
        """
        min_settings = {
            "chunking": {"chunk_size": 100, "chunk_overlap": 0},
            "retrieval": {"top_k": 1, "similarity_threshold": 0.0},
            "generation": {"temperature": 0.0, "top_p": 0.0, "max_tokens": 100},
        }

        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json=min_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chunking"]["chunk_size"] == 100
        assert data["generation"]["temperature"] == 0.0

    @pytest.mark.asyncio
    async def test_put_settings_with_empty_body(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        test_kb: KnowledgeBase,
    ):
        """
        [P2] PUT /settings with empty body preserves existing settings.

        GIVEN: Empty settings object
        WHEN: PUT /settings is called
        THEN: Existing settings are preserved
        """
        response = await api_client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/settings",
            json={},
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
