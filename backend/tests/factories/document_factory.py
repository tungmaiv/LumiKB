"""Document factory with sensible defaults.

Factory functions generate unique, parallel-safe document test data using faker.
"""

import hashlib
import uuid
from io import BytesIO
from typing import TYPE_CHECKING, Any

from faker import Faker

from app.models.document import Document, DocumentStatus
from app.models.outbox import Outbox

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()


def create_document_data(**overrides: Any) -> dict:
    """Factory function for document model data.

    Usage:
        doc = create_document_data()  # All defaults
        pdf_doc = create_document_data(mime_type="application/pdf")

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: Document data matching Document model fields
    """
    doc_id = uuid.uuid4()
    filename = f"document_{fake.word()}_{doc_id.hex[:6]}.pdf"

    defaults = {
        "id": doc_id,
        "name": fake.sentence(nb_words=3).rstrip("."),
        "original_filename": filename,
        "mime_type": "application/pdf",
        "file_size_bytes": fake.random_int(min=1024, max=10 * 1024 * 1024),
        "file_path": f"kb-{uuid.uuid4()}/{doc_id}/{filename}",
        "checksum": fake.sha256(),
        "status": DocumentStatus.PENDING,
        "chunk_count": 0,
        "processing_started_at": None,
        "processing_completed_at": None,
        "last_error": None,
        "retry_count": 0,
        "deleted_at": None,
        "tags": [],
    }

    defaults.update(overrides)
    return defaults


def create_document_upload_data(
    filename: str = "test_document.pdf",
    content_type: str = "application/pdf",
    content: bytes | None = None,
) -> dict:
    """Create data for simulating file upload.

    Usage:
        upload = create_document_upload_data()
        upload = create_document_upload_data(filename="report.docx",
                                             content_type="application/vnd.openxmlformats...")

    Args:
        filename: Name of the file
        content_type: MIME type of the file
        content: File content bytes (generates random if None)

    Returns:
        dict with file data for upload simulation
    """
    if content is None:
        # Generate random content between 1KB and 1MB
        size = fake.random_int(min=1024, max=1024 * 1024)
        content = fake.binary(length=size)

    return {
        "filename": filename,
        "content_type": content_type,
        "content": content,
        "file": BytesIO(content),
    }


def create_test_pdf_content() -> bytes:
    """Create minimal valid PDF content for testing.

    Returns:
        bytes: Valid PDF file content
    """
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
192
%%EOF"""
    return pdf_content


def create_test_markdown_content() -> bytes:
    """Create markdown content for testing.

    Returns:
        bytes: Markdown file content
    """
    return f"""# Test Document

## Introduction

{fake.paragraph(nb_sentences=5)}

## Section 1

{fake.paragraph(nb_sentences=3)}

### Subsection 1.1

- {fake.sentence()}
- {fake.sentence()}
- {fake.sentence()}

## Conclusion

{fake.paragraph(nb_sentences=2)}
""".encode()


def create_test_docx_content() -> bytes:
    """Create minimal DOCX content for testing.

    Note: This is a minimal valid DOCX file structure.
    For more complex testing, use actual test fixture files.

    Returns:
        bytes: Minimal DOCX file content
    """
    # DOCX files are ZIP archives with specific structure
    # This is a minimal valid DOCX - just the content types and minimal document
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
        zf.writestr("[Content_Types].xml", content_types)

        # _rels/.rels
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
        zf.writestr("_rels/.rels", rels)

        # word/document.xml
        document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Test Document Content</w:t></w:r></w:p>
</w:body>
</w:document>"""
        zf.writestr("word/document.xml", document)

    return buffer.getvalue()


def create_empty_file() -> bytes:
    """Create empty file content for testing validation.

    Returns:
        bytes: Empty content
    """
    return b""


def create_oversized_content(size_mb: int = 51) -> bytes:
    """Create oversized content for testing file size validation.

    Args:
        size_mb: Size in megabytes (default 51MB to exceed 50MB limit)

    Returns:
        bytes: Content of specified size
    """
    # Generate content that exceeds the limit
    return b"x" * (size_mb * 1024 * 1024)


async def create_document(
    session: "AsyncSession",
    kb_id: uuid.UUID | None = None,
    **overrides: Any,
) -> Document:
    """Create a document record in the database.

    Args:
        session: Database session.
        kb_id: Knowledge Base ID (required if not in overrides).
        **overrides: Any field to override from defaults.

    Returns:
        Document: Created document instance.
    """
    data = create_document_data(**overrides)

    if kb_id is not None:
        data["kb_id"] = kb_id

    # Generate proper checksum for file content
    if "checksum" not in overrides:
        content = b"test file content"
        data["checksum"] = hashlib.sha256(content).hexdigest()

    doc = Document(**data)
    session.add(doc)
    await session.flush()
    return doc


async def create_outbox_event(
    session: "AsyncSession",
    event_type: str,
    aggregate_id: uuid.UUID,
    aggregate_type: str = "document",
    payload: dict | None = None,
    **overrides: Any,
) -> Outbox:
    """Create an outbox event record in the database.

    Args:
        session: Database session.
        event_type: Event type (e.g., "document.process").
        aggregate_id: ID of the aggregate (e.g., document_id).
        aggregate_type: Type of aggregate.
        payload: Event payload.
        **overrides: Any field to override.

    Returns:
        Outbox: Created outbox event instance.
    """
    defaults = {
        "event_type": event_type,
        "aggregate_id": aggregate_id,
        "aggregate_type": aggregate_type,
        "payload": payload or {},
        "attempts": 0,
        "last_error": None,
        "processed_at": None,
    }
    defaults.update(overrides)

    event = Outbox(**defaults)
    session.add(event)
    await session.flush()
    return event
