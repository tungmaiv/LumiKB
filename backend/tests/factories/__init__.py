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
]
