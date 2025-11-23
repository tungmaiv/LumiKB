"""Knowledge Base API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from app.schemas.knowledge_base import (
    DocumentListResponse,
    DocumentMetadataResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("/", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KnowledgeBaseListResponse:
    """List all Knowledge Bases the user has access to.

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
            (KnowledgeBase.owner_id == current_user.id)
            | (permission_subq.c.permission_level.isnot(None))
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


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KnowledgeBaseResponse:
    """Get a specific Knowledge Base by ID.

    Requires the user to have at least READ permission.
    """
    # Get KB
    kb_result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge Base {kb_id} not found",
        )

    # Check permission
    permission = await _get_user_permission(session, current_user, kb)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this Knowledge Base",
        )

    # Get document count
    doc_count_result = await session.execute(
        select(func.count(Document.id)).where(Document.kb_id == kb_id)
    )
    doc_count = doc_count_result.scalar() or 0

    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        document_count=doc_count,
        permission_level=permission,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentListResponse:
    """List all documents in a Knowledge Base.

    Requires the user to have at least READ permission.
    """
    # Get KB
    kb_result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge Base {kb_id} not found",
        )

    # Check permission
    permission = await _get_user_permission(session, current_user, kb)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this Knowledge Base",
        )

    # Get documents
    docs_result = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.name)
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


async def _get_user_permission(
    session: AsyncSession,
    user: User,
    kb: KnowledgeBase,
) -> PermissionLevel | None:
    """Get user's effective permission level on a KB.

    Args:
        session: Database session.
        user: The user to check.
        kb: The Knowledge Base.

    Returns:
        Permission level if user has access, None otherwise.
    """
    # Owner has ADMIN permission
    if kb.owner_id == user.id:
        return PermissionLevel.ADMIN

    # Check explicit permission
    permission_result = await session.execute(
        select(KBPermission).where(
            KBPermission.user_id == user.id,
            KBPermission.kb_id == kb.id,
        )
    )
    permission = permission_result.scalar_one_or_none()

    return permission.permission_level if permission else None
