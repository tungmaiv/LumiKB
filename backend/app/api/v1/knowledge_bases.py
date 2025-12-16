"""Knowledge Base API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    current_active_user,
    get_current_administrator,
    get_current_operator,
)
from app.core.database import get_async_session
from app.core.redis import get_redis_client
from app.integrations.qdrant_client import qdrant_service
from app.models.document import Document, DocumentStatus
from app.models.group import Group
from app.models.kb_access_log import AccessType
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from app.schemas.document import (
    ArchivedDocumentItem,
    DocumentProcessingDetails,
    DocumentTagsUpdate,
    PaginatedArchivedDocumentsResponse,
    PaginatedDocumentProcessingResponse,
    ProcessingFilters,
    ProcessingStep,
)
from app.schemas.kb_settings import (
    KBSettings,
    PresetDetailResponse,
    PresetDetectRequest,
    PresetDetectResponse,
    PresetInfo,
    PresetListResponse,
)
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
    EffectivePermissionListResponse,
    PermissionCreate,
    PermissionCreateExtended,
    PermissionListResponse,
    PermissionListResponseExtended,
    PermissionResponse,
    PermissionResponseExtended,
    PermissionUpdate,
)
from app.services.audit_service import audit_service
from app.services.document_service import DocumentService, DocumentValidationError
from app.services.kb_config_resolver import get_kb_config_resolver
from app.services.kb_recommendation_service import KBRecommendationService
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
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> KBResponse:
    """Create a new Knowledge Base.

    Any authenticated user can create a KB. The creator becomes the owner
    and is automatically assigned ADMIN permission.

    Story 7-10: Model Configuration
    - embedding_model_id: UUID of embedding model from registry (optional)
    - generation_model_id: UUID of generation model from registry (optional)
    - RAG parameters: similarity_threshold, search_top_k, temperature, rerank_enabled

    A Qdrant collection is created for the KB with:
    - Collection name: kb_{uuid}
    - Vector size: From embedding model config, or default 768
    - Distance metric: From embedding model config, or default cosine
    """
    kb_service = KBService(session)

    try:
        # Create KB in database (handles model validation and Qdrant collection)
        # If embedding_model_id provided, creates collection with model dimensions
        # Otherwise, creates collection with default dimensions
        kb = await kb_service.create(data, current_user)
    except ValueError as e:
        # AC-7.10.2: Model validation failed (not found, inactive, wrong type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MODEL_VALIDATION_ERROR",
                "message": str(e),
            },
        ) from None

    # If no embedding model specified, create default Qdrant collection (legacy behavior)
    if not data.embedding_model_id:
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
        details={
            "name": kb.name,
            "embedding_model_id": str(data.embedding_model_id)
            if data.embedding_model_id
            else None,
            "generation_model_id": str(data.generation_model_id)
            if data.generation_model_id
            else None,
        },
    )

    # Build response with model info (Story 7-10)
    # Refresh KB to load all attributes and relationships (avoid lazy loading in async)
    await session.refresh(kb)
    await session.refresh(kb, attribute_names=["embedding_model", "generation_model"])

    from app.schemas.knowledge_base import EmbeddingModelInfo, GenerationModelInfo

    embedding_model_info = None
    if kb.embedding_model:
        embedding_model_info = EmbeddingModelInfo(
            id=kb.embedding_model.id,
            name=kb.embedding_model.name,
            model_id=kb.embedding_model.model_id,
            dimensions=kb.embedding_model.config.get("dimensions")
            if kb.embedding_model.config
            else None,
            distance_metric=kb.embedding_model.config.get("distance_metric")
            if kb.embedding_model.config
            else None,
        )

    generation_model_info = None
    if kb.generation_model:
        generation_model_info = GenerationModelInfo(
            id=kb.generation_model.id,
            name=kb.generation_model.name,
            model_id=kb.generation_model.model_id,
            context_window=kb.generation_model.config.get("context_window")
            if kb.generation_model.config
            else None,
            max_tokens=kb.generation_model.config.get("max_tokens")
            if kb.generation_model.config
            else None,
        )

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=0,
        total_size_bytes=0,
        permission_level=PermissionLevel.ADMIN,  # Creator is always ADMIN
        tags=kb.tags or [],
        embedding_model=embedding_model_info,
        generation_model=generation_model_info,
        qdrant_collection_name=kb.qdrant_collection_name,
        qdrant_vector_size=kb.qdrant_vector_size,
        similarity_threshold=kb.similarity_threshold,
        search_top_k=kb.search_top_k,
        temperature=kb.temperature,
        rerank_enabled=kb.rerank_enabled,
        embedding_model_locked=False,  # New KB has no documents yet
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/", response_model=KBListResponse)
async def list_knowledge_bases(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(
        default=False, description="Include archived KBs in the list"
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> KBListResponse:
    """List all Knowledge Bases the user has access to.

    Returns paginated list of KBs where the user has permission (READ, WRITE, or ADMIN).
    Each KB includes the user's permission level and document count.

    Story 7-26 (AC-7.26.5): Use include_archived=true to include archived KBs.
    """
    kb_service = KBService(session)
    summaries, total = await kb_service.list_for_user(
        current_user, page, limit, include_archived=include_archived
    )

    return KBListResponse(
        data=summaries,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/presets", response_model=PresetListResponse)
async def list_kb_presets(
    current_user: User = Depends(current_active_user),  # noqa: ARG001
) -> PresetListResponse:
    """List all available KB settings presets.

    Story 7-16: KB Settings Presets (AC-7.16.1)
    Returns a list of preset configurations that can be applied to
    knowledge bases for quick optimization (legal, technical, creative, code, general).

    Presets include:
    - legal: Strict citations, low temperature for legal documents
    - technical: Inline citations, balanced for technical docs
    - creative: High temperature, flexible for brainstorming
    - code: Low temperature, strict for code repositories
    - general: System defaults for general use
    """
    from app.core.kb_presets import list_presets

    presets = list_presets()
    preset_infos = [
        PresetInfo(id=p["id"], name=p["name"], description=p["description"])
        for p in presets
    ]
    return PresetListResponse(presets=preset_infos)


@router.post("/presets/detect", response_model=PresetDetectResponse)
async def detect_kb_preset(
    settings: PresetDetectRequest,
    current_user: User = Depends(current_active_user),  # noqa: ARG001
) -> PresetDetectResponse:
    """Detect which preset matches the provided settings.

    Story 7-16: KB Settings Presets (AC-7.16.8)
    Analyzes the provided settings and returns the matching preset ID
    or 'custom' if no preset matches.

    This is used by the frontend to show the current preset indicator.
    """
    from app.core.kb_presets import detect_preset

    # Convert request to KBSettings for detection
    settings_obj = KBSettings(
        chunking=settings.chunking,
        retrieval=settings.retrieval,
        generation=settings.generation,
        prompts=settings.prompts,
        preset=settings.preset,
    )

    detected = detect_preset(settings_obj)
    return PresetDetectResponse(detected_preset=detected)


@router.get("/presets/{preset_id}", response_model=PresetDetailResponse)
async def get_kb_preset(
    preset_id: str,
    current_user: User = Depends(current_active_user),  # noqa: ARG001
) -> PresetDetailResponse:
    """Get a specific preset by ID with full settings.

    Story 7-16: KB Settings Presets (AC-7.16.2-6)
    Returns the full configuration for a specific preset.

    Args:
        preset_id: Preset identifier (legal, technical, creative, code, general)

    Returns:
        PresetDetailResponse with full settings

    Raises:
        HTTPException: 404 if preset not found
    """
    from app.core.kb_presets import get_preset

    preset = get_preset(preset_id)
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_id}' not found",
        )

    return PresetDetailResponse(
        id=preset_id,
        name=preset["name"],
        description=preset["description"],
        settings=preset["settings"],
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

    Story 7-10: Returns model configuration including:
    - embedding_model: Configured embedding model info
    - generation_model: Configured generation model info
    - RAG parameters: similarity_threshold, search_top_k, temperature, rerank_enabled
    - embedding_model_locked: True if embedding model cannot be changed (documents exist)
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

    # Get user's permission level on this KB
    permission_level = await kb_service.get_user_permission(kb_id, current_user)

    # Log KB access for recommendations (fire-and-forget, Story 5.8)
    try:
        kb_rec_service = KBRecommendationService(session)
        await kb_rec_service.log_kb_access(
            user_id=current_user.id,
            kb_id=kb_id,
            access_type=AccessType.VIEW,
        )
    except Exception as e:
        # Fire-and-forget - don't fail request on logging error
        logger.warning(
            "kb_access_log_failed",
            kb_id=str(kb_id),
            user_id=str(current_user.id),
            error=str(e),
        )

    # Build model info for response (Story 7-10)
    from app.schemas.knowledge_base import EmbeddingModelInfo, GenerationModelInfo

    embedding_model_info = None
    if kb.embedding_model:
        embedding_model_info = EmbeddingModelInfo(
            id=kb.embedding_model.id,
            name=kb.embedding_model.name,
            model_id=kb.embedding_model.model_id,
            dimensions=kb.embedding_model.config.get("dimensions")
            if kb.embedding_model.config
            else None,
            distance_metric=kb.embedding_model.config.get("distance_metric")
            if kb.embedding_model.config
            else None,
        )

    generation_model_info = None
    if kb.generation_model:
        generation_model_info = GenerationModelInfo(
            id=kb.generation_model.id,
            name=kb.generation_model.name,
            model_id=kb.generation_model.model_id,
            context_window=kb.generation_model.config.get("context_window")
            if kb.generation_model.config
            else None,
            max_tokens=kb.generation_model.config.get("max_tokens")
            if kb.generation_model.config
            else None,
        )

    # AC-7.10.5: Embedding model is locked if KB has processed documents
    embedding_model_locked = doc_count > 0

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=doc_count,
        total_size_bytes=total_size,
        permission_level=permission_level,
        tags=kb.tags or [],
        embedding_model=embedding_model_info,
        generation_model=generation_model_info,
        qdrant_collection_name=kb.qdrant_collection_name,
        qdrant_vector_size=kb.qdrant_vector_size,
        similarity_threshold=kb.similarity_threshold,
        search_top_k=kb.search_top_k,
        temperature=kb.temperature,
        rerank_enabled=kb.rerank_enabled,
        embedding_model_locked=embedding_model_locked,
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

    Story 7-10: Model Configuration Updates
    - AC-7.10.5: Embedding model can only be changed if KB has no documents
    - AC-7.10.6: Generation model can be changed anytime
    - AC-7.10.7: RAG parameters can be updated anytime
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
    except ValueError as e:
        # AC-7.10.5: Embedding model locked or model validation error
        error_msg = str(e)
        if "locked" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMBEDDING_MODEL_LOCKED",
                    "message": error_msg,
                },
            ) from None
        # Model validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MODEL_VALIDATION_ERROR",
                "message": error_msg,
            },
        ) from None

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get document stats
    doc_count, total_size = await kb_service.get_document_stats(kb_id)

    # Build model info for response (Story 7-10)
    from app.schemas.knowledge_base import EmbeddingModelInfo, GenerationModelInfo

    embedding_model_info = None
    if kb.embedding_model:
        embedding_model_info = EmbeddingModelInfo(
            id=kb.embedding_model.id,
            name=kb.embedding_model.name,
            model_id=kb.embedding_model.model_id,
            dimensions=kb.embedding_model.config.get("dimensions")
            if kb.embedding_model.config
            else None,
            distance_metric=kb.embedding_model.config.get("distance_metric")
            if kb.embedding_model.config
            else None,
        )

    generation_model_info = None
    if kb.generation_model:
        generation_model_info = GenerationModelInfo(
            id=kb.generation_model.id,
            name=kb.generation_model.name,
            model_id=kb.generation_model.model_id,
            context_window=kb.generation_model.config.get("context_window")
            if kb.generation_model.config
            else None,
            max_tokens=kb.generation_model.config.get("max_tokens")
            if kb.generation_model.config
            else None,
        )

    # AC-7.10.5: Embedding model is locked if KB has processed documents
    embedding_model_locked = doc_count > 0

    # Build response BEFORE fire-and-forget logging to avoid session corruption
    # Update requires ADMIN permission, so we know user is ADMIN
    response = KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        owner_id=kb.owner_id,
        status=kb.status,
        document_count=doc_count,
        total_size_bytes=total_size,
        permission_level=PermissionLevel.ADMIN,  # Update requires ADMIN
        tags=kb.tags or [],
        embedding_model=embedding_model_info,
        generation_model=generation_model_info,
        qdrant_collection_name=kb.qdrant_collection_name,
        qdrant_vector_size=kb.qdrant_vector_size,
        similarity_threshold=kb.similarity_threshold,
        search_top_k=kb.search_top_k,
        temperature=kb.temperature,
        rerank_enabled=kb.rerank_enabled,
        embedding_model_locked=embedding_model_locked,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )

    # Log KB access for recommendations (fire-and-forget, Story 5.8)
    try:
        kb_rec_service = KBRecommendationService(session)
        await kb_rec_service.log_kb_access(
            user_id=current_user.id,
            kb_id=kb_id,
            access_type=AccessType.EDIT,
        )
    except Exception as e:
        # Fire-and-forget - don't fail request on logging error
        logger.warning(
            "kb_access_log_failed",
            kb_id=str(kb_id),
            user_id=str(current_user.id),
            error=str(e),
        )

    return response


# =============================================================================
# KB Settings Endpoints (Story 7-14: KB Settings UI - General Panel)
# =============================================================================


@router.get("/{kb_id}/settings", response_model=KBSettings)
async def get_kb_settings(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
) -> KBSettings:
    """Get KB-level configuration settings.

    AC-7.14.8: Returns full KBSettings object for the Knowledge Base.
    Uses cached settings via KBConfigResolver with 5-minute TTL.

    Requires at least READ permission on the KB.
    Returns 404 if KB doesn't exist or user has no permission.
    """
    kb_service = KBService(session)

    # Check permission (returns None if no access)
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get settings via config resolver (uses caching)
    try:
        resolver = await get_kb_config_resolver(session, redis)
        settings = await resolver.get_kb_settings(kb_id)
        return settings
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None


@router.put("/{kb_id}/settings", response_model=KBSettings)
async def update_kb_settings(
    kb_id: UUID,
    data: dict,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
) -> KBSettings:
    """Update KB-level configuration settings.

    AC-7.14.6: Saves settings to KB.settings JSONB field.
    AC-7.14.8: Validates settings against KBSettings schema, creates audit log.

    Supports partial updates - only provided fields are merged with existing settings.
    Requires ADMIN permission on the KB.
    Returns 404 if KB doesn't exist or user has no permission.
    Returns 422 if validation fails.
    """
    kb_service = KBService(session)

    # Check ADMIN permission
    has_admin = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.ADMIN
    )
    if not has_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to update KB settings",
            },
        )

    # Verify KB exists
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get current settings
    current_settings = kb.settings or {}

    # Deep merge: update existing settings with new data
    def deep_merge(base: dict, updates: dict) -> dict:
        """Deep merge updates into base dict."""
        result = base.copy()
        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    merged_settings = deep_merge(current_settings, data)

    # Validate merged settings against KBSettings schema
    try:
        validated_settings = KBSettings.model_validate(merged_settings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
            },
        ) from None

    # Update KB settings in database
    kb.settings = validated_settings.model_dump()
    await session.flush()

    # Invalidate cache (AC-7.14.8)
    try:
        resolver = await get_kb_config_resolver(session, redis)
        await resolver.invalidate_kb_settings_cache(kb_id)
    except Exception as e:
        # Log but don't fail if cache invalidation fails
        logger.warning(
            "kb_settings_cache_invalidate_failed",
            kb_id=str(kb_id),
            error=str(e),
        )

    # Audit log (AC-7.14.8)
    await audit_service.log_event(
        action="kb.settings_updated",
        resource_type="knowledge_base",
        user_id=current_user.id,
        resource_id=kb_id,
        details={
            "updated_fields": list(data.keys()),
        },
    )

    logger.info(
        "kb_settings_updated",
        kb_id=str(kb_id),
        user_id=str(current_user.id),
        updated_fields=list(data.keys()),
    )

    return validated_settings


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a Knowledge Base (hard delete).

    Story 7-24: KB Archive Backend
    - Only permitted for KBs with 0 documents
    - Performs hard delete of KB record and all related data
    - Creates outbox event to delete Qdrant collection

    Requires ADMIN permission on the KB.
    Returns 403 if user doesn't have ADMIN permission.
    Returns 404 if KB doesn't exist.
    Returns 409 if KB has documents (must archive first or delete documents).
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.hard_delete(kb_id, current_user)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to delete this Knowledge Base",
            },
        ) from None
    except ValueError as e:
        # KB has documents - cannot delete
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "KB_HAS_DOCUMENTS",
                "message": str(e),
            },
        ) from None

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )


@router.post("/{kb_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Archive a Knowledge Base (soft delete).

    Story 7-24: KB Archive Backend
    - Sets KB.archived_at timestamp and status to 'archived'
    - Cascades archive to all documents (sets document.archived_at)
    - Creates outbox event to update Qdrant payloads with is_archived: true

    Requires ADMIN permission on the KB.
    Returns 403 if user doesn't have ADMIN permission.
    Returns 404 if KB doesn't exist or is already archived.
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.archive(kb_id, current_user)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to archive this Knowledge Base",
            },
        ) from None

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found or already archived",
        )


@router.post("/{kb_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Restore an archived Knowledge Base.

    Story 7-25: KB Restore Backend
    - Clears KB.archived_at and sets status to 'active'
    - Cascades restore to all documents (clears document.archived_at)
    - Creates outbox event to update Qdrant payloads with is_archived: false

    Requires ADMIN permission on the KB.
    Returns 403 if user doesn't have ADMIN permission.
    Returns 404 if KB doesn't exist or is not archived.
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.restore(kb_id, current_user)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "ADMIN permission required to restore this Knowledge Base",
            },
        ) from None

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found or not archived",
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


# Extended permission endpoints for Story 5-20 (group permissions)
@router.post(
    "/{kb_id}/permissions/extended",
    response_model=PermissionResponseExtended,
    status_code=status.HTTP_201_CREATED,
)
async def grant_permission_extended(
    kb_id: UUID,
    data: PermissionCreateExtended,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PermissionResponseExtended:
    """Grant permission to a user or group on a Knowledge Base.

    AC-5.20.2: Creates or updates (upsert) permission entry.
    Requires ADMIN permission on the KB.
    Specify either user_id OR group_id (mutually exclusive).
    Returns 201 Created with PermissionResponseExtended.
    """
    kb_service = KBService(session)

    try:
        if data.user_id:
            # Grant user permission
            permission = await kb_service.grant_permission(
                kb_id=kb_id,
                user_id=data.user_id,
                level=data.permission_level,
                admin=current_user,
            )
            # Get user email for response
            user_result = await session.execute(
                select(User.email).where(User.id == data.user_id)
            )
            entity_name = user_result.scalar_one()
            return PermissionResponseExtended(
                id=permission.id,
                entity_type="user",
                entity_id=permission.user_id,
                entity_name=entity_name,
                kb_id=permission.kb_id,
                permission_level=permission.permission_level,
                created_at=permission.created_at,
            )
        else:
            # Grant group permission
            permission = await kb_service.grant_group_permission(
                kb_id=kb_id,
                group_id=data.group_id,
                level=data.permission_level,
                admin=current_user,
            )
            # Get group name for response
            group_result = await session.execute(
                select(Group.name).where(Group.id == data.group_id)
            )
            entity_name = group_result.scalar_one()
            return PermissionResponseExtended(
                id=permission.id,
                entity_type="group",
                entity_id=permission.group_id,
                entity_name=entity_name,
                kb_id=permission.kb_id,
                permission_level=permission.permission_level,
                created_at=permission.created_at,
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
        if "Group not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None


@router.get(
    "/{kb_id}/permissions/all",
    response_model=PermissionListResponseExtended,
)
async def list_all_permissions(
    kb_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PermissionListResponseExtended:
    """List all permissions (users + groups) on a Knowledge Base.

    AC-5.20.1: Returns paginated list of all permission entries.
    Each entry includes entity_type (user/group), entity_name, permission_level, created_at.
    Requires ADMIN permission on the KB.
    """
    kb_service = KBService(session)

    try:
        permissions, total = await kb_service.list_all_permissions(
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

    return PermissionListResponseExtended(
        data=permissions,
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/{kb_id}/permissions/effective",
    response_model=EffectivePermissionListResponse,
)
async def get_effective_permissions(
    kb_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> EffectivePermissionListResponse:
    """Get effective permissions for all users on a Knowledge Base.

    AC-5.20.4: Computes effective permissions considering:
    1. Direct user permissions (highest priority)
    2. Group permissions (inherited)

    Direct permissions always override group permissions.
    Returns list of EffectivePermission showing each user's resolved access.
    Requires ADMIN permission on the KB.
    """
    kb_service = KBService(session)

    # Check ADMIN permission
    has_admin = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.ADMIN
    )
    if not has_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN permission required to view effective permissions",
        )

    # Verify KB exists
    kb_result = await session.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.status == "active",
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    effective = await kb_service.get_effective_permissions(kb_id)

    return EffectivePermissionListResponse(data=effective)


@router.patch(
    "/{kb_id}/permissions/{permission_id}",
    response_model=PermissionResponseExtended,
)
async def update_permission(
    kb_id: UUID,
    permission_id: UUID,
    data: PermissionUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PermissionResponseExtended:
    """Update a permission's level on a Knowledge Base.

    AC-5.20.3: Updates the permission level for an existing permission entry.
    Requires ADMIN permission on the KB.
    Works for both user and group permissions.
    """
    kb_service = KBService(session)

    # Check ADMIN permission
    has_admin = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.ADMIN
    )
    if not has_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN permission required to update permissions",
        )

    # Try to find user permission first
    from app.models.kb_group_permission import KBGroupPermission

    user_perm_result = await session.execute(
        select(KBPermission).where(
            KBPermission.id == permission_id,
            KBPermission.kb_id == kb_id,
        )
    )
    user_perm = user_perm_result.scalar_one_or_none()

    if user_perm:
        # Update user permission
        user_perm.permission_level = data.permission_level
        await session.flush()

        # Get user email for response
        user_result = await session.execute(
            select(User.email).where(User.id == user_perm.user_id)
        )
        entity_name = user_result.scalar_one()

        return PermissionResponseExtended(
            id=user_perm.id,
            entity_type="user",
            entity_id=user_perm.user_id,
            entity_name=entity_name,
            kb_id=user_perm.kb_id,
            permission_level=user_perm.permission_level,
            created_at=user_perm.created_at,
        )

    # Try group permission
    group_perm_result = await session.execute(
        select(KBGroupPermission).where(
            KBGroupPermission.id == permission_id,
            KBGroupPermission.kb_id == kb_id,
        )
    )
    group_perm = group_perm_result.scalar_one_or_none()

    if group_perm:
        # Update group permission
        group_perm.permission_level = data.permission_level
        await session.flush()

        # Get group name for response
        group_result = await session.execute(
            select(Group.name).where(Group.id == group_perm.group_id)
        )
        entity_name = group_result.scalar_one()

        return PermissionResponseExtended(
            id=group_perm.id,
            entity_type="group",
            entity_id=group_perm.group_id,
            entity_name=entity_name,
            kb_id=group_perm.kb_id,
            permission_level=group_perm.permission_level,
            created_at=group_perm.created_at,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Permission not found",
    )


@router.delete(
    "/{kb_id}/permissions/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_group_permission(
    kb_id: UUID,
    group_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Revoke a group's permission on a Knowledge Base.

    Removes the group permission entry.
    Requires ADMIN permission on the KB.
    Returns 204 No Content on success, 404 if permission doesn't exist.
    """
    kb_service = KBService(session)

    try:
        success = await kb_service.revoke_group_permission(
            kb_id=kb_id,
            group_id=group_id,
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
                tags=kb.tags or [],
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


# Document Processing Status endpoints (Story 5-23)
@router.get(
    "/{kb_id}/processing",
    response_model=PaginatedDocumentProcessingResponse,
)
async def list_documents_processing_status(
    kb_id: UUID,
    name: str | None = Query(default=None, description="Filter by document name"),
    file_type: str | None = Query(default=None, description="Filter by file type"),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status (pending, processing, completed, error)",
    ),
    current_step: ProcessingStep | None = Query(
        default=None,
        description="Filter by current processing step",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedDocumentProcessingResponse:
    """List documents with processing status for a Knowledge Base.

    AC-5.23.1: Displays Processing tab with step-level progress for each document.
    AC-5.23.2: Supports filtering by name, file type, status, and processing step.
    AC-5.23.4: Requires WRITE or ADMIN permission (processing tab is admin/write only).

    Returns paginated list of documents with their processing status.
    """
    kb_service = KBService(session)

    # AC-5.23.4: Check WRITE permission (ADMIN inherits WRITE)
    has_write = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.WRITE
    )
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "WRITE permission required to view processing status",
            },
        )

    # Verify KB exists
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Build filters
    from app.models.document import DocumentStatus

    filters = ProcessingFilters(
        name=name,
        file_type=file_type,
        status=DocumentStatus(status_filter) if status_filter else None,
        current_step=current_step,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Get documents with processing status
    doc_service = DocumentService(session)
    documents, total = await doc_service.list_with_processing_status(kb_id, filters)

    return PaginatedDocumentProcessingResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{kb_id}/processing/{doc_id}",
    response_model=DocumentProcessingDetails,
)
async def get_document_processing_details(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentProcessingDetails:
    """Get detailed processing status for a specific document.

    AC-5.23.3: Returns step-by-step processing details with timing and errors.
    AC-5.23.4: Requires WRITE or ADMIN permission.

    Returns detailed processing information including:
    - Per-step status (pending, in_progress, done, error, skipped)
    - Step timing (started_at, completed_at, duration)
    - Error messages for failed steps
    """
    kb_service = KBService(session)

    # AC-5.23.4: Check WRITE permission
    has_write = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.WRITE
    )
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "WRITE permission required to view processing details",
            },
        )

    # Verify KB exists
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Get document processing details
    doc_service = DocumentService(session)
    details = await doc_service.get_processing_details(doc_id)

    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify document belongs to this KB
    document = await doc_service.get_by_id(doc_id)
    if document and document.kb_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this Knowledge Base",
        )

    return details


