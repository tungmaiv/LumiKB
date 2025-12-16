#!/usr/bin/env python3
"""E2E Test Database Seeding Script.

This script seeds the E2E test database with consistent test data:
- Test users (admin, regular user)
- Test knowledge bases with permissions
- Test documents with indexed content

Story 7-1: Docker E2E Infrastructure

Usage:
    docker-compose -f docker-compose.e2e.yml exec backend python seed_e2e.py

Environment Variables:
    LUMIKB_DATABASE_URL: PostgreSQL connection string
    LUMIKB_MINIO_*: MinIO connection settings
    LUMIKB_QDRANT_*: Qdrant connection settings
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import uuid
from pathlib import Path

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.models.document import Document, DocumentStatus  # noqa: E402
from app.models.knowledge_base import KnowledgeBase  # noqa: E402
from app.models.permission import KBPermission, PermissionLevel  # noqa: E402
from app.models.user import User  # noqa: E402

# =============================================================================
# E2E Test Data Constants
# =============================================================================

# Test Users
E2E_ADMIN_EMAIL = "admin@e2e-test.com"
E2E_ADMIN_PASSWORD = "admin123"

E2E_USER_EMAIL = "user@e2e-test.com"
E2E_USER_PASSWORD = "user123"

# Secondary test user for permission tests
E2E_USER2_EMAIL = "user2@e2e-test.com"
E2E_USER2_PASSWORD = "user2123"

# Test Knowledge Bases
E2E_KB1_NAME = "E2E Test KB - Documents"
E2E_KB1_DESCRIPTION = "Knowledge base for E2E document testing"

E2E_KB2_NAME = "E2E Test KB - Search"
E2E_KB2_DESCRIPTION = "Knowledge base for E2E search and chat testing"

E2E_KB3_NAME = "E2E Test KB - Permissions"
E2E_KB3_DESCRIPTION = "Knowledge base for E2E permission testing"

# Test Documents (mock content for search/chat tests)
E2E_TEST_DOCUMENTS = [
    {
        "name": "architecture-overview.md",
        "content": """# LumiKB Architecture Overview

LumiKB is a knowledge base management system with semantic search capabilities.

## Core Components

### Backend Services
- FastAPI application server
- Celery workers for document processing
- PostgreSQL for relational data
- Qdrant for vector search
- Redis for caching and sessions

### Frontend
- Next.js React application
- TypeScript with strict typing
- Tailwind CSS for styling

## Document Processing Pipeline

1. Upload document to MinIO storage
2. Parse document content (PDF, DOCX, MD)
3. Chunk content into semantic segments
4. Generate embeddings via LiteLLM
5. Store vectors in Qdrant collection

## Search Flow

When a user searches:
1. Query is embedded using the same model
2. Vector similarity search in Qdrant
3. Top-k results retrieved with metadata
4. LLM synthesizes answer with citations
""",
        "mime_type": "text/markdown",
    },
    {
        "name": "user-guide.md",
        "content": """# LumiKB User Guide

Welcome to LumiKB! This guide covers the main features.

## Getting Started

### Creating a Knowledge Base
1. Click "New Knowledge Base" button
2. Enter a name and description
3. Click "Create"

### Uploading Documents
Supported formats:
- PDF documents
- Microsoft Word (DOCX)
- Markdown files
- Plain text files

To upload:
1. Select a knowledge base
2. Click "Upload" or drag files
3. Wait for processing to complete

## Searching

### Basic Search
Type your question in the search bar. LumiKB will:
- Find relevant document sections
- Generate an AI-powered answer
- Show inline citations

### Advanced Features
- Use quotes for exact phrases
- Filter by document type
- Sort by relevance or date

## Chat Interface

The chat interface allows multi-turn conversations:
- Ask follow-up questions
- Request clarifications
- Generate documents based on context
""",
        "mime_type": "text/markdown",
    },
    {
        "name": "api-reference.md",
        "content": """# LumiKB API Reference

## Authentication

All API endpoints require authentication via JWT token.

### Login
```
POST /api/v1/auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password
```

### Response
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Knowledge Bases

### List Knowledge Bases
```
GET /api/v1/knowledge-bases
Authorization: Bearer <token>
```

### Create Knowledge Base
```
POST /api/v1/knowledge-bases
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My KB",
  "description": "Description"
}
```

