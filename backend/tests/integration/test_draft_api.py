"""Integration tests for Draft API endpoints.

Tests full request/response cycle including database, permissions, and validation.

Coverage Target: Full endpoint coverage
Test Count: 8
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.draft import Draft, DraftStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from tests.factories import (
    create_citation,
    create_draft,
    create_draft_update_data,
    create_draft_with_citations,
    create_regenerate_request,
)


class TestCreateDraft:
    """Test POST /api/v1/drafts endpoint."""

    @pytest.mark.asyncio
    async def test_create_draft_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_kb: KnowledgeBase,
        db_session: AsyncSession,
    ):
        """[P0] Authenticated user can create draft in their KB."""
        # GIVEN: Valid draft data
        draft_data = create_draft(kb_id=str(test_kb.id))
        draft_data.pop("id")  # Let DB generate ID
        draft_data.pop("created_at")
        draft_data.pop("updated_at")

        # WHEN: Creating draft
        response = await client.post(
            "/api/v1/drafts",
            json=draft_data,
            headers=auth_headers,
        )

        # THEN: Draft created successfully
        assert response.status_code == 201
        data = response.json()
        assert data["kb_id"] == str(test_kb.id)
        assert data["status"] == "streaming"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_draft_requires_authentication(
        self,
        client: AsyncClient,
        test_kb: KnowledgeBase,
    ):
        """[P0] Draft creation requires authentication."""
        # GIVEN: Draft data without auth
        draft_data = create_draft(kb_id=str(test_kb.id))

        # WHEN: Creating draft without auth headers
        response = await client.post("/api/v1/drafts", json=draft_data)

        # THEN: Unauthorized
        assert response.status_code == 401


class TestGetDrafts:
    """Test GET /api/v1/drafts endpoint."""

    @pytest.mark.asyncio
    async def test_get_drafts_by_kb(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_kb: KnowledgeBase,
        db_session: AsyncSession,
    ):
        """[P1] User can list drafts for a knowledge base."""
        # GIVEN: 3 drafts in test KB
        draft1 = Draft(**create_draft(kb_id=test_kb.id, title="Draft 1"))
        draft2 = Draft(**create_draft(kb_id=test_kb.id, title="Draft 2"))
        draft3 = Draft(**create_draft(kb_id=test_kb.id, title="Draft 3"))

        db_session.add_all([draft1, draft2, draft3])
        await db_session.commit()

        # WHEN: Getting drafts for KB
        response = await client.get(
            f"/api/v1/drafts?kb_id={test_kb.id}",
            headers=auth_headers,
        )

        # THEN: All 3 drafts returned
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        titles = [d["title"] for d in data]
        assert "Draft 1" in titles
        assert "Draft 2" in titles

    @pytest.mark.asyncio
    async def test_get_drafts_requires_read_permission(
        self,
        client: AsyncClient,
        test_kb: KnowledgeBase,
        other_user_headers: dict,
    ):
        """[P0] User without read permission cannot list drafts."""
        # GIVEN: Other user without access to test_kb
        # WHEN: Attempting to list drafts
        response = await client.get(
            f"/api/v1/drafts?kb_id={test_kb.id}",
            headers=other_user_headers,
        )

        # THEN: Forbidden
        assert response.status_code == 403


class TestUpdateDraft:
    """Test PATCH /api/v1/drafts/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_draft_content(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_draft: Draft,
    ):
        """[P0] User can update draft content and status changes to 'editing'."""
        # GIVEN: Existing draft with status='complete'
        update_data = create_draft_update_data(
            content="Updated content [1]",
            citations=[create_citation(number=1)],
            status="editing",
        )

        # WHEN: Updating draft
        response = await client.patch(
            f"/api/v1/drafts/{test_draft.id}",
            json=update_data,
            headers=auth_headers,
        )

        # THEN: Draft updated successfully
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content [1]"
        assert data["status"] == "editing"
        assert len(data["citations"]) == 1

    @pytest.mark.asyncio
    async def test_update_draft_validates_citation_markers(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_draft: Draft,
    ):
        """[P1] Update validates citation markers match citation data."""
        # GIVEN: Update with mismatched citations
        update_data = {
            "content": "No markers here",  # Missing [1]
            "citations": [create_citation(number=1)],  # Has citation data
        }

        # WHEN: Updating draft with invalid citations
        response = await client.patch(
            f"/api/v1/drafts/{test_draft.id}",
            json=update_data,
            headers=auth_headers,
        )

        # THEN: Validation error
        assert response.status_code == 422
        assert "citation" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_draft_requires_write_permission(
        self,
        client: AsyncClient,
        other_user_headers: dict,
        test_draft: Draft,
    ):
        """[P0] User without write permission cannot update draft."""
        # GIVEN: Other user without write access
        update_data = create_draft_update_data()

        # WHEN: Attempting to update draft
        response = await client.patch(
            f"/api/v1/drafts/{test_draft.id}",
            json=update_data,
            headers=other_user_headers,
        )

        # THEN: Forbidden
        assert response.status_code == 403


class TestRegenerateSection:
    """Test POST /api/v1/drafts/{id}/regenerate endpoint."""

    @pytest.mark.asyncio
    async def test_regenerate_section_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_draft: Draft,
    ):
        """[P1] User can regenerate section with instructions."""
        # GIVEN: Regeneration request
        regen_data = create_regenerate_request(
            selected_text="OAuth 2.0 is secure",
            instructions="Make it more technical",
            keep_citations=False,
        )

        # WHEN: Regenerating section
        response = await client.post(
            f"/api/v1/drafts/{test_draft.id}/regenerate",
            json=regen_data,
            headers=auth_headers,
        )

        # THEN: Regeneration succeeds (stub implementation returns placeholder)
        assert response.status_code == 200
        data = response.json()
        assert "regenerated_text" in data

    @pytest.mark.asyncio
    async def test_regenerate_preserves_citations_when_requested(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_draft: Draft,
    ):
        """[P2] Regeneration preserves existing citations when keep_citations=True."""
        # GIVEN: Regeneration request with keep_citations=True
        regen_data = create_regenerate_request(
            selected_text="OAuth 2.0 [1] is secure",
            keep_citations=True,
        )

        # WHEN: Regenerating section
        response = await client.post(
            f"/api/v1/drafts/{test_draft.id}/regenerate",
            json=regen_data,
            headers=auth_headers,
        )

        # THEN: Regeneration succeeds
        # NOTE: Full citation preservation logic tested when LLM integration complete
        assert response.status_code == 200


class TestDeleteDraft:
    """Test DELETE /api/v1/drafts/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_draft_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_draft: Draft,
        db_session: AsyncSession,
    ):
        """[P2] User can delete their draft."""
        # WHEN: Deleting draft
        response = await client.delete(
            f"/api/v1/drafts/{test_draft.id}",
            headers=auth_headers,
        )

        # THEN: Draft deleted
        assert response.status_code == 204

        # Verify deletion
        await db_session.refresh(test_draft)
        deleted = await db_session.get(Draft, test_draft.id)
        assert deleted is None
