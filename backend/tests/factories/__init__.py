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
from .conversation_factory import (
    create_chat_message,
    create_conversation,
    create_multi_turn_conversation,
)
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
from .feedback_factory import (
    create_alternative,
    create_feedback_request,
    create_feedback_with_context,
    create_generation_error,
    create_recovery_options,
)
from .generation_factory import (
    create_generation_request,
    create_streaming_generation_request,
    create_template_request,
)
from .group_factory import (
    create_group,
    create_group_data,
    create_group_member_response,
    create_group_response,
    create_group_update_data,
    create_group_with_members_response,
    create_member_add_data,
    create_paginated_groups_response,
)
from .kb_factory import create_kb_data, create_kb_update_data, create_knowledge_base
from .observability_factory import (
    create_chat_message as create_obs_chat_message,
)
from .observability_factory import (
    create_completed_trace,
    create_document_event,
    create_failed_trace,
    create_llm_span,
    create_metrics_aggregate,
    create_provider_sync_status,
    create_retrieval_span,
    create_span,
    create_trace,
    generate_span_id,
    generate_trace_id,
)
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
    # Generation factories (Epic 4)
    "create_generation_request",
    "create_streaming_generation_request",
    "create_template_request",
    # Conversation factories (Epic 4)
    "create_conversation",
    "create_multi_turn_conversation",
    "create_chat_message",
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
    # Group factories (Story 5.19)
    "create_group",
    "create_group_data",
    "create_group_update_data",
    "create_group_response",
    "create_group_with_members_response",
    "create_group_member_response",
    "create_member_add_data",
    "create_paginated_groups_response",
    # Observability factories (Epic 9)
    "generate_trace_id",
    "generate_span_id",
    "create_trace",
    "create_completed_trace",
    "create_failed_trace",
    "create_span",
    "create_llm_span",
    "create_retrieval_span",
    "create_obs_chat_message",
    "create_document_event",
    "create_metrics_aggregate",
    "create_provider_sync_status",
]