## Documents

### Upload Document
```
POST /api/v1/knowledge-bases/{kb_id}/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

### Get Document Status
```
GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}
Authorization: Bearer <token>
```

## Search

### Semantic Search
```
POST /api/v1/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "How does document processing work?",
  "kb_ids": ["uuid-1", "uuid-2"],
  "top_k": 5
}
```
""",
        "mime_type": "text/markdown",
    },
]

# Vector dimension for test embeddings
VECTOR_DIMENSION = 768


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.environ.get(
        "LUMIKB_DATABASE_URL",
        "postgresql+asyncpg://e2e_user:e2e_pass@postgres:5432/e2e_lumikb",
    )


def get_minio_config() -> dict:
    """Get MinIO configuration from environment."""
    return {
        "endpoint": os.environ.get("LUMIKB_MINIO_ENDPOINT", "minio:9000"),
        "access_key": os.environ.get("LUMIKB_MINIO_ACCESS_KEY", "e2e_minio"),
        "secret_key": os.environ.get("LUMIKB_MINIO_SECRET_KEY", "e2e_minio_secret"),
        "secure": os.environ.get("LUMIKB_MINIO_SECURE", "false").lower() == "true",
    }


def get_qdrant_config() -> dict:
    """Get Qdrant configuration from environment."""
    return {
        "host": os.environ.get("LUMIKB_QDRANT_HOST", "qdrant"),
        "port": int(os.environ.get("LUMIKB_QDRANT_PORT", "6333")),
    }


async def run_migrations(engine) -> None:
    """Run Alembic migrations programmatically."""
    print("Running database migrations...")

    # Use Alembic to run migrations
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")

    # Run migrations in a sync context
    def run_upgrade():
        command.upgrade(alembic_cfg, "head")

    # Run in thread pool since Alembic is sync
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_upgrade)

    print("  Migrations complete")


async def get_or_create_user(
    session: AsyncSession,
    email: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    """Get existing user or create a new one.

    Args:
        session: Database session.
        email: User email.
        password: User password.
        is_superuser: Whether user is admin.

    Returns:
        The user.
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        print(f"  User already exists: {email}")
        return user

    ph = PasswordHasher()
    hashed_password = ph.hash(password)

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=is_superuser,
        is_verified=True,
        onboarding_completed=True,
    )
    session.add(user)
    await session.flush()

    role = "admin" if is_superuser else "user"
    print(f"  Created {role} user: {email}")
    return user


async def get_or_create_kb(
    session: AsyncSession,
    name: str,
    description: str,
    owner: User,
) -> KnowledgeBase:
    """Get existing KB or create a new one.

    Args:
        session: Database session.
        name: KB name.
        description: KB description.
        owner: Owner user.

    Returns:
        The Knowledge Base.
    """
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.name == name)
    )
    kb = result.scalar_one_or_none()

    if kb:
        print(f"  KB already exists: {name}")
        return kb

    kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=name,
        description=description,
        owner_id=owner.id,
        status="active",
    )
    session.add(kb)
    await session.flush()

    print(f"  Created KB: {name}")
    return kb


async def grant_permission(
    session: AsyncSession,
    user: User,
    kb: KnowledgeBase,
    level: PermissionLevel,
) -> None:
    """Grant permission on KB to user.

    Args:
        session: Database session.
        user: User to grant permission to.
        kb: Knowledge Base.
        level: Permission level.
    """
    result = await session.execute(
        select(KBPermission).where(
            KBPermission.user_id == user.id,
            KBPermission.kb_id == kb.id,
        )
    )
    permission = result.scalar_one_or_none()

    if permission:
        print(f"  Permission already exists for {user.email} on {kb.name}")
        return

    permission = KBPermission(
        id=uuid.uuid4(),
        user_id=user.id,
        kb_id=kb.id,
        permission_level=level,
    )
    session.add(permission)
    await session.flush()

    print(f"  Granted {level.value} permission to {user.email} on {kb.name}")


async def create_document(
    session: AsyncSession,
    kb: KnowledgeBase,
    doc_info: dict,
) -> Document:
    """Create a test document record.

    Args:
        session: Database session.
        kb: Knowledge Base.
        doc_info: Document information dict.

    Returns:
        The Document.
    """
    name = doc_info["name"]

    result = await session.execute(
        select(Document).where(
            Document.kb_id == kb.id,
            Document.name == name,
        )
    )
    doc = result.scalar_one_or_none()

    if doc:
        print(f"  Document already exists: {name}")
        return doc

    content = doc_info["content"]
    checksum = hashlib.sha256(content.encode()).hexdigest()

    doc = Document(
        id=uuid.uuid4(),
        kb_id=kb.id,
        name=name,
        original_filename=name,
        mime_type=doc_info["mime_type"],
        file_size_bytes=len(content.encode()),
        checksum=checksum,
        file_path=f"kb-{kb.id}/{name}",
        status=DocumentStatus.READY,
        chunk_count=len(content) // 500 + 1,  # Approximate chunk count
    )
    session.add(doc)
    await session.flush()

    print(f"  Created document: {name}")
    return doc


def setup_minio_bucket(kb_id: uuid.UUID, documents: list[dict]) -> None:
    """Create MinIO bucket and upload test documents.

    Args:
        kb_id: Knowledge Base UUID.
        documents: List of document info dicts.
    """
    try:
        from io import BytesIO

        from minio import Minio
    except ImportError:
        print("  Warning: minio package not installed, skipping MinIO setup")
        return

    config = get_minio_config()

    client = Minio(
        config["endpoint"],
        access_key=config["access_key"],
        secret_key=config["secret_key"],
        secure=config["secure"],
    )

    bucket_name = f"kb-{kb_id}"

    # Create bucket if not exists
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"  Created bucket: {bucket_name}")
    else:
        print(f"  Bucket already exists: {bucket_name}")

    # Upload documents
    for doc_info in documents:
        object_name = doc_info["name"]
        content = doc_info["content"].encode()

        try:
            client.stat_object(bucket_name, object_name)
            print(f"  Object already exists: {object_name}")
            continue
        except Exception:
            pass

        client.put_object(
            bucket_name,
            object_name,
            BytesIO(content),
            len(content),
            content_type=doc_info["mime_type"],
        )
        print(f"  Uploaded: {object_name}")


def setup_qdrant_collection(kb_id: uuid.UUID) -> None:
    """Create Qdrant collection for KB.

    Args:
        kb_id: Knowledge Base UUID.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
    except ImportError:
        print("  Warning: qdrant-client package not installed, skipping Qdrant setup")
        return

    config = get_qdrant_config()

    client = QdrantClient(host=config["host"], port=config["port"])

    collection_name = f"kb_{kb_id}"

    # Check if collection exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        print(f"  Collection already exists: {collection_name}")
        return

    # Create collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_DIMENSION,
            distance=Distance.COSINE,
        ),
    )
    print(f"  Created collection: {collection_name}")


def insert_test_vectors(
    kb_id: uuid.UUID,
    documents: list[Document],
    doc_contents: list[dict],
) -> None:
    """Insert mock vectors for test documents.

    Args:
        kb_id: Knowledge Base UUID.
        documents: List of Document objects.
        doc_contents: List of document content dicts.
    """
    try:
        import random

        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
    except ImportError:
        print("  Warning: qdrant-client package not installed, skipping vector insert")
        return

    config = get_qdrant_config()
    client = QdrantClient(host=config["host"], port=config["port"])

    collection_name = f"kb_{kb_id}"

    # Check existing points
    try:
        collection_info = client.get_collection(collection_name)
        if collection_info.points_count > 0:
            print(f"  Collection already has {collection_info.points_count} points")
            return
    except Exception:
        print(f"  Collection {collection_name} not found, skipping")
        return

    # Generate mock vectors for each document chunk
    points = []
    for doc, doc_info in zip(documents, doc_contents, strict=False):
        content = doc_info["content"]

        # Simple chunking by paragraphs
        chunks = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, chunk_text in enumerate(chunks):
            # Generate deterministic mock vector based on chunk content
            random.seed(hash(chunk_text) % (2**32))
            mock_vector = [random.gauss(0, 1) for _ in range(VECTOR_DIMENSION)]

            # Normalize vector
            magnitude = sum(x**2 for x in mock_vector) ** 0.5
            mock_vector = [x / magnitude for x in mock_vector]

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=mock_vector,
                payload={
                    "document_id": str(doc.id),
                    "document_name": doc.name,
                    "chunk_index": i,
                    "chunk_text": chunk_text[:1000],  # Limit chunk text length
                    "section_header": chunk_text.split("\n")[0][:100]
                    if chunk_text
                    else "",
                },
            )
            points.append(point)

    if points:
        client.upsert(collection_name=collection_name, points=points)
        print(f"  Inserted {len(points)} vectors")


async def seed_e2e_database() -> None:
    """Main E2E seeding function."""
    print("=" * 60)
    print("LumiKB E2E Database Seeding")
    print("=" * 60)

    print("\nConnecting to database...")
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Run migrations first
    try:
        await run_migrations(engine)
    except Exception as e:
        print(f"  Warning: Migration failed (may already be applied): {e}")

    async with async_session() as session:
        # Create users
        print("\nCreating test users...")
        admin_user = await get_or_create_user(
            session, E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD, is_superuser=True
        )
        regular_user = await get_or_create_user(
            session, E2E_USER_EMAIL, E2E_USER_PASSWORD, is_superuser=False
        )
        user2 = await get_or_create_user(
            session, E2E_USER2_EMAIL, E2E_USER2_PASSWORD, is_superuser=False
        )

        # Create knowledge bases
        print("\nCreating test knowledge bases...")
        kb1 = await get_or_create_kb(
            session, E2E_KB1_NAME, E2E_KB1_DESCRIPTION, admin_user
        )
        kb2 = await get_or_create_kb(
            session, E2E_KB2_NAME, E2E_KB2_DESCRIPTION, regular_user
        )
        kb3 = await get_or_create_kb(
            session, E2E_KB3_NAME, E2E_KB3_DESCRIPTION, admin_user
        )

        # Grant permissions
        print("\nSetting up permissions...")
        # KB1: admin owns, regular user has WRITE
        await grant_permission(session, regular_user, kb1, PermissionLevel.WRITE)
        # KB2: regular user owns, admin has ADMIN (owner already has ADMIN)
        await grant_permission(session, admin_user, kb2, PermissionLevel.ADMIN)
        # KB3: admin owns, user2 has READ only
        await grant_permission(session, user2, kb3, PermissionLevel.READ)

        # Create test documents in KB2 (search/chat tests)
        print("\nCreating test documents...")
        documents = []
        for doc_info in E2E_TEST_DOCUMENTS:
            doc = await create_document(session, kb2, doc_info)
            documents.append(doc)

        await session.commit()
        print("\nDatabase changes committed")

    # Setup MinIO (outside transaction)
    print("\nSetting up MinIO storage...")
    try:
        setup_minio_bucket(kb2.id, E2E_TEST_DOCUMENTS)
    except Exception as e:
        print(f"  Warning: MinIO setup failed: {e}")

    # Setup Qdrant (outside transaction)
    print("\nSetting up Qdrant collections...")
    try:
        setup_qdrant_collection(kb1.id)
        setup_qdrant_collection(kb2.id)
        setup_qdrant_collection(kb3.id)
    except Exception as e:
        print(f"  Warning: Qdrant setup failed: {e}")

    # Insert test vectors for KB2
    print("\nInserting test vectors...")
    try:
        insert_test_vectors(kb2.id, documents, E2E_TEST_DOCUMENTS)
    except Exception as e:
        print(f"  Warning: Vector insert failed: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("E2E Seeding Complete!")
    print("=" * 60)
    print("\nTest Credentials:")
    print(f"  Admin: {E2E_ADMIN_EMAIL} / {E2E_ADMIN_PASSWORD}")
    print(f"  User:  {E2E_USER_EMAIL} / {E2E_USER_PASSWORD}")
    print(f"  User2: {E2E_USER2_EMAIL} / {E2E_USER2_PASSWORD}")
    print("\nKnowledge Bases:")
    print(f"  {E2E_KB1_NAME} (ID: {kb1.id})")
    print(f"  {E2E_KB2_NAME} (ID: {kb2.id})")
    print(f"  {E2E_KB3_NAME} (ID: {kb3.id})")
    print("\nDocuments seeded in KB2 for search/chat testing")
    print("=" * 60)


def main() -> None:
    """Main entry point."""
    asyncio.run(seed_e2e_database())


if __name__ == "__main__":
    main()
