#!/usr/bin/env python3
"""Generate pre-computed embeddings for demo documents.

This script loads demo markdown documents, chunks them into ~500 token segments
with 50 token overlap, generates embeddings using the configured model, and
saves the results to demo-embeddings.json.

Usage:
    python generate-embeddings.py [--model MODEL] [--output OUTPUT]

Environment Variables:
    LITELLM_URL: LiteLLM gateway URL (default: http://localhost:4000)
    LITELLM_API_KEY: API key for LiteLLM (default: sk-dev-master-key)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Try to import litellm for embedding generation
try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


# Constants
DEFAULT_MODEL = "text-embedding-ada-002"
DEFAULT_DIMENSION = 1536
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
APPROX_CHARS_PER_TOKEN = 4  # Rough approximation for English text

DEMO_DOCS_DIR = Path(__file__).parent.parent / "seed" / "demo-docs"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "seed" / "demo-embeddings.json"


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> list[dict[str, Any]]:
    """Chunk text into overlapping segments.

    Args:
        text: The full document text.
        chunk_size: Target chunk size in tokens.
        overlap: Overlap between chunks in tokens.

    Returns:
        List of chunk dictionaries with text, char_start, char_end, section_header.
    """
    # Convert token counts to approximate character counts
    chunk_chars = chunk_size * APPROX_CHARS_PER_TOKEN
    overlap_chars = overlap * APPROX_CHARS_PER_TOKEN

    chunks = []
    current_pos = 0
    current_section = "Introduction"

    # Extract section headers (# or ## headers)
    section_pattern = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)

    while current_pos < len(text):
        # Find the end of this chunk
        end_pos = min(current_pos + chunk_chars, len(text))

        # Try to break at a sentence or paragraph boundary
        if end_pos < len(text):
            # Look for paragraph break
            paragraph_break = text.rfind("\n\n", current_pos, end_pos)
            if paragraph_break > current_pos + chunk_chars // 2:
                end_pos = paragraph_break

            # Or look for sentence break
            elif (sentence_break := text.rfind(". ", current_pos, end_pos)) > 0:
                if sentence_break > current_pos + chunk_chars // 2:
                    end_pos = sentence_break + 1

        chunk_text_content = text[current_pos:end_pos].strip()

        # Find the current section header
        for match in section_pattern.finditer(text[:current_pos]):
            current_section = match.group(2).strip()

        if chunk_text_content:
            chunks.append(
                {
                    "text": chunk_text_content,
                    "char_start": current_pos,
                    "char_end": end_pos,
                    "section_header": current_section,
                }
            )

        # Move position, accounting for overlap
        current_pos = end_pos - overlap_chars
        if current_pos <= chunks[-1]["char_start"] if chunks else 0:
            current_pos = end_pos  # Prevent infinite loop

    return chunks


def generate_embedding(
    text: str,
    model: str = DEFAULT_MODEL,
) -> list[float]:
    """Generate embedding for text using LiteLLM.

    Args:
        text: Text to embed.
        model: Embedding model name.

    Returns:
        Embedding vector as list of floats.
    """
    if not LITELLM_AVAILABLE:
        raise RuntimeError(
            "litellm is not installed. Install with: pip install litellm"
        )

    # Configure LiteLLM
    litellm.api_base = os.environ.get("LITELLM_URL", "http://localhost:4000")
    litellm.api_key = os.environ.get("LITELLM_API_KEY", "sk-dev-master-key")

    response = litellm.embedding(model=model, input=[text])
    return response.data[0]["embedding"]


def generate_placeholder_embedding(text: str, dimension: int = DEFAULT_DIMENSION) -> list[float]:
    """Generate a deterministic placeholder embedding based on text hash.

    This is used when LiteLLM is not available or for testing.
    The embeddings are deterministic (same text = same embedding) but not
    semantically meaningful.

    Args:
        text: Text to generate placeholder embedding for.
        dimension: Embedding dimension.

    Returns:
        Placeholder embedding vector.
    """
    import random

    # Create a deterministic seed from text hash
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    seed = int(text_hash[:16], 16)

    # Use seeded random for deterministic results
    rng = random.Random(seed)

    # Generate deterministic floats
    embedding = [rng.gauss(0, 1) for _ in range(dimension)]

    # Normalize the vector
    magnitude = sum(x * x for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]

    return embedding


def process_documents(
    docs_dir: Path,
    model: str = DEFAULT_MODEL,
    use_placeholder: bool = False,
) -> dict[str, Any]:
    """Process all markdown documents in directory.

    Args:
        docs_dir: Directory containing markdown files.
        model: Embedding model name.
        use_placeholder: If True, use placeholder embeddings instead of real ones.

    Returns:
        Dictionary with metadata and all chunks with embeddings.
    """
    chunks_with_embeddings = []

    # Find all markdown files
    md_files = sorted(docs_dir.glob("*.md"))

    if not md_files:
        raise FileNotFoundError(f"No markdown files found in {docs_dir}")

    print(f"Found {len(md_files)} documents to process")

    for md_file in md_files:
        print(f"Processing: {md_file.name}")

        # Read document content
        content = md_file.read_text(encoding="utf-8")

        # Chunk the document
        chunks = chunk_text(content)
        print(f"  Created {len(chunks)} chunks")

        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            if use_placeholder:
                embedding = generate_placeholder_embedding(chunk["text"])
            else:
                try:
                    embedding = generate_embedding(chunk["text"], model)
                except Exception as e:
                    print(f"  Warning: Failed to generate embedding, using placeholder: {e}")
                    embedding = generate_placeholder_embedding(chunk["text"])

            chunks_with_embeddings.append(
                {
                    "document_name": md_file.name,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "char_start": chunk["char_start"],
                    "char_end": chunk["char_end"],
                    "section_header": chunk["section_header"],
                    "embedding": embedding,
                }
            )

    return {
        "model": model,
        "dimension": DEFAULT_DIMENSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "document_count": len(md_files),
        "chunk_count": len(chunks_with_embeddings),
        "chunks": chunks_with_embeddings,
    }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for demo documents"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Embedding model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DEMO_DOCS_DIR,
        help=f"Directory containing demo documents (default: {DEMO_DOCS_DIR})",
    )
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="Use placeholder embeddings (deterministic, not semantic)",
    )
    args = parser.parse_args()

    print(f"Demo Documents Directory: {args.docs_dir}")
    print(f"Output File: {args.output}")
    print(f"Model: {args.model}")
    print(f"Using Placeholders: {args.placeholder}")
    print()

    # Process documents
    result = process_documents(
        docs_dir=args.docs_dir,
        model=args.model,
        use_placeholder=args.placeholder,
    )

    # Save to JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print()
    print(f"Successfully generated embeddings:")
    print(f"  Documents: {result['document_count']}")
    print(f"  Chunks: {result['chunk_count']}")
    print(f"  Output: {args.output}")
    print()
    print("To regenerate embeddings with real model:")
    print(f"  python {Path(__file__).name} --model {args.model}")
    print()
    print("To regenerate with placeholder embeddings:")
    print(f"  python {Path(__file__).name} --placeholder")


if __name__ == "__main__":
    main()
