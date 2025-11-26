"""Knowledge Base API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.integrations.qdrant_client import qdrant_service
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from app.schemas.knowledge_base import (
    DocumentListResponse,
    DocumentMetadataResponse,
    KBCreate,
    KBListResponse,
    KBResponse,
    KBUpdate,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
)
from app.schemas.permission import (
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
)
from app.services.audit_service import audit_service
from app.services.kb_service import KBService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post(
    "/",
    response_model=KBResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    data: KBCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KBResponse:
    """Create a new Knowledge Base.

    Any authenticated user can create a KB. The creator becomes the owner
    and is automatically assigned ADMIN permission.

    A Qdrant collection is created for the KB with:
    - Collection name: kb_{uuid}
    - Vector size: 1536 (OpenAI ada-002)
    - Distance metric: Cosine similarity
    """
    kb_service = KBService(session)

    # Create KB in database
    kb = await kb_service.create(data, current_user)

    # Create Qdrant collection (AC2)
    try:
        await qdrant_service.create_collection(kb.id)
    except Exception as e:
        # Log but don't fail - Qdrant collection can be created later
        logger.error(
            "qdrant_collection_create_failed",
            kb_id=str(kb.id),
            error=str(e),
        )

    # Audit log (AC1)
    await audit_service.log_event(
        action="kb.created",
        resource_type="knowledge_base",
        user_id=current_user.id,
        resource_id=kb.id,
        details={"name": kb.name},
    )

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=0,
        total_size_bytes=0,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/", response_model=KBListResponse)
async def list_knowledge_bases(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KBListResponse:
    """List all Knowledge Bases the user has access to.

    Returns paginated list of KBs where the user has permission (READ, WRITE, or ADMIN).
    Each KB includes the user's permission level and document count.
    """
    kb_service = KBService(session)
    summaries, total = await kb_service.list_for_user(current_user, page, limit)

    return KBListResponse(
        data=summaries,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{kb_id}", response_model=KBResponse)
async def get_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KBResponse:
    """Get a specific Knowledge Base by ID.

    Requires the user to have at least READ permission.
    Returns 404 if KB doesn't exist or user has no permission (AC8).
    """
    kb_service = KBService(session)

    # Get KB with permission check (returns None if no access)
    kb = await kb_service.get(kb_id, current_user)

    if not kb:
        # AC8: Return 404 (not 403) to avoid leaking existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get document stats (AC3)
    doc_count, total_size = await kb_service.get_document_stats(kb_id)

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=doc_count,
        total_size_bytes=total_size,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.patch("/{kb_id}", response_model=KBResponse)
async def update_knowledge_base(
    kb_id: UUID,
    data: KBUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KBResponse:
    """Update a Knowledge Base.

    Requires ADMIN permission on the KB.
    Returns 403 if user doesn't have ADMIN permission (AC7).
    Returns 404 if KB doesn't exist.
    """
    kb_service = KBService(session)

    try:
        kb = await kb_service.update(kb_id, data, current_user)
    except PermissionError:
        # AC7: Return 403 Forbidden with PERMISSION_DENIED code
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to update this Knowledge Base",
            },
        ) from None

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get document stats
    doc_count, total_size = await kb_service.get_document_stats(kb_id)

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=doc_count,
        total_size_bytes=total_size,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Archive a Knowledge Base (soft delete).

    Requires ADMIN permission on the KB.
    Returns 403 if user doesn't have ADMIN permission (AC7).
    Returns 404 if KB doesn't exist.

    The KB is set to 'archived' status and removed from normal listings.
    An outbox event is created for async Qdrant collection deletion.
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.archive(kb_id, current_user)
    except PermissionError:
        # AC5, AC7: Return 403 Forbidden with PERMISSION_DENIED code
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to delete this Knowledge Base",
            },
        ) from None

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )


# Permission management endpoints (AC1, AC2, AC3)
@router.post(
    "/{kb_id}/permissions/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_permission(
    kb_id: UUID,
    data: PermissionCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PermissionResponse:
    """Grant permission to a user on a Knowledge Base.

    AC1: Creates or updates (upsert) permission entry.
    Requires ADMIN permission on the KB.
    Returns 201 Created with PermissionResponse.
    """
    kb_service = KBService(session)

    try:
        permission = await kb_service.grant_permission(
            kb_id=kb_id,
            user_id=data.user_id,
            level=data.permission_level,
            admin=current_user,
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN permission required to grant permissions",
        ) from None
    except ValueError as e:
        error_msg = str(e)
        if "User not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from None
        # KB not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None

    # Get user email for response
    from app.models.user import User as UserModel

    user_result = await session.execute(
        select(UserModel.email).where(UserModel.id == data.user_id)
    )
    email = user_result.scalar_one()

    return PermissionResponse(
        id=permission.id,
        user_id=permission.user_id,
        email=email,
        kb_id=permission.kb_id,
        permission_level=permission.permission_level,
        created_at=permission.created_at,
    )


@router.get("/{kb_id}/permissions/", response_model=PermissionListResponse)
async def list_permissions(
    kb_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PermissionListResponse:
    """List all permissions on a Knowledge Base.

    AC2: Returns paginated list with user_id, email, permission_level, created_at.
    Requires ADMIN permission on the KB.
    """
    kb_service = KBService(session)

    try:
        permissions, total = await kb_service.list_permissions(
            kb_id=kb_id,
            admin=current_user,
            page=page,
            limit=limit,
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN permission required to list permissions",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None

    return PermissionListResponse(
        data=permissions,
        total=total,
        page=page,
        limit=limit,
    )


@router.delete(
    "/{kb_id}/permissions/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_permission(
    kb_id: UUID,
    user_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Revoke a user's permission on a Knowledge Base.

    AC3: Removes the permission entry.
    Requires ADMIN permission on the KB.
    Returns 204 No Content on success, 404 if permission doesn't exist.
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.revoke_permission(
            kb_id=kb_id,
            user_id=user_id,
            admin=current_user,
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN permission required to revoke permissions",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )


# Legacy endpoints for backwards compatibility
@router.get("/legacy/list", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases_legacy(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KnowledgeBaseListResponse:
    """Legacy endpoint: List all Knowledge Bases the user has access to.

    Returns Knowledge Bases where the user is:
    - The owner
    - Has explicit permission (READ, WRITE, or ADMIN)

    Each KB includes the user's permission level and document count.
    """
    # Subquery to get document count per KB
    doc_count_subq = (
        select(
            Document.kb_id,
            func.count(Document.id).label("doc_count"),
        )
        .where(Document.status != DocumentStatus.ARCHIVED)
        .group_by(Document.kb_id)
        .subquery()
    )

    # Subquery to get user's permission level per KB
    permission_subq = (
        select(
            KBPermission.kb_id,
            KBPermission.permission_level,
        )
        .where(KBPermission.user_id == current_user.id)
        .subquery()
    )

    # Main query: get KBs user owns or has permission to
    query = (
        select(
            KnowledgeBase,
            func.coalesce(doc_count_subq.c.doc_count, 0).label("document_count"),
            permission_subq.c.permission_level,
        )
        .outerjoin(doc_count_subq, KnowledgeBase.id == doc_count_subq.c.kb_id)
        .outerjoin(permission_subq, KnowledgeBase.id == permission_subq.c.kb_id)
        .where(
            KnowledgeBase.status == "active",
            (KnowledgeBase.owner_id == current_user.id)
            | (permission_subq.c.permission_level.isnot(None)),
        )
        .order_by(KnowledgeBase.name)
    )

    result = await session.execute(query)
    rows = result.all()

    kbs = []
    for row in rows:
        kb = row[0]
        doc_count = row[1]
        permission = row[2]

        # If user is owner, they have ADMIN permission
        if kb.owner_id == current_user.id:
            effective_permission = PermissionLevel.ADMIN
        else:
            effective_permission = permission

        kbs.append(
            KnowledgeBaseResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                status=kb.status,
                document_count=doc_count,
                permission_level=effective_permission,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
            )
        )

    return KnowledgeBaseListResponse(data=kbs)


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentListResponse:
    """List all documents in a Knowledge Base.

    Requires the user to have at least READ permission.
    """
    kb_service = KBService(session)

    # Check permission using service
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get documents (excluding archived)
    docs_result = await session.execute(
        select(Document)
        .where(
            Document.kb_id == kb_id,
            Document.status != DocumentStatus.ARCHIVED,
        )
        .order_by(Document.name)
    )
    documents = docs_result.scalars().all()

    return DocumentListResponse(
        data=[
            DocumentMetadataResponse(
                id=doc.id,
                name=doc.name,
                status=doc.status.value,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]
    )
