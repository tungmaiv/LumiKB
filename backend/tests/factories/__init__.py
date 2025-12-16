"""Test data factories for parallel-safe, schema-resilient test data.

Usage:
    from tests.factories import create_user, create_registration_data

    # Default user model data
    user = create_user()

    # Registration API payload (unique email each time)
    reg_data = create_registration_data()

    # Override specific fields
    admin = create_user(is_superuser=True, email="admin@example.com")
"""

from .document_factory import (
    create_document,
    create_document_data,
    create_document_upload_data,
    create_empty_file,
    create_outbox_event,
    create_oversized_content,
    create_test_docx_content,
    create_test_markdown_content,
    create_test_pdf_content,
)
from .draft_factory import (
    create_citation,
    create_draft,
    create_draft_update_data,
    create_draft_with_citations,
    create_regenerate_request,
)
from .admin_factory import (
    create_admin_stats,
    create_audit_event,
    create_audit_filter,
    create_config_value,
    create_kb_recommendation,
    create_kb_stats,
    create_onboarding_state,
    create_queue_status,
    create_recent_kb,
    create_task_info,
    create_worker_info,
)
from .feedback_factory import (
    create_alternative,
    create_feedback_request,
    create_feedback_with_context,
    create_generation_error,
    create_recovery_options,
)
from .kb_factory import create_kb_data, create_kb_update_data, create_knowledge_base
from .user_factory import create_admin_user, create_registration_data, create_user

__all__ = [
    # User factories
    "create_user",
    "create_admin_user",
    "create_registration_data",
    # KB factories
    "create_kb_data",
    "create_kb_update_data",
    "create_knowledge_base",
    # Document factories
    "create_document",
    "create_document_data",
    "create_document_upload_data",
    "create_test_pdf_content",
    "create_test_markdown_content",
    "create_test_docx_content",
    "create_empty_file",
    "create_oversized_content",
    # Outbox factories
    "create_outbox_event",
    # Draft factories
    "create_draft",
    "create_draft_with_citations",
    "create_citation",
    "create_draft_update_data",
    "create_regenerate_request",
    # Feedback factories
    "create_feedback_request",
    "create_alternative",
    "create_feedback_with_context",
    "create_recovery_options",
    "create_generation_error",
    # Admin factories (Epic 5)
    "create_admin_stats",
    "create_audit_filter",
    "create_audit_event",
    "create_queue_status",
    "create_worker_info",
    "create_config_value",
    "create_kb_stats",
    "create_onboarding_state",
    "create_kb_recommendation",
    "create_recent_kb",
    "create_task_info",
]
