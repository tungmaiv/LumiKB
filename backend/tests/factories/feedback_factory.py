"""Feedback and recovery factory with sensible defaults and explicit overrides.

Factory functions generate unique, parallel-safe test data using faker.
Override specific fields to make test intent explicit.
"""

from typing import Any

from faker import Faker

fake = Faker()


def create_feedback_request(**overrides: Any) -> dict:
    """Factory function for feedback request test data.

    Usage:
        feedback = create_feedback_request()  # Default "not_relevant"
        feedback = create_feedback_request(feedback_type="wrong_format")
        feedback = create_feedback_request(
            feedback_type="other",
            comments="Custom feedback text"
        )

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: Feedback request payload matching FeedbackRequest schema
    """
    defaults = {
        "feedback_type": "not_relevant",
        "comments": None,
    }

    # Apply overrides
    defaults.update(overrides)

    # Generate comments for "other" type if not provided
    if defaults["feedback_type"] == "other" and defaults["comments"] is None:
        defaults["comments"] = fake.sentence(nb_words=10)

    return defaults


def create_alternative(**overrides: Any) -> dict:
    """Factory for alternative suggestion metadata.

    Usage:
        alt = create_alternative()
        alt = create_alternative(
            type="use_template",
            description="Choose a different template",
            action="select_template"
        )

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: Alternative suggestion metadata
    """
    defaults = {
        "type": "re_search",
        "description": "Search for different sources with a broader or more specific query",
        "action": "change_search",
    }

    defaults.update(overrides)
    return defaults


def create_feedback_with_context(**overrides: Any) -> dict:
    """Factory for feedback request with regeneration context.

    Usage:
        feedback = create_feedback_with_context()  # Default with previous_draft_id
        feedback = create_feedback_with_context(
            feedback_type="needs_more_detail",
            previous_draft_id="specific-uuid"
        )

    Returns:
        dict: Feedback request with regeneration context
    """
    import uuid

    defaults = {
        "feedback_type": "needs_more_detail",
        "comments": "Add more technical details and examples",
        "previous_draft_id": str(uuid.uuid4()),
    }

    defaults.update(overrides)
    return defaults


def create_recovery_options(**overrides: Any) -> list[dict]:
    """Factory for error recovery options.

    Usage:
        options = create_recovery_options()  # Default 3 options
        options = create_recovery_options(error_type="timeout")

    Args:
        **overrides: Override error_type or options list

    Returns:
        list[dict]: List of recovery option dictionaries
    """
    error_type = overrides.pop("error_type", "timeout")

    # Recovery options by error type
    recovery_map = {
        "timeout": [
            {
                "type": "retry",
                "description": "Retry generation with same parameters",
                "action": "retry",
            },
            {
                "type": "use_template",
                "description": "Start from a structured template instead",
                "action": "select_template",
            },
            {
                "type": "search_more",
                "description": "Search for more sources before generating",
                "action": "search",
            },
        ],
        "rate_limit": [
            {
                "type": "wait_retry",
                "description": "Wait 30 seconds and retry automatically",
                "action": "auto_retry",
            },
            {
                "type": "use_template",
                "description": "Use a template while waiting",
                "action": "select_template",
            },
        ],
        "insufficient_sources": [
            {
                "type": "search_more",
                "description": "Search for more sources with different query",
                "action": "search",
            },
            {
                "type": "use_template",
                "description": "Start from a structured template",
                "action": "select_template",
            },
        ],
    }

    return recovery_map.get(error_type, recovery_map["timeout"])


def create_generation_error(**overrides: Any) -> dict:
    """Factory for generation error metadata.

    Usage:
        error = create_generation_error()  # Default timeout error
        error = create_generation_error(
            error_type="RateLimitError",
            message="Too many requests"
        )

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: Generation error metadata
    """
    defaults = {
        "message": "Generation took too long and was cancelled.",
        "error_type": "LLMTimeout",
        "recovery_options": create_recovery_options(error_type="timeout"),
    }

    defaults.update(overrides)
    return defaults
