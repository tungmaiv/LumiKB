"""Database integration tests."""

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditEvent,
    Document,
    DocumentStatus,
    KBPermission,
    KnowledgeBase,
    Outbox,
    PermissionLevel,
    User,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestDatabaseSchema:
    """Test database schema and tables."""

    async def test_users_table_exists(self, db_session: AsyncSession):
        """Test that users table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
                """
            )
        )
        columns = {row[0]: {"data_type": row[1], "nullable": row[2]} for row in result}

        assert "id" in columns
        assert "email" in columns
        assert "hashed_password" in columns
        assert "is_active" in columns
        assert "is_superuser" in columns
        assert "is_verified" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    async def test_knowledge_bases_table_exists(self, db_session: AsyncSession):
        """Test that knowledge_bases table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'knowledge_bases'
                """
            )
        )
        columns = {row[0] for row in result}

        assert "id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "owner_id" in columns
        assert "status" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    async def test_documents_table_exists(self, db_session: AsyncSession):
        """Test that documents table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'documents'
                """
            )
        )
        columns = {row[0] for row in result}

        assert "id" in columns
        assert "kb_id" in columns
        assert "name" in columns
        assert "file_path" in columns
        assert "status" in columns
        assert "chunk_count" in columns
        assert "last_error" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    async def test_kb_permissions_table_exists(self, db_session: AsyncSession):
        """Test that kb_permissions table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'kb_permissions'
                """
            )
        )
        columns = {row[0] for row in result}

        assert "id" in columns
        assert "user_id" in columns
        assert "kb_id" in columns
        assert "permission_level" in columns
        assert "created_at" in columns

    async def test_outbox_table_exists(self, db_session: AsyncSession):
        """Test that outbox table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'outbox'
                """
            )
        )
        columns = {row[0] for row in result}

        assert "id" in columns
        assert "event_type" in columns
        assert "aggregate_id" in columns
        assert "payload" in columns
        assert "created_at" in columns
        assert "processed_at" in columns
        assert "attempts" in columns
        assert "last_error" in columns

    async def test_audit_events_table_exists(self, db_session: AsyncSession):
        """Test that audit.events table exists with correct columns."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'audit' AND table_name = 'events'
                """
            )
        )
        columns = {row[0] for row in result}

        assert "id" in columns
        assert "timestamp" in columns
        assert "user_id" in columns
        assert "action" in columns
        assert "resource_type" in columns
        assert "resource_id" in columns
        assert "details" in columns
        assert "ip_address" in columns


class TestModelOperations:
    """Test CRUD operations on models."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashedpassword123",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        db_session.add(user)
        await db_session.flush()

        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_create_knowledge_base(self, db_session: AsyncSession):
        """Test creating a knowledge base."""
        kb = KnowledgeBase(
            name="Test KB",
            description="A test knowledge base",
        )
        db_session.add(kb)
        await db_session.flush()

        assert kb.id is not None
        assert kb.status == "active"

    async def test_create_document(self, db_session: AsyncSession):
        """Test creating a document."""
        kb = KnowledgeBase(name="Test KB")
        db_session.add(kb)
        await db_session.flush()

        doc = Document(
            kb_id=kb.id,
            name="test.pdf",
            file_path="/uploads/test.pdf",
            status=DocumentStatus.PENDING,
        )
        db_session.add(doc)
        await db_session.flush()

        assert doc.id is not None
        assert doc.chunk_count == 0

    async def test_create_kb_permission(self, db_session: AsyncSession):
        """Test creating a KB permission."""
        user = User(
            email="perm@example.com",
            hashed_password="hashedpassword",
        )
        kb = KnowledgeBase(name="Test KB")
        db_session.add_all([user, kb])
        await db_session.flush()

        perm = KBPermission(
            user_id=user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session.add(perm)
        await db_session.flush()

        assert perm.id is not None

    async def test_create_outbox_event(self, db_session: AsyncSession):
        """Test creating an outbox event."""
        event = Outbox(
            event_type="document.uploaded",
            aggregate_id=uuid.uuid4(),
            payload={"filename": "test.pdf", "size": 1024},
        )
        db_session.add(event)
        await db_session.flush()

        assert event.id is not None
        assert event.processed_at is None
        assert event.attempts == 0

    async def test_create_audit_event(self, db_session: AsyncSession):
        """Test creating an audit event."""
        audit = AuditEvent(
            user_id=uuid.uuid4(),
            action="user.login",
            resource_type="user",
            resource_id=uuid.uuid4(),
            details={"ip": "192.168.1.1"},
            ip_address="192.168.1.1",
        )
        db_session.add(audit)
        await db_session.flush()

        assert audit.id is not None
        assert audit.timestamp is not None


class TestForeignKeyConstraints:
    """Test foreign key constraints."""

    async def test_document_kb_foreign_key(self, db_session: AsyncSession):
        """Test that documents require valid kb_id."""
        kb = KnowledgeBase(name="Test KB")
        db_session.add(kb)
        await db_session.flush()

        doc = Document(
            kb_id=kb.id,
            name="test.pdf",
        )
        db_session.add(doc)
        await db_session.flush()

        # Verify the relationship works
        result = await db_session.execute(
            select(Document).where(Document.kb_id == kb.id)
        )
        fetched_doc = result.scalar_one()
        assert fetched_doc.id == doc.id

    async def test_kb_permission_cascade_delete(self, db_session: AsyncSession):
        """Test that KB permissions cascade on KB delete."""
        user = User(email="cascade@test.com", hashed_password="hash")
        kb = KnowledgeBase(name="Delete Test KB")
        db_session.add_all([user, kb])
        await db_session.flush()

        perm = KBPermission(
            user_id=user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.ADMIN,
        )
        db_session.add(perm)
        await db_session.flush()

        perm_id = perm.id

        # Delete the KB
        await db_session.delete(kb)
        await db_session.flush()

        # Permission should be deleted too
        result = await db_session.execute(
            select(KBPermission).where(KBPermission.id == perm_id)
        )
        assert result.scalar_one_or_none() is None
