#!/usr/bin/env python3
"""Seed demo Knowledge Base with pre-computed embeddings.

This script creates the demo KB, demo user, uploads documents to MinIO,
creates database records, and inserts pre-computed vectors into Qdrant.

Usage:
    python seed-data.py [--skip-embeddings] [--skip-minio]

Environment Variables:
    DEMO_USER_PASSWORD: Password for demo user (default: demo123)
    LUMIKB_DATABASE_URL: PostgreSQL connection string
    LUMIKB_MINIO_*: MinIO connection settings
    LUMIKB_QDRANT_*: Qdrant connection settings
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# Add backend to path for imports
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from argon2 import PasswordHasher  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

# Import models after path setup
from app.models.document import Document, DocumentStatus  # noqa: E402
from app.models.knowledge_base import KnowledgeBase  # noqa: E402
from app.models.permission import KBPermission, PermissionLevel  # noqa: E402
from app.models.user import User  # noqa: E402

# Constants
DEMO_KB_NAME = "Sample Knowledge Base"
DEMO_KB_DESCRIPTION = "Explore LumiKB with these demo documents about the platform's features"
DEMO_USER_EMAIL = "demo@lumikb.local"
DEFAULT_DEMO_PASSWORD = "demo123"

SEED_DIR = Path(__file__).parent.parent / "seed"
DEMO_DOCS_DIR = SEED_DIR / "demo-docs"
EMBEDDINGS_FILE = SEED_DIR / "demo-embeddings.json"


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.environ.get(
        "LUMIKB_DATABASE_URL",
        "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
    )


def get_minio_config() -> dict:
    """Get MinIO configuration from environment."""
    return {
        "endpoint": os.environ.get("LUMIKB_MINIO_ENDPOINT", "localhost:9000"),
        "access_key": os.environ.get("LUMIKB_MINIO_ACCESS_KEY", "lumikb"),
        "secret_key": os.environ.get("LUMIKB_MINIO_SECRET_KEY", "lumikb_dev_password"),
        "secure": os.environ.get("LUMIKB_MINIO_SECURE", "false").lower() == "true",
    }


def get_qdrant_config() -> dict:
    """Get Qdrant configuration from environment."""
    return {
        "host": os.environ.get("LUMIKB_QDRANT_HOST", "localhost"),
        "port": int(os.environ.get("LUMIKB_QDRANT_PORT", "6333")),
    }


async def get_or_create_demo_user(session: AsyncSession) -> User:
    """Get existing demo user or create a new one.

    Args:
        session: Database session.

    Returns:
        The demo user.
    """
    # Check if demo user exists
    result = await session.execute(
        select(User).where(User.email == DEMO_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if user:
        print(f"  Demo user already exists: {DEMO_USER_EMAIL}")
        return user

    # Create new demo user
    password = os.environ.get("DEMO_USER_PASSWORD", DEFAULT_DEMO_PASSWORD)
    ph = PasswordHasher()
    hashed_password = ph.hash(password)

    user = User(
        id=uuid.uuid4(),
        email=DEMO_USER_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    print(f"  Created demo user: {DEMO_USER_EMAIL}")
    return user


async def get_or_create_demo_kb(session: AsyncSession, owner: User) -> KnowledgeBase:
    """Get existing demo KB or create a new one.

    Args:
        session: Database session.
        owner: The owner user.

    Returns:
        The demo Knowledge Base.
    """
    # Check if demo KB exists
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.name == DEMO_KB_NAME)
    )
    kb = result.scalar_one_or_none()

    if kb:
        print(f"  Demo KB already exists: {DEMO_KB_NAME}")
        return kb

    # Create new demo KB
    kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=DEMO_KB_NAME,
        description=DEMO_KB_DESCRIPTION,
        owner_id=owner.id,
        status="active",
    )
    session.add(kb)
    await session.flush()

    print(f"  Created demo KB: {DEMO_KB_NAME}")
    return kb


async def grant_demo_permission(
    session: AsyncSession,
    user: User,
    kb: KnowledgeBase,
) -> None:
    """Grant READ permission on demo KB to user.

    Args:
        session: Database session.
        user: User to grant permission to.
        kb: Knowledge Base.
    """
    # Check if permission exists
    result = await session.execute(
        select(KBPermission).where(
            KBPermission.user_id == user.id,
            KBPermission.kb_id == kb.id,
        )
    )
    permission = result.scalar_one_or_none()

    if permission:
        print(f"  Permission already exists for user {user.email}")
        return

    # Create permission
    permission = KBPermission(
        id=uuid.uuid4(),
        user_id=user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.READ,
    )
    session.add(permission)
    await session.flush()

    print(f"  Granted READ permission to {user.email}")


async def create_document_records(
    session: AsyncSession,
    kb: KnowledgeBase,
    embeddings_data: dict,
) -> dict[str, Document]:
    """Create document records in database.

    Args:
        session: Database session.
        kb: Knowledge Base.
        embeddings_data: Loaded embeddings JSON.

    Returns:
        Mapping of document name to Document object.
    """
    # Get unique document names from chunks
    doc_names = sorted(set(chunk["document_name"] for chunk in embeddings_data["chunks"]))

    documents = {}

    for doc_name in doc_names:
        # Check if document exists
        result = await session.execute(
            select(Document).where(
                Document.kb_id == kb.id,
                Document.name == doc_name,
            )
        )
        doc = result.scalar_one_or_none()

        if doc:
            print(f"  Document already exists: {doc_name}")
            documents[doc_name] = doc
            continue

        # Count chunks for this document
        chunk_count = sum(
            1 for chunk in embeddings_data["chunks"]
            if chunk["document_name"] == doc_name
        )

        # Create document record
        doc = Document(
            id=uuid.uuid4(),
            kb_id=kb.id,
            name=doc_name,
            file_path=f"kb-{kb.id}/{doc_name}",
            status=DocumentStatus.READY,
            chunk_count=chunk_count,
        )
        session.add(doc)
        await session.flush()

        print(f"  Created document: {doc_name} ({chunk_count} chunks)")
        documents[doc_name] = doc

    return documents


def upload_to_minio(kb_id: uuid.UUID, docs_dir: Path) -> None:
    """Upload demo documents to MinIO.

    Args:
        kb_id: Knowledge Base UUID.
        docs_dir: Directory containing demo documents.
    """
    try:
        from minio import Minio
    except ImportError:
        print("  Warning: minio package not installed, skipping MinIO upload")
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

    # Upload each document
    for doc_path in docs_dir.glob("*.md"):
        object_name = doc_path.name

        # Check if object exists
        try:
            client.stat_object(bucket_name, object_name)
            print(f"  Object already exists: {object_name}")
            continue
        except Exception:
            pass

        client.fput_object(
            bucket_name,
            object_name,
            str(doc_path),
            content_type="text/markdown",
        )
        print(f"  Uploaded: {object_name}")


def setup_qdrant_collection(kb_id: uuid.UUID, dimension: int = 1536) -> None:
    """Create Qdrant collection for demo KB.

    Args:
        kb_id: Knowledge Base UUID.
        dimension: Vector dimension.
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
            size=dimension,
            distance=Distance.COSINE,
        ),
    )
    print(f"  Created collection: {collection_name}")


