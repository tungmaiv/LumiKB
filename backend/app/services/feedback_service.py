"""
Feedback service for analyzing user feedback and suggesting recovery alternatives.

Provides intelligent recovery suggestions based on feedback type to help users
regenerate better drafts without starting from scratch.
"""


from pydantic import BaseModel


class Alternative(BaseModel):
    """Recovery alternative suggestion."""

    type: str  # Action type identifier
    description: str  # Human-readable description
    action: str  # Frontend action to trigger


class FeedbackService:
    """
    Analyze user feedback and suggest recovery alternatives.

    Maps feedback types to actionable suggestions that guide regeneration.
    """

    ALTERNATIVES_MAP: dict[str, list[Alternative]] = {
        "not_relevant": [
            Alternative(
                type="re_search",
                description="Search for different sources with a broader or more specific query",
                action="change_search",
            ),
            Alternative(
                type="add_context",
                description="Provide more context or instructions to guide generation",
                action="add_context",
            ),
            Alternative(
                type="start_fresh",
                description="Clear this draft and start over",
                action="new_draft",
            ),
        ],
        "wrong_format": [
            Alternative(
                type="use_template",
                description="Choose a different template for structured output",
                action="select_template",
            ),
            Alternative(
                type="regenerate_structured",
                description="Regenerate with explicit structure guidelines",
                action="regenerate_with_structure",
            ),
            Alternative(
                type="start_fresh",
                description="Clear this draft and start over",
                action="new_draft",
            ),
        ],
        "needs_more_detail": [
            Alternative(
                type="regenerate_detailed",
                description="Regenerate with instructions to provide more detail and examples",
                action="regenerate_detailed",
            ),
            Alternative(
                type="add_sections",
                description="Manually add specific sections that are missing",
                action="add_sections",
            ),
            Alternative(
                type="start_fresh",
                description="Clear this draft and start over",
                action="new_draft",
            ),
        ],
        "low_confidence": [
            Alternative(
                type="better_sources",
                description="Search for higher-quality sources with stronger relevance",
                action="search_better_sources",
            ),
            Alternative(
                type="review_citations",
                description="Manually review and select citations to keep",
                action="review_citations",
            ),
            Alternative(
                type="start_fresh",
                description="Clear this draft and start over",
                action="new_draft",
            ),
        ],
        "other": [
            Alternative(
                type="regenerate_with_feedback",
                description="Regenerate with your custom feedback as instructions",
                action="regenerate_with_feedback",
            ),
            Alternative(
                type="adjust_parameters",
                description="Adjust generation parameters (temperature, sources, etc.)",
                action="adjust_parameters",
            ),
            Alternative(
                type="start_fresh",
                description="Clear this draft and start over",
                action="new_draft",
            ),
        ],
    }

    def suggest_alternatives(self, feedback_type: str) -> list[Alternative]:
        """
        Return suggested alternatives based on feedback type.

        Args:
            feedback_type: One of "not_relevant", "wrong_format", "needs_more_detail",
                          "low_confidence", "other"

        Returns:
            List of Alternative suggestions (max 3)

        Raises:
            ValueError: If feedback_type is invalid
        """
        if feedback_type not in self.ALTERNATIVES_MAP:
            valid_types = list(self.ALTERNATIVES_MAP.keys())
            raise ValueError(
                f"Invalid feedback type: {feedback_type}. "
                f"Must be one of {valid_types}"
            )

        return self.ALTERNATIVES_MAP[feedback_type]

    def build_regeneration_context(
        self, original_context: str, feedback_type: str, comments: str | None = None
    ) -> str:
        """
        Build enhanced context string for regeneration based on feedback.

        Args:
            original_context: User's original generation instructions
            feedback_type: Type of feedback received
            comments: Optional custom feedback comments

        Returns:
            Enhanced context string with feedback instructions

        Example:
            Original: "Generate RFP response for authentication section"
            Feedback: "needs_more_detail"
            Output: "Generate RFP response for authentication section.
                     Based on user feedback: Provide detailed explanation with
                     specific examples and technical depth."
        """
        feedback_instructions = {
            "not_relevant": "Focus on the core context and ensure all content directly addresses the requirements.",
            "wrong_format": "Follow the requested template structure strictly with clear section headings.",
            "needs_more_detail": "Provide detailed explanation with specific examples, technical depth, and comprehensive coverage.",
            "low_confidence": "Only use high-confidence sources (relevance score > 0.8) with strong citation support.",
            "other": f"Based on user feedback: {comments}" if comments else "",
        }

        instruction = feedback_instructions.get(feedback_type, "")

        if instruction:
            return f"{original_context}\n\nBased on user feedback: {instruction}"
        else:
            return original_context


def get_feedback_service() -> FeedbackService:
    """Dependency injection for FeedbackService."""
    return FeedbackService()
