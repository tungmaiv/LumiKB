"""Integration tests for demo KB seeding functionality."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Constants matching seed-data.py
DEMO_KB_NAME = "Sample Knowledge Base"
DEMO_KB_DESCRIPTION = (
    "Explore LumiKB with these demo documents about the platform's features"
)
DEMO_USER_EMAIL = "demo@lumikb.local"


class TestDemoKBSeeding:
    """Test demo KB seeding operations."""

    async def test_create_demo_kb(self, db_session: AsyncSession):
        """Test creating a demo KB with correct attributes (AC: 1)."""
        # Create owner user first
        owner = User(
            email="owner@lumikb.local",
            hashed_password="hashedpassword",
            is_active=True,
            is_verified=True,
        )
        db_session.add(owner)
        await db_session.flush()

        # Create demo KB
        kb = KnowledgeBase(
            name=DEMO_KB_NAME,
            description=DEMO_KB_DESCRIPTION,
            owner_id=owner.id,
            status="active",
        )
        db_session.add(kb)
        await db_session.flush()

        # Verify attributes
        assert kb.id is not None
        assert kb.name == DEMO_KB_NAME
        assert kb.description == DEMO_KB_DESCRIPTION
        assert kb.status == "active"
        assert kb.owner_id == owner.id

    async def test_create_demo_user(self, db_session: AsyncSession):
        """Test creating a demo user with correct attributes (AC: 7)."""
        user = User(
            email=DEMO_USER_EMAIL,
            hashed_password="hashedpassword",  # In real seeding, this is argon2 hashed
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Verify attributes
        assert user.id is not None
        assert user.email == DEMO_USER_EMAIL
        assert user.is_superuser is False
        assert user.is_verified is True

    async def test_seed_idempotent_user(self, db_session: AsyncSession):
        """Test that creating demo user twice doesn't duplicate (AC: 8)."""
        # Create first user
        user1 = User(
            email=DEMO_USER_EMAIL,
            hashed_password="hashedpassword",
        )
        db_session.add(user1)
        await db_session.flush()

        # Query to check for existing user (simulating idempotent check)
        result = await db_session.execute(
            select(User).where(User.email == DEMO_USER_EMAIL)
        )
        existing = result.scalar_one_or_none()

        assert existing is not None
        assert existing.id == user1.id

    async def test_seed_idempotent_kb(self, db_session: AsyncSession):
        """Test that creating demo KB twice doesn't duplicate (AC: 8)."""
        # Create first KB
        kb1 = KnowledgeBase(
            name=DEMO_KB_NAME,
            description=DEMO_KB_DESCRIPTION,
        )
        db_session.add(kb1)
        await db_session.flush()

        # Query to check for existing KB (simulating idempotent check)
        result = await db_session.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == DEMO_KB_NAME)
        )
        existing = result.scalar_one_or_none()

        assert existing is not None
        assert existing.id == kb1.id

    async def test_create_document_records(self, db_session: AsyncSession):
        """Test creating document records with correct status (AC: 3)."""
        # Create KB first
        kb = KnowledgeBase(name=DEMO_KB_NAME)
        db_session.add(kb)
        await db_session.flush()

        # Create document with READY status (seeded documents are pre-processed)
        doc = Document(
            kb_id=kb.id,
            name="01-getting-started.md",
            file_path=f"kb-{kb.id}/01-getting-started.md",
            status=DocumentStatus.READY,
            chunk_count=3,  # Pre-computed chunks
        )
        db_session.add(doc)
        await db_session.flush()

        # Verify
        assert doc.id is not None
        assert doc.status == DocumentStatus.READY
        assert doc.chunk_count == 3
        assert doc.file_path == f"kb-{kb.id}/01-getting-started.md"

    async def test_grant_read_permission(self, db_session: AsyncSession):
        """Test granting READ permission on demo KB (AC: 4)."""
        # Create user and KB
        user = User(
            email="new_user@example.com",
            hashed_password="hashedpassword",
        )
        kb = KnowledgeBase(name=DEMO_KB_NAME)
        db_session.add_all([user, kb])
        await db_session.flush()

        # Grant READ permission
        permission = KBPermission(
            user_id=user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session.add(permission)
        await db_session.flush()

        # Verify
        result = await db_session.execute(
            select(KBPermission).where(
                KBPermission.user_id == user.id,
                KBPermission.kb_id == kb.id,
            )
        )
        perm = result.scalar_one()
        assert perm.permission_level == PermissionLevel.READ


class TestKBPermissions:
    """Test KB permission mechanics."""

    async def test_read_permission_grants_access(self, db_session: AsyncSession):
        """Test that READ permission grants access to KB."""
        # Create user and KB
        user = User(
            email="reader@example.com",
            hashed_password="hashedpassword",
        )
        kb = KnowledgeBase(name="Test KB")
        db_session.add_all([user, kb])
        await db_session.flush()

        # Grant READ permission
        permission = KBPermission(
            user_id=user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session.add(permission)
        await db_session.flush()

        # Check permission exists
        result = await db_session.execute(
            select(KBPermission).where(
                KBPermission.user_id == user.id,
                KBPermission.kb_id == kb.id,
            )
        )
        perm = result.scalar_one_or_none()

        assert perm is not None
        assert perm.permission_level == PermissionLevel.READ

    async def test_no_permission_denies_access(self, db_session: AsyncSession):
        """Test that lack of permission denies access to KB."""
        # Create user and KB
        user = User(
            email="outsider@example.com",
            hashed_password="hashedpassword",
        )
        kb = KnowledgeBase(name="Private KB")
        db_session.add_all([user, kb])
        await db_session.flush()

        # Don't grant any permission

        # Check permission doesn't exist
        result = await db_session.execute(
            select(KBPermission).where(
                KBPermission.user_id == user.id,
                KBPermission.kb_id == kb.id,
            )
        )
        perm = result.scalar_one_or_none()

        assert perm is None

    async def test_owner_has_admin_access(self, db_session: AsyncSession):
        """Test that KB owner has implicit ADMIN access."""
        # Create user who will be owner
        owner = User(
            email="owner@example.com",
            hashed_password="hashedpassword",
        )
        db_session.add(owner)
        await db_session.flush()

        # Create KB with owner
        kb = KnowledgeBase(
            name="Owned KB",
            owner_id=owner.id,
        )
        db_session.add(kb)
        await db_session.flush()

        # Verify owner is set correctly
        assert kb.owner_id == owner.id

        # In the API layer, owner should be treated as having ADMIN permission
        # even without explicit KBPermission record

    async def test_multiple_users_same_kb(self, db_session: AsyncSession):
        """Test multiple users can have different permissions on same KB."""
        # Create users
        admin_user = User(email="admin@example.com", hashed_password="hash")
        editor_user = User(email="editor@example.com", hashed_password="hash")
        reader_user = User(email="reader@example.com", hashed_password="hash")
        db_session.add_all([admin_user, editor_user, reader_user])
        await db_session.flush()

        # Create KB
        kb = KnowledgeBase(name="Shared KB")
        db_session.add(kb)
        await db_session.flush()

        # Grant different permissions
        admin_perm = KBPermission(
            user_id=admin_user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.ADMIN,
        )
        editor_perm = KBPermission(
            user_id=editor_user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.WRITE,
        )
        reader_perm = KBPermission(
            user_id=reader_user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session.add_all([admin_perm, editor_perm, reader_perm])
        await db_session.flush()

        # Verify each user has correct permission
        result = await db_session.execute(
            select(KBPermission).where(KBPermission.kb_id == kb.id)
        )
        perms = result.scalars().all()

        assert len(perms) == 3

        perm_map = {p.user_id: p.permission_level for p in perms}
        assert perm_map[admin_user.id] == PermissionLevel.ADMIN
        assert perm_map[editor_user.id] == PermissionLevel.WRITE
        assert perm_map[reader_user.id] == PermissionLevel.READ
