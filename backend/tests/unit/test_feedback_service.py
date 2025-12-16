"""Unit tests for FeedbackService."""

import pytest

from app.services.feedback_service import FeedbackService


class TestFeedbackService:
    """Test FeedbackService alternative suggestions and context building."""

    @pytest.fixture
    def feedback_service(self) -> FeedbackService:
        """Create FeedbackService instance."""
        return FeedbackService()

    # Test alternative suggestions for each feedback type (5 tests)

    def test_suggest_alternatives_not_relevant(self, feedback_service: FeedbackService):
        """Test alternatives for 'not_relevant' feedback."""
        alternatives = feedback_service.suggest_alternatives("not_relevant")

        assert len(alternatives) == 3
        assert alternatives[0].type == "re_search"
        assert alternatives[0].action == "change_search"
        assert alternatives[1].type == "add_context"
        assert alternatives[2].type == "start_fresh"

    def test_suggest_alternatives_wrong_format(self, feedback_service: FeedbackService):
        """Test alternatives for 'wrong_format' feedback."""
        alternatives = feedback_service.suggest_alternatives("wrong_format")

        assert len(alternatives) == 3
        assert alternatives[0].type == "use_template"
        assert alternatives[0].action == "select_template"
        assert alternatives[1].type == "regenerate_structured"
        assert alternatives[2].type == "start_fresh"

    def test_suggest_alternatives_needs_more_detail(self, feedback_service: FeedbackService):
        """Test alternatives for 'needs_more_detail' feedback."""
        alternatives = feedback_service.suggest_alternatives("needs_more_detail")

        assert len(alternatives) == 3
        assert alternatives[0].type == "regenerate_detailed"
        assert alternatives[0].action == "regenerate_detailed"
        assert alternatives[1].type == "add_sections"
        assert alternatives[2].type == "start_fresh"

    def test_suggest_alternatives_low_confidence(self, feedback_service: FeedbackService):
        """Test alternatives for 'low_confidence' feedback."""
        alternatives = feedback_service.suggest_alternatives("low_confidence")

        assert len(alternatives) == 3
        assert alternatives[0].type == "better_sources"
        assert alternatives[0].action == "search_better_sources"
        assert alternatives[1].type == "review_citations"
        assert alternatives[2].type == "start_fresh"

    def test_suggest_alternatives_other(self, feedback_service: FeedbackService):
        """Test alternatives for 'other' feedback."""
        alternatives = feedback_service.suggest_alternatives("other")

        assert len(alternatives) == 3
        assert alternatives[0].type == "regenerate_with_feedback"
        assert alternatives[0].action == "regenerate_with_feedback"
        assert alternatives[1].type == "adjust_parameters"
        assert alternatives[2].type == "start_fresh"

    def test_suggest_alternatives_invalid_type(self, feedback_service: FeedbackService):
        """Test ValueError for invalid feedback type."""
        with pytest.raises(ValueError) as exc_info:
            feedback_service.suggest_alternatives("invalid_type")

        assert "Invalid feedback type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)

    # Test context builder (3 tests)

    def test_build_regeneration_context_not_relevant(self, feedback_service: FeedbackService):
        """Test context builder appends 'not_relevant' instruction."""
        original = "Generate RFP response for authentication"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="not_relevant",
        )

        assert original in enhanced
        assert "Based on user feedback:" in enhanced
        assert "Focus on the core context" in enhanced
        assert "ensure all content directly addresses the requirements" in enhanced

    def test_build_regeneration_context_needs_more_detail(self, feedback_service: FeedbackService):
        """Test context builder appends 'needs_more_detail' instruction."""
        original = "Generate security checklist"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="needs_more_detail",
        )

        assert original in enhanced
        assert "Based on user feedback:" in enhanced
        assert "Provide detailed explanation" in enhanced
        assert "specific examples" in enhanced
        assert "technical depth" in enhanced

    def test_build_regeneration_context_other_with_comments(self, feedback_service: FeedbackService):
        """Test context builder uses custom comments for 'other' type."""
        original = "Generate requirements summary"
        custom_comment = "Add more metrics and KPIs"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="other",
            comments=custom_comment,
        )

        assert original in enhanced
        assert "Based on user feedback:" in enhanced
        assert custom_comment in enhanced

    def test_build_regeneration_context_low_confidence(self, feedback_service: FeedbackService):
        """Test context builder appends 'low_confidence' instruction."""
        original = "Generate technical analysis"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="low_confidence",
        )

        assert original in enhanced
        assert "Based on user feedback:" in enhanced
        assert "Only use high-confidence sources" in enhanced
        assert "relevance score > 0.8" in enhanced

    def test_build_regeneration_context_wrong_format(self, feedback_service: FeedbackService):
        """Test context builder appends 'wrong_format' instruction."""
        original = "Generate gap analysis"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="wrong_format",
        )

        assert original in enhanced
        assert "Based on user feedback:" in enhanced
        assert "Follow the requested template structure" in enhanced
        assert "clear section headings" in enhanced

    # Test all alternatives have required fields (2 tests)

    def test_all_alternatives_have_required_fields(self, feedback_service: FeedbackService):
        """Test all alternatives have type, description, action fields."""
        feedback_types = ["not_relevant", "wrong_format", "needs_more_detail", "low_confidence", "other"]

        for feedback_type in feedback_types:
            alternatives = feedback_service.suggest_alternatives(feedback_type)

            for alt in alternatives:
                assert hasattr(alt, "type")
                assert hasattr(alt, "description")
                assert hasattr(alt, "action")
                assert len(alt.type) > 0
                assert len(alt.description) > 0
                assert len(alt.action) > 0

    def test_start_fresh_always_available(self, feedback_service: FeedbackService):
        """Test 'start_fresh' alternative appears in most feedback types."""
        feedback_types = ["not_relevant", "wrong_format", "needs_more_detail", "low_confidence", "other"]

        for feedback_type in feedback_types:
            alternatives = feedback_service.suggest_alternatives(feedback_type)
            alternative_types = [alt.type for alt in alternatives]

            # At least one alternative should provide a recovery path
            assert len(alternative_types) >= 1

            # 'start_fresh' should be available for all types
            assert "start_fresh" in alternative_types

    # Test context builder with empty original context (2 tests)

    def test_build_regeneration_context_empty_original(self, feedback_service: FeedbackService):
        """Test context builder handles empty original context."""
        enhanced = feedback_service.build_regeneration_context(
            original_context="",
            feedback_type="needs_more_detail",
        )

        assert "Based on user feedback:" in enhanced
        assert "Provide detailed explanation" in enhanced

    def test_build_regeneration_context_other_without_comments(self, feedback_service: FeedbackService):
        """Test context builder handles 'other' without comments."""
        original = "Generate document"
        enhanced = feedback_service.build_regeneration_context(
            original_context=original,
            feedback_type="other",
            comments=None,
        )

        # Should NOT append feedback instructions if no comments for 'other'
        assert original == enhanced or "Based on user feedback:" not in enhanced
