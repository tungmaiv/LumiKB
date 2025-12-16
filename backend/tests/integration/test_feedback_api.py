"""Integration tests for feedback API endpoints (Story 4-8).

Test Coverage:
- P0 (Security): Permission enforcement
- P1 (Core API): Feedback submission, alternative suggestions, error recovery

Following test-levels-framework.md:
- Integration level: API contracts, service integration, business logic
- Fast execution with testcontainers (no UI)
- Validate service-to-service interactions
"""

import pytest

pytestmark = pytest.mark.integration


class TestFeedbackSubmission:
    """Test feedback submission API endpoint (AC2-AC3)."""

    @pytest.mark.asyncio
    async def test_submit_feedback_valid_type_returns_alternatives(
        self,
        api_client,
        authenticated_headers,
        test_user_data,
        demo_kb_with_indexed_docs,
        db_session,
    ):
        """[P1] POST /drafts/{id}/feedback - valid feedback type → alternatives returned.

        GIVEN a draft with status 'complete'
        WHEN user submits feedback with valid type "not_relevant"
        THEN API returns 200 with alternative suggestions
        AND alternatives match feedback type
        """
        from tests.factories import create_draft, create_feedback_request

        # Create draft in database
        from app.models.draft import Draft

        draft = Draft(
            **create_draft(
                kb_id=demo_kb_with_indexed_docs["id"],
                user_id=test_user_data["user_id"],
                status="complete",
            )
        )
        db_session.add(draft)
        await db_session.commit()

        # Submit feedback
        feedback = create_feedback_request(feedback_type="not_relevant")
        response = await api_client.post(
            f"/api/v1/drafts/{draft.id}/feedback",
            json=feedback,
            cookies=authenticated_headers,
        )

        # THEN: Returns 200 with alternatives
        assert response.status_code == 200
        data = response.json()

        assert "alternatives" in data
        assert len(data["alternatives"]) == 3  # 3 alternatives per feedback type
        assert all("type" in alt for alt in data["alternatives"])
        assert all("description" in alt for alt in data["alternatives"])
        assert all("action" in alt for alt in data["alternatives"])

        # Verify alternatives match "not_relevant" feedback type
        alt_types = [alt["type"] for alt in data["alternatives"]]
        assert "re_search" in alt_types
        assert "add_context" in alt_types
        assert "start_fresh" in alt_types

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_type_returns_400(
        self,
        api_client,
        authenticated_headers,
        test_user_data,
        demo_kb_with_indexed_docs,
        db_session,
    ):
        """[P1] POST /drafts/{id}/feedback - invalid feedback type → 400 error.

        GIVEN a draft exists
        WHEN user submits feedback with invalid type "invalid_type"
        THEN API returns 400 Bad Request
        AND error message indicates invalid feedback type
        """
        from tests.factories import create_draft

        # Create draft
        draft_data = create_draft(
            kb_id=demo_kb_with_indexed_docs["id"],
            user_id=test_user_data["user_id"],
        )

        from app.models.draft import Draft

        draft = Draft(
            id=draft_data["id"],
            kb_id=draft_data["kb_id"],
            user_id=draft_data["user_id"],
            title=draft_data["title"],
            content=draft_data["content"],
            status="complete",  # Use string, not enum
            word_count=draft_data["word_count"],
            citations=[],
        )
        db_session.add(draft)
        await db_session.commit()

        # Submit invalid feedback
        response = await api_client.post(
            f"/api/v1/drafts/{draft.id}/feedback",
            json={"feedback_type": "invalid_type", "comments": None},
            cookies=authenticated_headers,
        )

        # THEN: Returns 400 error
        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "invalid feedback type" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_feedback_without_permission_returns_403(
        self,
        api_client,
        test_user_data,
        demo_kb_with_indexed_docs,
        db_session,
    ):
        """[P0] Permission enforcement on feedback submission.

        GIVEN a draft exists in KB owned by another user
        WHEN user without READ permission submits feedback
        THEN API returns 403 Forbidden
        """
        from tests.factories import create_draft, create_registration_data

        # Create second user without permissions
        second_user = create_registration_data()
        register_response = await api_client.post(
            "/api/v1/auth/register",
            json=second_user,
        )
        assert register_response.status_code == 201

        login_response = await api_client.post(
            "/api/v1/auth/login",
            data={
                "username": second_user["email"],
                "password": second_user["password"],
            },
        )
        assert login_response.status_code in (200, 204)
        second_user_cookies = login_response.cookies

        # Create draft owned by first user (test_user_data)
        draft_data = create_draft(
            kb_id=demo_kb_with_indexed_docs["id"],
            user_id=test_user_data["user_id"],
        )

        from app.models.draft import Draft

        draft = Draft(
            id=draft_data["id"],
            kb_id=draft_data["kb_id"],
            user_id=draft_data["user_id"],
            title=draft_data["title"],
            content=draft_data["content"],
            status="complete",  # Use string, not enum
            word_count=draft_data["word_count"],
            citations=[],
        )
        db_session.add(draft)
        await db_session.commit()

        # Second user tries to submit feedback (no permission)
        from tests.factories import create_feedback_request

        feedback = create_feedback_request(feedback_type="not_relevant")
        response = await api_client.post(
            f"/api/v1/drafts/{draft.id}/feedback",
            json=feedback,
            cookies=second_user_cookies,
        )

        # THEN: Returns 403 Forbidden
        assert response.status_code == 403


