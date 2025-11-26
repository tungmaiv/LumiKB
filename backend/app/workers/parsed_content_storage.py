"""Parsed content storage for document processing pipeline.

Stores parsed content in MinIO for handoff to chunking task (Story 2.6).
Uses JSON format at path: {kb_id}/{doc_id}/.parsed.json
"""

import json
from io import BytesIO
from uuid import UUID

import structlog

from app.integrations.minio_client import minio_service
from app.workers.parsing import ParsedContent, ParsedElement

logger = structlog.get_logger(__name__)


async def store_parsed_content(
    kb_id: UUID,
    document_id: UUID,
    parsed: ParsedContent,
) -> str:
    """Store parsed content in MinIO for chunking step.

    Stores as JSON at path: {doc_id}/.parsed.json

    Args:
        kb_id: Knowledge Base UUID.
        document_id: Document UUID.
        parsed: ParsedContent from parsing.

    Returns:
        Storage path of the parsed content.
    """
    # Convert to serializable dict
    content_dict = {
        "text": parsed.text,
        "elements": [
            {
                "text": el.text,
                "element_type": el.element_type,
                "metadata": el.metadata,
            }
            for el in parsed.elements
        ],
        "metadata": parsed.metadata,
        "stats": {
            "extracted_chars": parsed.extracted_chars,
            "page_count": parsed.page_count,
            "section_count": parsed.section_count,
        },
    }

    # Serialize to JSON
    json_bytes = json.dumps(content_dict, ensure_ascii=False, indent=2).encode("utf-8")
    file_obj = BytesIO(json_bytes)

    # Store in MinIO
    object_path = f"{document_id}/.parsed.json"
    storage_path = await minio_service.upload_file(
        kb_id=kb_id,
        object_path=object_path,
        file=file_obj,
        content_type="application/json",
    )

    logger.info(
        "parsed_content_stored",
        kb_id=str(kb_id),
        document_id=str(document_id),
        storage_path=storage_path,
        extracted_chars=parsed.extracted_chars,
    )

    return storage_path


async def load_parsed_content(kb_id: UUID, document_id: UUID) -> ParsedContent | None:
    """Load parsed content from MinIO.

    Used by chunking task (Story 2.6) to retrieve parsed content.

    Args:
        kb_id: Knowledge Base UUID.
        document_id: Document UUID.

    Returns:
        ParsedContent if found, None otherwise.
    """
    object_path = f"{document_id}/.parsed.json"

    try:
        exists = await minio_service.file_exists(kb_id, object_path)
        if not exists:
            return None

        data = await minio_service.download_file(kb_id, object_path)
        content_dict = json.loads(data.decode("utf-8"))

        # Reconstruct ParsedContent
        elements = [
            ParsedElement(
                text=el["text"],
                element_type=el["element_type"],
                metadata=el["metadata"],
            )
            for el in content_dict["elements"]
        ]

        return ParsedContent(
            text=content_dict["text"],
            elements=elements,
            metadata=content_dict["metadata"],
        )

    except Exception as e:
        logger.error(
            "parsed_content_load_failed",
            kb_id=str(kb_id),
            document_id=str(document_id),
            error=str(e),
        )
        return None


async def delete_parsed_content(kb_id: UUID, document_id: UUID) -> bool:
    """Delete parsed content from MinIO after chunking completes.

    Args:
        kb_id: Knowledge Base UUID.
        document_id: Document UUID.

    Returns:
        True if deleted, False otherwise.
    """
    object_path = f"{document_id}/.parsed.json"

    try:
        exists = await minio_service.file_exists(kb_id, object_path)
        if not exists:
            return True  # Already deleted or never existed

        await minio_service.delete_file(kb_id, object_path)
        logger.info(
            "parsed_content_deleted",
            kb_id=str(kb_id),
            document_id=str(document_id),
        )
        return True

    except Exception as e:
        logger.error(
            "parsed_content_delete_failed",
            kb_id=str(kb_id),
            document_id=str(document_id),
            error=str(e),
        )
        return False
