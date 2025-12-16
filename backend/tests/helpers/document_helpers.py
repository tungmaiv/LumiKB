"""Document indexing helpers for integration tests.

These helpers manage document upload and indexing lifecycle in tests.
They allow tests to wait for asynchronous document processing to complete.
"""

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.models.document import Document, DocumentStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def poll_document_status(
    session: "AsyncSession",
    document_id: UUID,
    timeout: float = 30.0,
    poll_interval: float = 0.5,
) -> DocumentStatus:
    """Poll document status until it reaches a terminal state.

    Args:
        session: Database session for querying document status.
        document_id: Document ID to poll.
        timeout: Maximum time to wait in seconds (default: 30s).
        poll_interval: Time between polls in seconds (default: 0.5s).

    Returns:
        Final DocumentStatus.

    Raises:
        TimeoutError: If document doesn't reach terminal state within timeout.
        ValueError: If document not found.
    """
    terminal_states = {
        DocumentStatus.READY,
        DocumentStatus.FAILED,
        DocumentStatus.ARCHIVED,
    }
    elapsed = 0.0

    while elapsed < timeout:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()

        if doc is None:
            raise ValueError(f"Document {document_id} not found")

        if doc.status in terminal_states:
            return doc.status

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        await session.expire_all()  # Refresh from DB

    raise TimeoutError(
        f"Document {document_id} did not reach terminal state within {timeout}s. "
        f"Current status: {doc.status if doc else 'unknown'}"
    )


async def wait_for_document_indexed(
    session: "AsyncSession",
    document_id: UUID,
    timeout: float = 60.0,
    poll_interval: float = 1.0,
) -> Document:
    """Wait for document to be fully indexed (status=READY).

    This helper is used in integration tests to wait for the
    asynchronous document processing pipeline to complete:
    1. Document uploaded to MinIO
    2. Celery worker processes document (parse, chunk, embed)
    3. Chunks indexed in Qdrant
    4. Document status updated to READY

    Args:
        session: Database session for querying.
        document_id: Document ID to wait for.
        timeout: Maximum wait time in seconds (default: 60s for large docs).
        poll_interval: Time between status checks (default: 1s).

    Returns:
        Document: The indexed document with status=READY.

    Raises:
        TimeoutError: If document doesn't reach READY within timeout.
        ValueError: If document status is FAILED.

    Example:
        ```python
        # Upload document
        doc_response = await client.post(f"/api/v1/knowledge-bases/{kb_id}/documents", ...)

        # Wait for indexing
        doc = await wait_for_document_indexed(session, doc_response.json()["id"])

        # Now search will find chunks from this document
        search_response = await client.post("/api/v1/search", json={"query": "test"})
        ```
    """
    status = await poll_document_status(
        session=session,
        document_id=document_id,
        timeout=timeout,
        poll_interval=poll_interval,
    )

    if status == DocumentStatus.FAILED:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one()
        raise ValueError(f"Document {document_id} failed processing: {doc.last_error}")

    if status != DocumentStatus.READY:
        raise ValueError(f"Document {document_id} in unexpected state: {status}")

    result = await session.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one()