def insert_vectors(
    kb_id: uuid.UUID,
    documents: dict[str, Document],
    embeddings_data: dict,
) -> None:
    """Insert vectors into Qdrant.

    Args:
        kb_id: Knowledge Base UUID.
        documents: Mapping of document name to Document.
        embeddings_data: Loaded embeddings JSON.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
    except ImportError:
        print("  Warning: qdrant-client package not installed, skipping vector insert")
        return

    config = get_qdrant_config()

    client = QdrantClient(host=config["host"], port=config["port"])

    collection_name = f"kb_{kb_id}"

    # Check existing points
    collection_info = client.get_collection(collection_name)
    if collection_info.points_count > 0:
        print(f"  Collection already has {collection_info.points_count} points, skipping insert")
        return

    # Prepare points
    points = []
    for i, chunk in enumerate(embeddings_data["chunks"]):
        doc = documents.get(chunk["document_name"])
        if not doc:
            continue

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["embedding"],
            payload={
                "document_id": str(doc.id),
                "document_name": chunk["document_name"],
                "page_number": None,  # Markdown doesn't have pages
                "section_header": chunk["section_header"],
                "chunk_text": chunk["text"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
            },
        )
        points.append(point)

    # Insert points
    if points:
        client.upsert(collection_name=collection_name, points=points)
        print(f"  Inserted {len(points)} vectors")


async def seed_database(skip_embeddings: bool = False, skip_minio: bool = False) -> None:
    """Main seeding function.

    Args:
        skip_embeddings: Skip Qdrant vector insertion.
        skip_minio: Skip MinIO file upload.
    """
    print("Loading embeddings data...")
    if not EMBEDDINGS_FILE.exists():
        print(f"Error: Embeddings file not found: {EMBEDDINGS_FILE}")
        print("Run generate-embeddings.py first")
        sys.exit(1)

    with EMBEDDINGS_FILE.open() as f:
        embeddings_data = json.load(f)

    print(f"  Loaded {embeddings_data['chunk_count']} chunks from {embeddings_data['document_count']} documents")

    print("\nConnecting to database...")
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        print("\nCreating demo user...")
        user = await get_or_create_demo_user(session)

        print("\nCreating demo Knowledge Base...")
        kb = await get_or_create_demo_kb(session, user)

        print("\nGranting permissions...")
        await grant_demo_permission(session, user, kb)

        print("\nCreating document records...")
        documents = await create_document_records(session, kb, embeddings_data)

        await session.commit()
        print("\nDatabase changes committed")

    # MinIO upload (outside transaction)
    if not skip_minio:
        print("\nUploading to MinIO...")
        try:
            upload_to_minio(kb.id, DEMO_DOCS_DIR)
        except Exception as e:
            print(f"  Warning: MinIO upload failed: {e}")

    # Qdrant operations (outside transaction)
    if not skip_embeddings:
        print("\nSetting up Qdrant collection...")
        try:
            setup_qdrant_collection(kb.id, embeddings_data["dimension"])
        except Exception as e:
            print(f"  Warning: Qdrant setup failed: {e}")

        print("\nInserting vectors...")
        try:
            insert_vectors(kb.id, documents, embeddings_data)
        except Exception as e:
            print(f"  Warning: Vector insert failed: {e}")

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)
    print(f"\nDemo KB ID: {kb.id}")
    print(f"Demo User: {DEMO_USER_EMAIL}")
    print(f"Demo Password: {os.environ.get('DEMO_USER_PASSWORD', DEFAULT_DEMO_PASSWORD)}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed demo Knowledge Base")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip Qdrant vector insertion",
    )
    parser.add_argument(
        "--skip-minio",
        action="store_true",
        help="Skip MinIO file upload",
    )
    args = parser.parse_args()

    asyncio.run(seed_database(
        skip_embeddings=args.skip_embeddings,
        skip_minio=args.skip_minio,
    ))


if __name__ == "__main__":
    main()
