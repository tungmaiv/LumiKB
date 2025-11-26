"""Knowledge Base service for business logic."""

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.outbox import Outbox
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from app.schemas.knowledge_base import KBCreate, KBSummary, KBUpdate
from app.schemas.permission import PermissionResponse
from app.services.audit_service import audit_service

logger = structlog.get_logger(__name__)


# Permission hierarchy: ADMIN > WRITE > READ
PERMISSION_HIERARCHY = {
    PermissionLevel.ADMIN: 3,
    PermissionLevel.WRITE: 2,
    PermissionLevel.READ: 1,
}


class KBService:
    """Service for Knowledge Base operations.

    Handles business logic including permission checks, CRUD operations,
    and coordination with audit logging.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize KBService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def create(self, data: KBCreate, user: User) -> KnowledgeBase:
        """Create a new Knowledge Base.

        Args:
            data: KB creation data (name, description).
            user: The user creating the KB.

        Returns:
            The newly created KnowledgeBase.

        Note:
            - Sets owner_id to the creating user
            - Sets status to 'active'
            - Sets settings to empty dict
            - Creates ADMIN permission for the creator
            - Qdrant collection creation is handled by the API layer
        """
        # Create the KB
        kb = KnowledgeBase(
            name=data.name,
            description=data.description,
            owner_id=user.id,
            status="active",
            settings={},
        )
        self.session.add(kb)
        await self.session.flush()  # Get the ID

        # Grant ADMIN permission to creator (AC2)
        permission = KBPermission(
            user_id=user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.ADMIN,
        )
        self.session.add(permission)

        logger.info(
            "kb_created",
            kb_id=str(kb.id),
            name=kb.name,
            owner_id=str(user.id),
        )

        return kb

    async def get(self, kb_id: UUID, user: User) -> KnowledgeBase | None:
        """Get a Knowledge Base by ID with permission check.

        Args:
            kb_id: The KB UUID.
            user: The user requesting access.

        Returns:
            The KnowledgeBase if user has permission, None otherwise.
            Returns None for non-existent or archived KBs (AC8: return 404, not 403).
        """
        # Get KB (only active ones)
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return None

        # Check permission
        has_access = await self.check_permission(kb_id, user, PermissionLevel.READ)
        if not has_access:
            return None  # AC8: Return None (maps to 404) to not leak existence

        return kb

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[KBSummary], int]:
        """List Knowledge Bases accessible to a user.

        Args:
            user: The user requesting the list.
            page: Page number (1-indexed).
            limit: Number of items per page.

        Returns:
            Tuple of (list of KBSummary, total count).
        """
        offset = (page - 1) * limit

        # Subquery for document counts
        doc_count_subq = (
            select(
                Document.kb_id,
                func.count(Document.id).label("doc_count"),
            )
            .where(Document.status != DocumentStatus.ARCHIVED)
            .group_by(Document.kb_id)
            .subquery()
        )

        # Main query: KBs where user has permission
        query = (
            select(
                KnowledgeBase.id,
                KnowledgeBase.name,
                KnowledgeBase.updated_at,
                KBPermission.permission_level,
                func.coalesce(doc_count_subq.c.doc_count, 0).label("document_count"),
            )
            .join(KBPermission, KnowledgeBase.id == KBPermission.kb_id)
            .outerjoin(doc_count_subq, KnowledgeBase.id == doc_count_subq.c.kb_id)
            .where(
                KBPermission.user_id == user.id,
                KnowledgeBase.status == "active",
            )
            .order_by(KnowledgeBase.updated_at.desc())
        )

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await self.session.execute(query.offset(offset).limit(limit))
        rows = result.all()

        summaries = [
            KBSummary(
                id=row.id,
                name=row.name,
                document_count=row.document_count,
                permission_level=row.permission_level,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

        return summaries, total

    async def update(
        self,
        kb_id: UUID,
        data: KBUpdate,
        user: User,
    ) -> KnowledgeBase | None:
        """Update a Knowledge Base.

        Args:
            kb_id: The KB UUID.
            data: Update data (name and/or description).
            user: The user performing the update.

        Returns:
            The updated KnowledgeBase, or None if not found/no permission.

        Raises:
            PermissionError: If user doesn't have ADMIN permission.
        """
        # Check ADMIN permission (AC4, AC7)
        has_admin = await self.check_permission(kb_id, user, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to update KB")

        # Get KB
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return None

        # Track changes for audit
        changes: dict[str, dict[str, str | None]] = {}

        # Update fields if provided
        if data.name is not None and data.name != kb.name:
            changes["name"] = {"old": kb.name, "new": data.name}
            kb.name = data.name

        if data.description is not None and data.description != kb.description:
            changes["description"] = {"old": kb.description, "new": data.description}
            kb.description = data.description

        if changes:
            # Audit log (AC4)
            await audit_service.log_event(
                action="kb.updated",
                resource_type="knowledge_base",
                user_id=user.id,
                resource_id=kb_id,
                details={"changes": changes},
            )

            logger.info(
                "kb_updated",
                kb_id=str(kb_id),
                changes=list(changes.keys()),
                user_id=str(user.id),
            )

        # Flush to persist changes and refresh to get updated timestamp
        await self.session.flush()
        await self.session.refresh(kb)

        return kb

    async def archive(self, kb_id: UUID, user: User) -> bool:
        """Archive a Knowledge Base (soft delete).

        Args:
            kb_id: The KB UUID.
            user: The user performing the archive.

        Returns:
            True if archived successfully, False if not found.

        Raises:
            PermissionError: If user doesn't have ADMIN permission.
        """
        # Check ADMIN permission (AC5, AC7)
        has_admin = await self.check_permission(kb_id, user, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to archive KB")

        # Get KB
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Set status to archived (AC5)
        kb.status = "archived"

        # Create outbox event for async Qdrant cleanup (AC5)
        outbox_event = Outbox(
            event_type="kb.archived",
            aggregate_id=kb_id,
            aggregate_type="knowledge_base",
            payload={
                "kb_id": str(kb_id),
                "collection_name": f"kb_{kb_id}",
            },
        )
        self.session.add(outbox_event)

        # Audit log (AC5)
        await audit_service.log_event(
            action="kb.archived",
            resource_type="knowledge_base",
            user_id=user.id,
            resource_id=kb_id,
        )

        logger.info(
            "kb_archived",
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return True

    async def check_permission(
        self,
        kb_id: UUID,
        user: User,
        required: PermissionLevel,
    ) -> bool:
        """Check if user has required permission level on a KB.

        Implements permission hierarchy: ADMIN > WRITE > READ.
        AC8: Owner automatically has ADMIN permission (owner bypass).

        Args:
            kb_id: The KB UUID.
            user: The user to check.
            required: The minimum required permission level.

        Returns:
            True if user has sufficient permission, False otherwise.
        """
        # Superusers have full access
        if user.is_superuser:
            return True

        # AC8: Owner bypass - owner has implicit ADMIN permission
        kb_result = await self.session.execute(
            select(KnowledgeBase.owner_id).where(KnowledgeBase.id == kb_id)
        )
        owner_id = kb_result.scalar_one_or_none()
        if owner_id == user.id:
            return True

        # Get user's permission on this KB
        result = await self.session.execute(
            select(KBPermission.permission_level).where(
                KBPermission.kb_id == kb_id,
                KBPermission.user_id == user.id,
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        # Check hierarchy
        user_level = PERMISSION_HIERARCHY.get(permission, 0)
        required_level = PERMISSION_HIERARCHY.get(required, 0)

        return user_level >= required_level

    async def get_user_permission(
        self,
        kb_id: UUID,
        user: User,
    ) -> PermissionLevel | None:
        """Get user's permission level on a KB.

        Args:
            kb_id: The KB UUID.
            user: The user.

        Returns:
            The user's permission level, or None if no permission.
        """
        if user.is_superuser:
            return PermissionLevel.ADMIN

        result = await self.session.execute(
            select(KBPermission.permission_level).where(
                KBPermission.kb_id == kb_id,
                KBPermission.user_id == user.id,
            )
        )
        return result.scalar_one_or_none()

    async def get_document_stats(self, kb_id: UUID) -> tuple[int, int]:
        """Get document statistics for a KB.

        Args:
            kb_id: The KB UUID.

        Returns:
            Tuple of (document_count, total_size_bytes).
        """
        # Count non-archived documents and sum file sizes
        result = await self.session.execute(
            select(
                func.count(Document.id),
                func.coalesce(func.sum(Document.file_size_bytes), 0),
            ).where(
                Document.kb_id == kb_id,
                Document.status != DocumentStatus.ARCHIVED,
                Document.deleted_at.is_(None),
            )
        )
        row = result.one()
        doc_count = row[0] or 0
        total_size = row[1] or 0

        return doc_count, total_size

    async def grant_permission(
        self,
        kb_id: UUID,
        user_id: UUID,
        level: PermissionLevel,
        admin: User,
    ) -> KBPermission:
        """Grant permission to a user on a Knowledge Base.

        AC1: Upsert behavior - updates if permission already exists.
        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            user_id: The user to grant permission to.
            level: The permission level to grant.
            admin: The admin user performing the grant.

        Returns:
            The created or updated KBPermission.

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
            ValueError: If target user doesn't exist.
        """
        # Check admin has ADMIN permission
        has_admin = await self.check_permission(kb_id, admin, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to grant permissions")

        # Verify KB exists and is active
        kb_result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = kb_result.scalar_one_or_none()
        if not kb:
            raise ValueError("Knowledge Base not found")

        # Verify target user exists
        from app.models.user import User as UserModel

        user_result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        target_user = user_result.scalar_one_or_none()
        if not target_user:
            raise ValueError("User not found")

        # Check if permission already exists (upsert behavior)
        existing_result = await self.session.execute(
            select(KBPermission).where(
                KBPermission.kb_id == kb_id,
                KBPermission.user_id == user_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing permission
            old_level = existing.permission_level
            existing.permission_level = level
            permission = existing
            action_detail = f"updated from {old_level.value} to {level.value}"
        else:
            # Create new permission
            permission = KBPermission(
                kb_id=kb_id,
                user_id=user_id,
                permission_level=level,
            )
            self.session.add(permission)
            action_detail = f"granted {level.value}"

        await self.session.flush()

        # Audit log (AC1)
        await audit_service.log_event(
            action="kb.permission_granted",
            resource_type="knowledge_base",
            user_id=admin.id,
            resource_id=kb_id,
            details={
                "target_user_id": str(user_id),
                "permission_level": level.value,
                "action": action_detail,
                "granted_by": str(admin.id),
            },
        )

        logger.info(
            "kb_permission_granted",
            kb_id=str(kb_id),
            target_user_id=str(user_id),
            permission_level=level.value,
            granted_by=str(admin.id),
        )

        return permission

    async def list_permissions(
        self,
        kb_id: UUID,
        admin: User,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[PermissionResponse], int]:
        """List all permissions on a Knowledge Base.

        AC2: Returns paginated list with user email joined.
        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            admin: The admin user requesting the list.
            page: Page number (1-indexed).
            limit: Items per page.

        Returns:
            Tuple of (list of PermissionResponse, total count).

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
        """
        # Check admin has ADMIN permission
        has_admin = await self.check_permission(kb_id, admin, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to list permissions")

        # Verify KB exists
        kb_result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        if not kb_result.scalar_one_or_none():
            raise ValueError("Knowledge Base not found")

        from app.models.user import User as UserModel

        offset = (page - 1) * limit

        # Get total count
        count_result = await self.session.execute(
            select(func.count(KBPermission.id)).where(KBPermission.kb_id == kb_id)
        )
        total = count_result.scalar() or 0

        # Get paginated permissions with user email
        query = (
            select(KBPermission, UserModel.email)
            .join(UserModel, KBPermission.user_id == UserModel.id)
            .where(KBPermission.kb_id == kb_id)
            .order_by(KBPermission.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()

        permissions = [
            PermissionResponse(
                id=row[0].id,
                user_id=row[0].user_id,
                email=row[1],
                kb_id=row[0].kb_id,
                permission_level=row[0].permission_level,
                created_at=row[0].created_at,
            )
            for row in rows
        ]

        return permissions, total

    async def revoke_permission(
        self,
        kb_id: UUID,
        user_id: UUID,
        admin: User,
    ) -> bool:
        """Revoke a user's permission on a Knowledge Base.

        AC3: Removes the permission entry.
        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            user_id: The user whose permission to revoke.
            admin: The admin user performing the revocation.

        Returns:
            True if permission was revoked, False if no permission existed.

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
        """
        # Check admin has ADMIN permission
        has_admin = await self.check_permission(kb_id, admin, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to revoke permissions")

        # Verify KB exists
        kb_result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        if not kb_result.scalar_one_or_none():
            raise ValueError("Knowledge Base not found")

        # Find the permission
        result = await self.session.execute(
            select(KBPermission).where(
                KBPermission.kb_id == kb_id,
                KBPermission.user_id == user_id,
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        # Store level for audit log before deletion
        revoked_level = permission.permission_level

        # Delete the permission
        await self.session.delete(permission)
        await self.session.flush()

        # Audit log (AC3)
        await audit_service.log_event(
            action="kb.permission_revoked",
            resource_type="knowledge_base",
            user_id=admin.id,
            resource_id=kb_id,
            details={
                "target_user_id": str(user_id),
                "revoked_level": revoked_level.value,
                "revoked_by": str(admin.id),
            },
        )

        logger.info(
            "kb_permission_revoked",
            kb_id=str(kb_id),
            target_user_id=str(user_id),
            revoked_level=revoked_level.value,
            revoked_by=str(admin.id),
        )

        return True


class KBPermissionService:
    """Service for KB permission checks used by search and other services."""

    def __init__(self, session: AsyncSession):
        """Initialize permission service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def get_permitted_kb_ids(
        self,
        user_id: str,
        permission_level: str = "READ",  # noqa: ARG002 - Reserved for future permission filtering
    ) -> list[str]:
        """Get list of KB IDs the user has access to.

        Args:
            user_id: User ID (string)
            permission_level: Minimum permission level required

        Returns:
            List of KB IDs as strings
        """
        from app.models.user import User as UserModel

        # Get user
        user_result = await self.session.execute(
            select(UserModel).where(UserModel.id == UUID(user_id))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        # Superusers have access to all KBs
        if user.is_superuser:
            result = await self.session.execute(
                select(KnowledgeBase.id).where(KnowledgeBase.status == "active")
            )
            return [str(kb_id) for kb_id in result.scalars().all()]

        # Get KBs where user has permission
        result = await self.session.execute(
            select(KnowledgeBase.id)
            .join(KBPermission, KnowledgeBase.id == KBPermission.kb_id)
            .where(
                KBPermission.user_id == UUID(user_id),
                KnowledgeBase.status == "active",
            )
        )
        kb_ids = result.scalars().all()

        # Also include KBs where user is owner (implicit ADMIN)
        owner_result = await self.session.execute(
            select(KnowledgeBase.id).where(
                KnowledgeBase.owner_id == UUID(user_id),
                KnowledgeBase.status == "active",
            )
        )
        owner_kb_ids = owner_result.scalars().all()

        # Combine and deduplicate
        all_kb_ids = set(kb_ids) | set(owner_kb_ids)

        return [str(kb_id) for kb_id in all_kb_ids]

    async def check_permission(
        self, user_id: str, kb_id: str, permission_level: str = "READ"
    ) -> bool:
        """Check if user has permission on a KB.

        Args:
            user_id: User ID (string)
            kb_id: KB ID (string)
            permission_level: Required permission level

        Returns:
            True if user has permission, False otherwise
        """
        from app.models.user import User as UserModel

        # Get user
        user_result = await self.session.execute(
            select(UserModel).where(UserModel.id == UUID(user_id))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return False

        # Map string to PermissionLevel
        perm_map = {
            "READ": PermissionLevel.READ,
            "WRITE": PermissionLevel.WRITE,
            "ADMIN": PermissionLevel.ADMIN,
        }
        required = perm_map.get(permission_level, PermissionLevel.READ)

        # Use KBService check_permission
        kb_service = KBService(self.session)
        return await kb_service.check_permission(UUID(kb_id), user, required)


def get_kb_permission_service(
    session: AsyncSession = None,
) -> KBPermissionService:
    """Dependency injection for KBPermissionService.

    Note:
        For use with FastAPI Depends. Session must be provided via Depends(get_db).
    """
    if session is None:
        raise RuntimeError(
            "get_kb_permission_service requires session via Depends(get_db)"
        )
    return KBPermissionService(session)