# Archived Documents endpoint
@router.get(
    "/{kb_id}/archived",
    response_model=PaginatedArchivedDocumentsResponse,
)
async def list_archived_documents(
    kb_id: UUID,
    search: str | None = Query(default=None, description="Search by document name"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedArchivedDocumentsResponse:
    """List archived documents for a Knowledge Base.

    Returns paginated list of archived documents. Requires WRITE or ADMIN permission.
    """
    kb_service = KBService(session)

    # Check WRITE permission (ADMIN inherits WRITE)
    has_write = await kb_service.check_permission(
        kb_id, current_user, PermissionLevel.WRITE
    )
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "WRITE permission required to view archived documents",
            },
        )

    # Verify KB exists
    kb = await kb_service.get(kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        )

    # Build query for archived documents
    from sqlalchemy.orm import selectinload

    conditions = [
        Document.kb_id == kb_id,
        Document.deleted_at.is_(None),
        Document.archived_at.is_not(None),
    ]

    # Apply search filter
    if search:
        search_pattern = f"%{search.lower()}%"
        conditions.append(
            func.lower(Document.name).like(search_pattern)
            | func.lower(Document.original_filename).like(search_pattern)
        )

    # Get total count
    count_query = select(func.count(Document.id)).where(*conditions)
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    has_more = (page * page_size) < total

    # Get archived documents with uploader info
    query = (
        select(Document)
        .options(selectinload(Document.uploader))
        .where(*conditions)
        .order_by(Document.archived_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    documents = result.scalars().all()

    # Build response
    data = [
        ArchivedDocumentItem(
            id=doc.id,
            name=doc.name,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            file_size_bytes=doc.file_size_bytes,
            chunk_count=doc.chunk_count or 0,
            archived_at=doc.archived_at,
            created_at=doc.created_at,
            tags=doc.tags or [],
            uploader_email=doc.uploader.email if doc.uploader else None,
        )
        for doc in documents
    ]

    return PaginatedArchivedDocumentsResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


# Document Tags endpoint (Story 5-22)
@router.patch(
    "/{kb_id}/documents/{doc_id}/tags",
    response_model=DocumentTagsUpdate,
)
async def update_document_tags(
    kb_id: UUID,
    doc_id: UUID,
    data: DocumentTagsUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentTagsUpdate:
    """Update tags for a document.

    AC-5.22.1: Users with WRITE/ADMIN permission can add/edit tags.
    AC-5.22.3: Tags are validated (max 10 tags, max 50 chars each).
    AC-5.22.5: Tag updates are logged for audit.

    Returns the updated tags after normalization (lowercase, trimmed).
    """
    doc_service = DocumentService(session)

    try:
        document = await doc_service.update_tags(
            kb_id=kb_id,
            doc_id=doc_id,
            tags=data.tags,
            user=current_user,
        )
    except DocumentValidationError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            ) from None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": e.message,
            },
        ) from None

    return DocumentTagsUpdate(tags=document.tags or [])
