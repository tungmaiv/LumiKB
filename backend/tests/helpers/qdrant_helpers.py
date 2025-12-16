"""Qdrant test helpers for integration tests.

These helpers allow tests to directly insert test data into Qdrant
without going through the full document processing pipeline.

This is useful for:
- Testing search functionality in isolation
- Creating deterministic test data with known embeddings
- Speeding up tests by bypassing Celery workers
"""

import hashlib
import uuid
from typing import Any

from qdrant_client.http import models

from app.integrations.qdrant_client import VECTOR_SIZE, qdrant_service


def create_test_embedding(
    text: str,
    seed: int | None = None,
) -> list[float]:
    """Create a deterministic test embedding vector.

    Generates a pseudo-random embedding based on text hash.
    This is NOT a real semantic embedding but allows predictable
    test behavior where similar texts produce similar vectors.

    Args:
        text: Text to generate embedding for.
        seed: Optional seed for reproducibility.

    Returns:
        List of floats of size VECTOR_SIZE (1536 for ada-002).

    Example:
        ```python
        # Same text always produces same embedding
        emb1 = create_test_embedding("OAuth 2.0")
        emb2 = create_test_embedding("OAuth 2.0")
        assert emb1 == emb2

        # Different texts produce different embeddings
        emb3 = create_test_embedding("MFA authentication")
        assert emb1 != emb3
        ```
    """
    import random

    # Create deterministic seed from text
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    combined_seed = int(text_hash[:8], 16)
    if seed is not None:
        combined_seed ^= seed

    # Generate pseudo-random embedding
    rng = random.Random(combined_seed)
    embedding = [rng.uniform(-1, 1) for _ in range(VECTOR_SIZE)]

    # Normalize to unit vector (like real embeddings)
    magnitude = sum(x * x for x in embedding) ** 0.5
    return [x / magnitude for x in embedding]


def create_test_chunk(
    text: str,
    document_id: str,
    document_name: str,
    kb_id: str,
    chunk_index: int = 0,
    page_number: int | None = None,
    section_header: str | None = None,
    char_start: int = 0,
    char_end: int | None = None,
    **extra_payload: Any,
) -> models.PointStruct:
    """Create a Qdrant point for a test chunk.

    Generates a PointStruct with:
    - Deterministic point ID based on document_id and chunk_index
    - Deterministic embedding based on chunk text
    - Standard payload fields matching production format

    Args:
        text: Chunk text content.
        document_id: Document ID (UUID string).
        document_name: Document display name.
        kb_id: Knowledge Base ID (UUID string).
        chunk_index: Index of chunk within document.
        page_number: Optional page number.
        section_header: Optional section header.
        char_start: Character start offset.
        char_end: Character end offset (defaults to len(text)).
        **extra_payload: Additional payload fields.

    Returns:
        PointStruct ready for Qdrant upsert.

    Example:
        ```python
        chunk = create_test_chunk(
            text="OAuth 2.0 is an authorization framework...",
            document_id=str(doc.id),
            document_name="OAuth Guide.md",
            kb_id=str(kb.id),
        )
        await qdrant_service.upsert_points(kb.id, [chunk])
        ```
    """
    # Generate deterministic point ID from document_id and chunk_index
    point_id_seed = f"{document_id}:{chunk_index}"
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id_seed))

    # Generate embedding from text
    embedding = create_test_embedding(text)

    # Build payload matching production format
    payload = {
        "chunk_text": text,
        "document_id": document_id,
        "document_name": document_name,
        "kb_id": kb_id,
        "chunk_index": chunk_index,
        "page_number": page_number,
        "section_header": section_header or "",
        "char_start": char_start,
        "char_end": char_end or char_start + len(text),
        **extra_payload,
    }

    return models.PointStruct(
        id=point_id,
        vector=embedding,
        payload=payload,
    )


async def insert_test_chunks(
    kb_id: uuid.UUID,
    chunks: list[dict[str, Any]],
    ensure_collection: bool = True,
) -> int:
    """Insert multiple test chunks into Qdrant for a KB.

    Convenience function that:
    1. Creates collection if needed
    2. Converts chunk dicts to PointStructs
    3. Upserts to Qdrant

    Args:
        kb_id: Knowledge Base UUID.
        chunks: List of chunk dicts with keys:
            - text: Chunk text (required)
            - document_id: Document ID (required)
            - document_name: Document name (required)
            - Other optional fields from create_test_chunk
        ensure_collection: Create collection if not exists (default: True).

    Returns:
        Number of chunks inserted.

    Raises:
        ValueError: If chunk missing required fields.

    Example:
        ```python
        chunks = [
            {
                "text": "OAuth 2.0 enables delegated access...",
                "document_id": str(doc1.id),
                "document_name": "OAuth Guide.md",
            },
            {
                "text": "MFA adds an extra security layer...",
                "document_id": str(doc2.id),
                "document_name": "Security Best Practices.md",
            },
        ]
        count = await insert_test_chunks(kb.id, chunks)
        assert count == 2
        ```
    """
    if ensure_collection:
        await qdrant_service.create_collection(kb_id)

    points = []
    for i, chunk in enumerate(chunks):
        # Validate required fields
        required = {"text", "document_id", "document_name"}
        missing = required - set(chunk.keys())
        if missing:
            raise ValueError(f"Chunk {i} missing required fields: {missing}")

        point = create_test_chunk(
            text=chunk["text"],
            document_id=chunk["document_id"],
            document_name=chunk["document_name"],
            kb_id=str(kb_id),
            chunk_index=chunk.get("chunk_index", i),
            page_number=chunk.get("page_number"),
            section_header=chunk.get("section_header"),
            char_start=chunk.get("char_start", 0),
            char_end=chunk.get("char_end"),
        )
        points.append(point)

    if points:
        return await qdrant_service.upsert_points(kb_id, points)

    return 0
