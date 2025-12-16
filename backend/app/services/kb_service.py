"""Knowledge Base service for business logic."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.group import Group, UserGroup
from app.models.kb_group_permission import KBGroupPermission
from app.models.knowledge_base import KnowledgeBase
from app.models.llm_model import LLMModel, ModelStatus, ModelType
from app.models.outbox import Outbox
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from app.schemas.knowledge_base import KBCreate, KBSummary, KBUpdate
from app.schemas.permission import (
    EffectivePermission,
    PermissionResponse,
    PermissionResponseExtended,
    PermissionSource,
)
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

    async def create(
        self,
        data: KBCreate,
        user: User,
        create_qdrant_collection: bool = True,
    ) -> KnowledgeBase:
        """Create a new Knowledge Base.

        Args:
            data: KB creation data (name, description, model IDs, RAG params).
            user: The user creating the KB.
            create_qdrant_collection: Whether to create Qdrant collection (default True).
                Set to False for testing without Qdrant.

        Returns:
            The newly created KnowledgeBase.

        Raises:
            ValueError: If model_id references inactive/non-existent model or wrong type.

        Note:
            - Sets owner_id to the creating user
            - Sets status to 'active'
            - Sets settings to empty dict
            - Creates ADMIN permission for the creator
            - Validates model IDs reference active models of correct type
            - Creates Qdrant collection with embedding model dimensions (AC-7.10.4)
        """
        # Validate embedding model if provided (AC-7.10.2)
        embedding_model: LLMModel | None = None
        if data.embedding_model_id:
            embedding_model = await self._validate_model(
                data.embedding_model_id,
                ModelType.EMBEDDING,
                "Embedding model",
            )

        # Validate generation model if provided (AC-7.10.2)
        if data.generation_model_id:
            await self._validate_model(
                data.generation_model_id,
                ModelType.GENERATION,
                "Generation model",
            )

        # Create the KB
        kb = KnowledgeBase(
            name=data.name,
            description=data.description,
            tags=data.tags or [],
            owner_id=user.id,
            status="active",
            settings={},
            embedding_model_id=data.embedding_model_id,
            generation_model_id=data.generation_model_id,
            similarity_threshold=data.similarity_threshold,
            search_top_k=data.search_top_k,
            temperature=data.temperature,
            rerank_enabled=data.rerank_enabled,
        )
        self.session.add(kb)
        await self.session.flush()  # Get the ID

        # Set Qdrant collection name (always set for consistency)
        kb.qdrant_collection_name = f"kb_{kb.id}"

        # Set vector size from embedding model config (AC-7.10.4)
        if embedding_model and embedding_model.config:
            kb.qdrant_vector_size = embedding_model.config.get("dimensions")

        # Create Qdrant collection with correct dimensions (AC-7.10.4)
        if create_qdrant_collection and embedding_model:
            await self._create_qdrant_collection(kb, embedding_model)

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
            embedding_model_id=str(data.embedding_model_id)
            if data.embedding_model_id
            else None,
            generation_model_id=str(data.generation_model_id)
            if data.generation_model_id
            else None,
            qdrant_collection=kb.qdrant_collection_name,
            vector_size=kb.qdrant_vector_size,
        )

        return kb

    async def _validate_model(
        self,
        model_id: UUID,
        expected_type: ModelType,
        model_label: str,
    ) -> LLMModel:
        """Validate that a model ID references an active model of correct type.

        Args:
            model_id: The model UUID to validate.
            expected_type: Expected ModelType (EMBEDDING or GENERATION).
            model_label: Human-readable label for error messages.

        Returns:
            The validated LLMModel.

        Raises:
            ValueError: If model not found, inactive, or wrong type.
        """
        result = await self.session.execute(
            select(LLMModel).where(LLMModel.id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"{model_label} not found: {model_id}")

        if model.status != ModelStatus.ACTIVE.value:
            raise ValueError(f"{model_label} is not active (status: {model.status})")

        if model.type != expected_type.value:
            raise ValueError(
                f"{model_label} has wrong type: expected {expected_type.value}, "
                f"got {model.type}"
            )

        return model

    async def _create_qdrant_collection(
        self,
        kb: KnowledgeBase,
        embedding_model: LLMModel,
    ) -> None:
        """Create Qdrant collection with embedding model configuration.

        Args:
            kb: The KnowledgeBase to create collection for.
            embedding_model: The embedding model with dimension config.

        Note:
            Uses dimensions and distance_metric from embedding model config.
        """
        from app.integrations.qdrant_client import qdrant_service

        dimensions = embedding_model.config.get("dimensions", 768)
        distance_metric = embedding_model.config.get("distance_metric", "cosine")

        try:
            await qdrant_service.create_collection_for_kb(
                kb_id=kb.id,
                vector_size=dimensions,
                distance_metric=distance_metric,
            )
            logger.info(
                "qdrant_collection_created_for_kb",
                kb_id=str(kb.id),
                collection_name=kb.qdrant_collection_name,
                vector_size=dimensions,
                distance_metric=distance_metric,
            )
        except Exception as e:
            logger.error(
                "qdrant_collection_creation_failed",
                kb_id=str(kb.id),
                error=str(e),
            )
            raise

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
        include_archived: bool = False,
    ) -> tuple[list[KBSummary], int]:
        """List Knowledge Bases accessible to a user.

        Args:
            user: The user requesting the list.
            page: Page number (1-indexed).
            limit: Number of items per page.
            include_archived: If True, include archived KBs in the results.

        Returns:
            Tuple of (list of KBSummary, total count).

        Story 7-26 (AC-7.26.5): Supports include_archived flag to show archived KBs
        with their archived_at timestamp for display in the sidebar filter.
        """
        offset = (page - 1) * limit

        # Subquery for document counts
        # Only count non-archived, non-deleted documents to match document list filtering
        doc_count_subq = (
            select(
                Document.kb_id,
                func.count(Document.id).label("doc_count"),
            )
            .where(
                Document.status != DocumentStatus.ARCHIVED,
                Document.deleted_at.is_(None),
            )
            .group_by(Document.kb_id)
            .subquery()
        )

        # Main query: KBs where user has permission
        # Story 7-10: Include model IDs for KB Settings modal
        # Story 7-26: Include archived_at for archived KB display
        query = (
            select(
                KnowledgeBase.id,
                KnowledgeBase.name,
                KnowledgeBase.tags,
                KnowledgeBase.updated_at,
                KnowledgeBase.archived_at,
                KnowledgeBase.embedding_model_id,
                KnowledgeBase.generation_model_id,
                KBPermission.permission_level,
                func.coalesce(doc_count_subq.c.doc_count, 0).label("document_count"),
            )
            .join(KBPermission, KnowledgeBase.id == KBPermission.kb_id)
            .outerjoin(doc_count_subq, KnowledgeBase.id == doc_count_subq.c.kb_id)
            .where(KBPermission.user_id == user.id)
        )

        # Story 7-26: Filter by status based on include_archived flag
        if include_archived:
            # Include both active and archived KBs
            query = query.where(KnowledgeBase.status.in_(["active", "archived"]))
        else:
            # Only include active KBs
            query = query.where(KnowledgeBase.status == "active")

        query = query.order_by(KnowledgeBase.updated_at.desc())

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
                tags=row.tags or [],
                # Story 7-26: Include archived_at for archived KB display
                archived_at=row.archived_at,
                # Story 7-10: Include model IDs and lock status for KB Settings
                embedding_model_id=row.embedding_model_id,
                generation_model_id=row.generation_model_id,
                embedding_model_locked=row.document_count > 0,
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
            data: Update data (name, description, model IDs, RAG params).
            user: The user performing the update.

        Returns:
            The updated KnowledgeBase, or None if not found/no permission.

        Raises:
            PermissionError: If user doesn't have ADMIN permission.
            ValueError: If embedding model change is attempted when KB has documents,
                       or if model validation fails.

        Story 7-10: Model Configuration Updates
        - AC-7.10.5: Embedding model locked after first document
        - AC-7.10.6: Generation model always changeable
        - AC-7.10.7: RAG parameters always updatable
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
        changes: dict[str, dict[str, str | list[str] | None]] = {}

        # Update fields if provided
        if data.name is not None and data.name != kb.name:
            changes["name"] = {"old": kb.name, "new": data.name}
            kb.name = data.name

        if data.description is not None and data.description != kb.description:
            changes["description"] = {"old": kb.description, "new": data.description}
            kb.description = data.description

        if data.tags is not None and data.tags != kb.tags:
            changes["tags"] = {"old": kb.tags, "new": data.tags}
            kb.tags = data.tags

        # Story 7-10: Model configuration updates
        # AC-7.10.5: Embedding model locked after first document
        if data.embedding_model_id is not None:
            # Check if embedding model is locked (has documents)
            doc_count, _ = await self.get_document_stats(kb_id)
            if doc_count > 0 and data.embedding_model_id != kb.embedding_model_id:
                raise ValueError(
                    "Embedding model is locked: KB has processed documents. "
                    "Changing the embedding model would invalidate existing vectors."
                )

            # Validate new embedding model
            if data.embedding_model_id != kb.embedding_model_id:
                embedding_model = await self._validate_model(
                    data.embedding_model_id,
                    ModelType.EMBEDDING,
                    "Embedding model",
                )
                changes["embedding_model_id"] = {
                    "old": str(kb.embedding_model_id)
                    if kb.embedding_model_id
                    else None,
                    "new": str(data.embedding_model_id),
                }
                kb.embedding_model_id = data.embedding_model_id
                # Update Qdrant vector size from new model
                if embedding_model.config:
                    kb.qdrant_vector_size = embedding_model.config.get("dimensions")

        # AC-7.10.6: Generation model can be changed anytime
        if (
            data.generation_model_id is not None
            and data.generation_model_id != kb.generation_model_id
        ):
            await self._validate_model(
                data.generation_model_id,
                ModelType.GENERATION,
                "Generation model",
            )
            changes["generation_model_id"] = {
                "old": str(kb.generation_model_id) if kb.generation_model_id else None,
                "new": str(data.generation_model_id),
            }
            kb.generation_model_id = data.generation_model_id

        # AC-7.10.7: RAG parameters can be updated anytime
        if (
            data.similarity_threshold is not None
            and data.similarity_threshold != kb.similarity_threshold
        ):
            changes["similarity_threshold"] = {
                "old": str(kb.similarity_threshold)
                if kb.similarity_threshold
                else None,
                "new": str(data.similarity_threshold),
            }
            kb.similarity_threshold = data.similarity_threshold

        if data.search_top_k is not None and data.search_top_k != kb.search_top_k:
            changes["search_top_k"] = {
                "old": str(kb.search_top_k) if kb.search_top_k else None,
                "new": str(data.search_top_k),
            }
            kb.search_top_k = data.search_top_k

        if data.temperature is not None and data.temperature != kb.temperature:
            changes["temperature"] = {
                "old": str(kb.temperature) if kb.temperature else None,
                "new": str(data.temperature),
            }
            kb.temperature = data.temperature

        if data.rerank_enabled is not None and data.rerank_enabled != kb.rerank_enabled:
            changes["rerank_enabled"] = {
                "old": str(kb.rerank_enabled)
                if kb.rerank_enabled is not None
                else None,
                "new": str(data.rerank_enabled),
            }
            kb.rerank_enabled = data.rerank_enabled

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
        """Archive a Knowledge Base with cascade to documents.

        Story 7-24: KB Archive Backend
        - Sets KB.archived_at timestamp
        - Sets KB.status to 'archived'
        - Cascades to all documents (sets document.archived_at)
        - Creates outbox event for Qdrant payload updates (is_archived: true)

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

        now = datetime.now(UTC)

        # Set KB as archived with timestamp (Story 7-24)
        kb.status = "archived"
        kb.archived_at = now

        # Cascade archive to all documents (Story 7-24 AC1)
        # Set archived_at on all non-archived documents
        await self.session.execute(
            update(Document)
            .where(
                Document.kb_id == kb_id,
                Document.archived_at.is_(None),
            )
            .values(archived_at=now)
        )

        # Count affected documents for logging
        doc_count_result = await self.session.execute(
            select(func.count(Document.id)).where(Document.kb_id == kb_id)
        )
        doc_count = doc_count_result.scalar() or 0

        # Create outbox event for async Qdrant payload updates (Story 7-24 AC2)
        # This will update all document vectors with is_archived: true
        outbox_event = Outbox(
            event_type="kb.archive",
            aggregate_id=kb_id,
            aggregate_type="knowledge_base",
            payload={
                "kb_id": str(kb_id),
                "collection_name": kb.qdrant_collection_name or f"kb_{kb_id}",
                "archived_at": now.isoformat(),
                "is_archived": True,
            },
        )
        self.session.add(outbox_event)

        # Audit log (AC5)
        await audit_service.log_event(
            action="kb.archived",
            resource_type="knowledge_base",
            user_id=user.id,
            resource_id=kb_id,
            details={
                "archived_at": now.isoformat(),
                "documents_archived": doc_count,
            },
        )

        logger.info(
            "kb_archived",
            kb_id=str(kb_id),
            user_id=str(user.id),
            archived_at=now.isoformat(),
            documents_archived=doc_count,
        )

        return True

    async def restore(self, kb_id: UUID, user: User) -> bool:
        """Restore an archived Knowledge Base.

        Story 7-25: KB Restore Backend
        - Clears KB.archived_at
        - Sets KB.status to 'active'
        - Clears document.archived_at for all documents
        - Creates outbox event for Qdrant payload updates (is_archived: false)

        Args:
            kb_id: The KB UUID.
            user: The user performing the restore.

        Returns:
            True if restored successfully, False if not found.

        Raises:
            PermissionError: If user doesn't have ADMIN permission.
        """
        # Check ADMIN permission
        has_admin = await self.check_permission(kb_id, user, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to restore KB")

        # Get archived KB
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "archived",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Clear archive status (Story 7-25)
        kb.status = "active"
        kb.archived_at = None

        # Cascade restore to all documents (Story 7-25 AC1)
        # Clear archived_at on all documents that were archived with the KB
        await self.session.execute(
            update(Document)
            .where(
                Document.kb_id == kb_id,
                Document.archived_at.isnot(None),
            )
            .values(archived_at=None)
        )

        # Count affected documents for logging
        doc_count_result = await self.session.execute(
            select(func.count(Document.id)).where(Document.kb_id == kb_id)
        )
        doc_count = doc_count_result.scalar() or 0

        # Create outbox event for async Qdrant payload updates (Story 7-25 AC2)
        # This will update all document vectors with is_archived: false
        outbox_event = Outbox(
            event_type="kb.restore",
            aggregate_id=kb_id,
            aggregate_type="knowledge_base",
            payload={
                "kb_id": str(kb_id),
                "collection_name": kb.qdrant_collection_name or f"kb_{kb_id}",
                "is_archived": False,
            },
        )
        self.session.add(outbox_event)

        # Audit log
        await audit_service.log_event(
            action="kb.restored",
            resource_type="knowledge_base",
            user_id=user.id,
            resource_id=kb_id,
            details={
                "documents_restored": doc_count,
            },
        )

        logger.info(
            "kb_restored",
            kb_id=str(kb_id),
            user_id=str(user.id),
            documents_restored=doc_count,
        )

        return True

    async def hard_delete(self, kb_id: UUID, user: User) -> bool:
        """Permanently delete a Knowledge Base (hard delete).

        Story 7-24: Modified DELETE behavior
        - Only permitted for KBs with 0 documents
        - Performs hard delete of KB record
        - Creates outbox event to delete Qdrant collection

        Args:
            kb_id: The KB UUID.
            user: The user performing the delete.

        Returns:
            True if deleted successfully, False if not found.

        Raises:
            PermissionError: If user doesn't have ADMIN permission.
            ValueError: If KB has documents (must be empty to delete).
        """
        # Check ADMIN permission
        has_admin = await self.check_permission(kb_id, user, PermissionLevel.ADMIN)
        if not has_admin:
            raise PermissionError("ADMIN permission required to delete KB")

        # Get KB (can be active or archived)
        result = await self.session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Check document count - must be 0 to delete (Story 7-24 AC3)
        doc_count_result = await self.session.execute(
            select(func.count(Document.id)).where(Document.kb_id == kb_id)
        )
        doc_count = doc_count_result.scalar() or 0

        if doc_count > 0:
            raise ValueError(
                f"Cannot delete KB with {doc_count} documents. "
                "Archive documents first or use archive KB instead."
            )

        collection_name = kb.qdrant_collection_name or f"kb_{kb_id}"

        # Create outbox event for Qdrant collection deletion (Story 7-24 AC4)
        outbox_event = Outbox(
            event_type="kb.delete",
            aggregate_id=kb_id,
            aggregate_type="knowledge_base",
            payload={
                "kb_id": str(kb_id),
                "collection_name": collection_name,
            },
        )
        self.session.add(outbox_event)

        # Delete the KB record (cascade will delete permissions, drafts, etc.)
        await self.session.delete(kb)

        # Audit log
        await audit_service.log_event(
            action="kb.deleted",
            resource_type="knowledge_base",
            user_id=user.id,
            resource_id=kb_id,
            details={
                "collection_name": collection_name,
                "hard_delete": True,
            },
        )

        logger.info(
            "kb_deleted",
            kb_id=str(kb_id),
            user_id=str(user.id),
            collection_name=collection_name,
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

    # =========================================================================
    # Group Permission Methods (Story 5-20)
    # =========================================================================

    async def grant_group_permission(
        self,
        kb_id: UUID,
        group_id: UUID,
        level: PermissionLevel,
        admin: User,
    ) -> KBGroupPermission:
        """Grant permission to a group on a Knowledge Base.

        Upsert behavior - updates if permission already exists.
        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            group_id: The group to grant permission to.
            level: The permission level to grant.
            admin: The admin user performing the grant.

        Returns:
            The created or updated KBGroupPermission.

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
            ValueError: If KB or group doesn't exist.
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

        # Verify target group exists and is active
        group_result = await self.session.execute(
            select(Group).where(
                Group.id == group_id,
                Group.is_active.is_(True),
            )
        )
        target_group = group_result.scalar_one_or_none()
        if not target_group:
            raise ValueError("Group not found")

        # Check if permission already exists (upsert behavior)
        existing_result = await self.session.execute(
            select(KBGroupPermission).where(
                KBGroupPermission.kb_id == kb_id,
                KBGroupPermission.group_id == group_id,
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
            permission = KBGroupPermission(
                kb_id=kb_id,
                group_id=group_id,
                permission_level=level,
            )
            self.session.add(permission)
            action_detail = f"granted {level.value}"

        await self.session.flush()

        # Audit log
        await audit_service.log_event(
            action="kb.group_permission_granted",
            resource_type="knowledge_base",
            user_id=admin.id,
            resource_id=kb_id,
            details={
                "target_group_id": str(group_id),
                "group_name": target_group.name,
                "permission_level": level.value,
                "action": action_detail,
                "granted_by": str(admin.id),
            },
        )

        logger.info(
            "kb_group_permission_granted",
            kb_id=str(kb_id),
            target_group_id=str(group_id),
            permission_level=level.value,
            granted_by=str(admin.id),
        )

        return permission

    async def revoke_group_permission(
        self,
        kb_id: UUID,
        group_id: UUID,
        admin: User,
    ) -> bool:
        """Revoke a group's permission on a Knowledge Base.

        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            group_id: The group whose permission to revoke.
            admin: The admin user performing the revocation.

        Returns:
            True if permission was revoked, False if no permission existed.

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
            ValueError: If KB doesn't exist.
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
            select(KBGroupPermission).where(
                KBGroupPermission.kb_id == kb_id,
                KBGroupPermission.group_id == group_id,
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        # Get group name for audit log
        group_result = await self.session.execute(
            select(Group.name).where(Group.id == group_id)
        )
        group_name = group_result.scalar_one_or_none() or "unknown"

        # Store level for audit log before deletion
        revoked_level = permission.permission_level

        # Delete the permission
        await self.session.delete(permission)
        await self.session.flush()

        # Audit log
        await audit_service.log_event(
            action="kb.group_permission_revoked",
            resource_type="knowledge_base",
            user_id=admin.id,
            resource_id=kb_id,
            details={
                "target_group_id": str(group_id),
                "group_name": group_name,
                "revoked_level": revoked_level.value,
                "revoked_by": str(admin.id),
            },
        )

        logger.info(
            "kb_group_permission_revoked",
            kb_id=str(kb_id),
            target_group_id=str(group_id),
            revoked_level=revoked_level.value,
            revoked_by=str(admin.id),
        )

        return True

    async def list_all_permissions(
        self,
        kb_id: UUID,
        admin: User,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[PermissionResponseExtended], int]:
        """List all permissions (user + group) on a Knowledge Base.

        Requires ADMIN permission on the KB.

        Args:
            kb_id: The KB UUID.
            admin: The admin user requesting the list.
            page: Page number (1-indexed).
            limit: Items per page.

        Returns:
            Tuple of (list of PermissionResponseExtended, total count).

        Raises:
            PermissionError: If admin doesn't have ADMIN permission.
            ValueError: If KB doesn't exist.
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

        offset = (page - 1) * limit

        # Get user permissions count
        user_count_result = await self.session.execute(
            select(func.count(KBPermission.id)).where(KBPermission.kb_id == kb_id)
        )
        user_count = user_count_result.scalar() or 0

        # Get group permissions count
        group_count_result = await self.session.execute(
            select(func.count(KBGroupPermission.id)).where(
                KBGroupPermission.kb_id == kb_id
            )
        )
        group_count = group_count_result.scalar() or 0

        total = user_count + group_count

        # Build combined results
        permissions: list[PermissionResponseExtended] = []

        # Get user permissions with email
        user_query = (
            select(KBPermission, User.email)
            .join(User, KBPermission.user_id == User.id)
            .where(KBPermission.kb_id == kb_id)
            .order_by(KBPermission.created_at.desc())
        )
        user_result = await self.session.execute(user_query)
        user_rows = user_result.all()

        for perm, email in user_rows:
            permissions.append(
                PermissionResponseExtended(
                    id=perm.id,
                    entity_type="user",
                    entity_id=perm.user_id,
                    entity_name=email,
                    kb_id=perm.kb_id,
                    permission_level=perm.permission_level,
                    created_at=perm.created_at,
                )
            )

        # Get group permissions with name
        group_query = (
            select(KBGroupPermission, Group.name)
            .join(Group, KBGroupPermission.group_id == Group.id)
            .where(KBGroupPermission.kb_id == kb_id)
            .order_by(KBGroupPermission.created_at.desc())
        )
        group_result = await self.session.execute(group_query)
        group_rows = group_result.all()

        for perm, name in group_rows:
            permissions.append(
                PermissionResponseExtended(
                    id=perm.id,
                    entity_type="group",
                    entity_id=perm.group_id,
                    entity_name=name,
                    kb_id=perm.kb_id,
                    permission_level=perm.permission_level,
                    created_at=perm.created_at,
                )
            )

        # Sort by created_at descending and apply pagination
        permissions.sort(key=lambda p: p.created_at, reverse=True)
        paginated = permissions[offset : offset + limit]

        return paginated, total

    async def get_effective_permissions(
        self,
        kb_id: UUID,
    ) -> list[EffectivePermission]:
        """Get effective permissions for all users on a KB.

        Computes the effective permission for each user by considering:
        1. Direct user permissions (highest priority)
        2. Group permissions (inherited)

        Direct permissions always override group permissions.

        Args:
            kb_id: The KB UUID.

        Returns:
            List of EffectivePermission showing each user's resolved access.
        """
        # Get all direct user permissions
        direct_query = (
            select(KBPermission, User.email)
            .join(User, KBPermission.user_id == User.id)
            .where(KBPermission.kb_id == kb_id)
        )
        direct_result = await self.session.execute(direct_query)
        direct_rows = direct_result.all()

        # Build map of user_id -> direct permission
        direct_permissions: dict[UUID, tuple[PermissionLevel, str]] = {}
        for perm, email in direct_rows:
            direct_permissions[perm.user_id] = (perm.permission_level, email)

        # Get all group permissions for this KB
        group_perm_query = (
            select(KBGroupPermission, Group.id)
            .join(Group, KBGroupPermission.group_id == Group.id)
            .where(
                KBGroupPermission.kb_id == kb_id,
                Group.is_active.is_(True),
            )
        )
        group_perm_result = await self.session.execute(group_perm_query)
        group_perms = {
            row[1]: row[0].permission_level for row in group_perm_result.all()
        }

        # Get all users in groups that have permissions on this KB
        if group_perms:
            group_ids = list(group_perms.keys())
            user_group_query = (
                select(UserGroup.user_id, UserGroup.group_id, User.email)
                .join(User, UserGroup.user_id == User.id)
                .where(UserGroup.group_id.in_(group_ids))
            )
            user_group_result = await self.session.execute(user_group_query)
            user_group_rows = user_group_result.all()
        else:
            user_group_rows = []

        # Build map of user_id -> list of (group_id, permission_level)
        user_group_permissions: dict[UUID, list[tuple[UUID, PermissionLevel, str]]] = {}
        user_emails: dict[UUID, str] = {}
        for user_id, group_id, email in user_group_rows:
            user_emails[user_id] = email
            if user_id not in user_group_permissions:
                user_group_permissions[user_id] = []
            user_group_permissions[user_id].append(
                (group_id, group_perms[group_id], email)
            )

        # Combine all user IDs
        all_user_ids = set(direct_permissions.keys()) | set(
            user_group_permissions.keys()
        )

        # Build effective permissions
        effective: list[EffectivePermission] = []
        for user_id in all_user_ids:
            sources: list[PermissionSource] = []
            effective_level: PermissionLevel | None = None

            # Check direct permission first (highest priority)
            if user_id in direct_permissions:
                level, email = direct_permissions[user_id]
                user_email = email
                sources.append(
                    PermissionSource(
                        source_type="direct",
                        source_id=user_id,
                        source_name="Direct",
                        permission_level=level,
                    )
                )
                effective_level = level
            else:
                user_email = user_emails.get(user_id, "unknown")

            # Add group sources
            if user_id in user_group_permissions:
                for group_id, group_level, _ in user_group_permissions[user_id]:
                    # Get group name
                    group_name_result = await self.session.execute(
                        select(Group.name).where(Group.id == group_id)
                    )
                    group_name = group_name_result.scalar_one_or_none() or "Unknown"

                    sources.append(
                        PermissionSource(
                            source_type="group",
                            source_id=group_id,
                            source_name=group_name,
                            permission_level=group_level,
                        )
                    )

                    # If no direct permission, use highest group permission
                    if effective_level is None:
                        effective_level = group_level
                    elif user_id not in direct_permissions and PERMISSION_HIERARCHY.get(
                        group_level, 0
                    ) > PERMISSION_HIERARCHY.get(effective_level, 0):
                        # Compare group permissions to find highest
                        effective_level = group_level

            if effective_level:
                effective.append(
                    EffectivePermission(
                        user_id=user_id,
                        user_email=user_email,
                        effective_level=effective_level,
                        sources=sources,
                    )
                )

        return effective

    async def check_permission_with_groups(
        self,
        user_id: UUID,
        kb_id: UUID,
    ) -> PermissionLevel | None:
        """Check user's permission on a KB including group inheritance.

        Resolution order:
        1. Direct user permission (if exists, return immediately)
        2. Highest group permission from user's groups
        3. None if no permission found

        Args:
            user_id: The user UUID.
            kb_id: The KB UUID.

        Returns:
            The effective permission level, or None if no access.
        """
        # Check direct permission first
        direct_result = await self.session.execute(
            select(KBPermission.permission_level).where(
                KBPermission.kb_id == kb_id,
                KBPermission.user_id == user_id,
            )
        )
        direct_level = direct_result.scalar_one_or_none()
        if direct_level:
            return direct_level

        # Get user's groups
        user_groups_result = await self.session.execute(
            select(UserGroup.group_id).where(UserGroup.user_id == user_id)
        )
        user_group_ids = [row[0] for row in user_groups_result.all()]

        if not user_group_ids:
            return None

        # Get highest group permission
        group_perm_result = await self.session.execute(
            select(KBGroupPermission.permission_level)
            .join(Group, KBGroupPermission.group_id == Group.id)
            .where(
                KBGroupPermission.kb_id == kb_id,
                KBGroupPermission.group_id.in_(user_group_ids),
                Group.is_active.is_(True),
            )
        )
        group_levels = [row[0] for row in group_perm_result.all()]

        if not group_levels:
            return None

        # Return highest permission level
        highest_level = max(
            group_levels, key=lambda level: PERMISSION_HIERARCHY.get(level, 0)
        )
        return highest_level


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