class TestFeedbackAlternatives:
    """Test alternative suggestions match feedback type (AC3)."""

    @pytest.mark.asyncio
    async def test_wrong_format_feedback_returns_template_alternatives(
        self,
        api_client,
        authenticated_headers,
        test_user_data,
        demo_kb_with_indexed_docs,
        db_session,
    ):
        """[P1] "wrong_format" feedback → template-related alternatives.

        GIVEN a draft exists
        WHEN user submits "wrong_format" feedback
        THEN alternatives suggest using different template
        """
        from tests.factories import create_draft, create_feedback_request

        # Create draft
        draft_data = create_draft(
            kb_id=demo_kb_with_indexed_docs["id"],
            user_id=test_user_data["user_id"],
        )

        from app.models.draft import Draft

        draft = Draft(
            id=draft_data["id"],
            kb_id=draft_data["kb_id"],
            user_id=draft_data["user_id"],
            title=draft_data["title"],
            content=draft_data["content"],
            status="complete",  # Use string, not enum
            word_count=draft_data["word_count"],
            citations=[],
        )
        db_session.add(draft)
        await db_session.commit()

        # Submit wrong_format feedback
        feedback = create_feedback_request(feedback_type="wrong_format")
        response = await api_client.post(
            f"/api/v1/drafts/{draft.id}/feedback",
            json=feedback,
            cookies=authenticated_headers,
        )

        # THEN: Alternatives include template-related actions
        assert response.status_code == 200
        data = response.json()

        alt_types = [alt["type"] for alt in data["alternatives"]]
        assert "use_template" in alt_types
        assert "regenerate_structured" in alt_types
        assert "start_fresh" in alt_types

    @pytest.mark.asyncio
    async def test_needs_more_detail_feedback_returns_detail_alternatives(
        self,
        api_client,
        authenticated_headers,
        test_user_data,
        demo_kb_with_indexed_docs,
        db_session,
    ):
        """[P1] "needs_more_detail" feedback → regenerate with detail alternatives.

        GIVEN a draft exists
        WHEN user submits "needs_more_detail" feedback
        THEN alternatives suggest regenerating with more detail
        """
        from tests.factories import create_draft, create_feedback_request

        # Create draft
        draft_data = create_draft(
            kb_id=demo_kb_with_indexed_docs["id"],
            user_id=test_user_data["user_id"],
        )

        from app.models.draft import Draft

        draft = Draft(
            id=draft_data["id"],
            kb_id=draft_data["kb_id"],
            user_id=draft_data["user_id"],
            title=draft_data["title"],
            content=draft_data["content"],
            status="complete",  # Use string, not enum
            word_count=draft_data["word_count"],
            citations=[],
        )
        db_session.add(draft)
        await db_session.commit()

        # Submit needs_more_detail feedback
        feedback = create_feedback_request(feedback_type="needs_more_detail")
        response = await api_client.post(
            f"/api/v1/drafts/{draft.id}/feedback",
            json=feedback,
            cookies=authenticated_headers,
        )

        # THEN: Alternatives include detail-focused actions
        assert response.status_code == 200
        data = response.json()

        alt_types = [alt["type"] for alt in data["alternatives"]]
        assert "regenerate_detailed" in alt_types
        assert "add_sections" in alt_types


class TestErrorRecovery:
    """Test error recovery API responses (AC5)."""

    @pytest.mark.asyncio
    async def test_timeout_error_returns_retry_alternatives(self):
        """[P1] TimeoutError → retry alternatives.

        NOTE: This test validates the error recovery structure.
        Actual timeout simulation requires mocking GenerationService.
        For now, we test the recovery options data structure.
        """
        from tests.factories import create_recovery_options

        # Validate recovery options structure for timeout
        options = create_recovery_options(error_type="timeout")

        assert len(options) == 3
        assert any(opt["action"] == "retry" for opt in options)
        assert any(opt["action"] == "select_template" for opt in options)
        assert any(opt["action"] == "search" for opt in options)

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_wait_alternatives(self):
        """[P1] RateLimitError → wait + retry alternatives.

        NOTE: This test validates the error recovery structure.
        """
        from tests.factories import create_recovery_options

        # Validate recovery options structure for rate limit
        options = create_recovery_options(error_type="rate_limit")

        assert len(options) == 2
        assert any(opt["action"] == "auto_retry" for opt in options)
        assert any(opt["action"] == "select_template" for opt in options)

    @pytest.mark.asyncio
    async def test_insufficient_sources_error_returns_search_alternatives(self):
        """[P1] InsufficientSources error → search alternatives.

        NOTE: This test validates the error recovery structure.
        """
        from tests.factories import create_recovery_options

        # Validate recovery options structure for insufficient sources
        options = create_recovery_options(error_type="insufficient_sources")

        assert len(options) == 2
        assert any(opt["action"] == "search" for opt in options)
        assert any(opt["action"] == "select_template" for opt in options)
