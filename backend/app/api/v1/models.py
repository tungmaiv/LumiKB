"""LLM Model Registry API endpoints.

Provides admin endpoints for managing LLM models and public endpoints
for listing available models for KB selection.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user, get_current_administrator
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.llm_model import (
    ConnectionTestResult,
    LLMModelCreate,
    LLMModelList,
    LLMModelResponse,
    LLMModelSummary,
    LLMModelUpdate,
    ModelAvailableResponse,
    ModelPublicInfo,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.model_registry_service import (
    ModelNotFoundError,
    ModelRegistryService,
    ModelValidationError,
)

logger = structlog.get_logger(__name__)

# Admin router (superuser only)
admin_router = APIRouter(prefix="/admin/models", tags=["Model Registry (Admin)"])

# Public router (authenticated users)
public_router = APIRouter(prefix="/models", tags=["Models"])


def _model_to_response(model, service: ModelRegistryService) -> LLMModelResponse:
    """Convert LLMModel to response schema."""
    return LLMModelResponse(
        id=model.id,
        type=model.type,
        provider=model.provider,
        name=model.name,
        model_id=model.model_id,
        config=model.config,
        api_endpoint=model.api_endpoint,
        status=model.status,
        is_default=model.is_default,
        has_api_key=service.model_has_api_key(model),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _model_to_summary(model, service: ModelRegistryService) -> LLMModelSummary:
    """Convert LLMModel to summary schema."""
    return LLMModelSummary(
        id=model.id,
        type=model.type,
        provider=model.provider,
        name=model.name,
        model_id=model.model_id,
        status=model.status,
        is_default=model.is_default,
        has_api_key=service.model_has_api_key(model),
    )


# =============================================================================
# Admin Endpoints (Superuser Only)
# =============================================================================


@admin_router.get("", response_model=LLMModelList)
async def list_models(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
    type: Annotated[str | None, Query(description="Filter by type")] = None,
    provider: Annotated[str | None, Query(description="Filter by provider")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> LLMModelList:
    """List all registered LLM models.

    AC-7.9.1: Admin Model Registry page lists all registered models with
    name, type, provider, status, and is_default columns.

    Requires superuser role.
    """
    service = ModelRegistryService(db)
    models, total = await service.list_models(
        model_type=type,
        provider=provider,
        status=status,
        skip=skip,
        limit=limit,
    )

    summaries = [_model_to_summary(m, service) for m in models]

    logger.info(
        "admin_models_listed",
        user_id=str(user.id),
        count=len(summaries),
        total=total,
    )

    return LLMModelList(models=summaries, total=total)


@admin_router.post(
    "", response_model=LLMModelResponse, status_code=status.HTTP_201_CREATED
)
async def create_model(
    data: LLMModelCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> LLMModelResponse:
    """Register a new LLM model.

    AC-7.9.2: Clicking "Add Model" opens a modal form.
    AC-7.9.3: Form requires model type selection (Embedding/Generation).
    AC-7.9.4: Provider selection shows appropriate fields.
    AC-7.9.5-7: Complete parameter sets for model types.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)
        model = await service.create_model(data)

        # Audit log
        await audit_service.log_event(
            action="model_created",
            resource_type="llm_model",
            user_id=user.id,
            resource_id=model.id,
            details={
                "type": model.type,
                "provider": model.provider,
                "name": model.name,
                "model_id": model.model_id,
                "is_default": model.is_default,
            },
        )

        logger.info(
            "model_created_by_admin",
            model_id=str(model.id),
            user_id=str(user.id),
            type=model.type,
            provider=model.provider,
        )

        return _model_to_response(model, service)

    except ModelValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@admin_router.get("/{model_id}", response_model=LLMModelResponse)
async def get_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _user: Annotated[User, Depends(get_current_administrator)],
) -> LLMModelResponse:
    """Get details of a specific model.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)
        model = await service.get_model(model_id)
        return _model_to_response(model, service)
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@admin_router.put("/{model_id}", response_model=LLMModelResponse)
async def update_model(
    model_id: UUID,
    data: LLMModelUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> LLMModelResponse:
    """Update a model's configuration.

    AC-7.9.11: Edit and delete buttons available with KB dependency warnings.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)

        # Get old values for audit
        old_model = await service.get_model(model_id)
        old_values = {
            "name": old_model.name,
            "model_id": old_model.model_id,
            "status": old_model.status,
            "is_default": old_model.is_default,
        }

        model = await service.update_model(model_id, data)

        # Audit log
        await audit_service.log_event(
            action="model_updated",
            resource_type="llm_model",
            user_id=user.id,
            resource_id=model.id,
            details={
                "old_values": old_values,
                "new_values": {
                    "name": model.name,
                    "model_id": model.model_id,
                    "status": model.status,
                    "is_default": model.is_default,
                },
            },
        )

        logger.info(
            "model_updated_by_admin",
            model_id=str(model_id),
            user_id=str(user.id),
        )

        return _model_to_response(model, service)

    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ModelValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@admin_router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> None:
    """Delete a model from the registry.

    AC-7.9.11: Delete with KB dependency warnings.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)

        # Get model info for audit before deletion
        model = await service.get_model(model_id)
        model_info = {
            "type": model.type,
            "provider": model.provider,
            "name": model.name,
            "model_id": model.model_id,
        }

        await service.delete_model(model_id)

        # Audit log
        await audit_service.log_event(
            action="model_deleted",
            resource_type="llm_model",
            user_id=user.id,
            resource_id=model_id,
            details=model_info,
        )

        logger.info(
            "model_deleted_by_admin",
            model_id=str(model_id),
            user_id=str(user.id),
        )

    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@admin_router.post("/{model_id}/set-default", response_model=LLMModelResponse)
async def set_model_default(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> LLMModelResponse:
    """Set a model as the default for its type.

    AC-7.9.10: Default model designation with visual indicator.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)
        model = await service.set_default(model_id)

        # Audit log
        await audit_service.log_event(
            action="model_set_default",
            resource_type="llm_model",
            user_id=user.id,
            resource_id=model.id,
            details={
                "type": model.type,
                "name": model.name,
            },
        )

        logger.info(
            "model_set_default_by_admin",
            model_id=str(model_id),
            user_id=str(user.id),
            type=model.type,
        )

        return _model_to_response(model, service)

    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@admin_router.post("/{model_id}/test", response_model=ConnectionTestResult)
async def test_model_connection(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_administrator)],
) -> ConnectionTestResult:
    """Test connection to a model.

    AC-7.9.8: "Test Connection" button validates model accessibility.

    Requires superuser role.
    """
    try:
        service = ModelRegistryService(db)
        model = await service.get_model(model_id)

        # Import here to avoid circular imports
        from app.services.model_connection_tester import test_model_connection

        result = await test_model_connection(model, service)

        logger.info(
            "model_connection_tested",
            model_id=str(model_id),
            user_id=str(user.id),
            success=result.success,
        )

        return result

    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# =============================================================================
# Public Endpoints (Authenticated Users)
# =============================================================================


@public_router.get("/available", response_model=ModelAvailableResponse)
async def get_available_models(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _user: Annotated[User, Depends(current_active_user)],
) -> ModelAvailableResponse:
    """Get available models for KB selection.

    Returns active embedding, generation, and NER models that can be used
    when creating or configuring a knowledge base or entity extraction.

    Requires authentication.
    """
    service = ModelRegistryService(db)

    embedding_models = await service.get_active_models_by_type("embedding")
    generation_models = await service.get_active_models_by_type("generation")
    ner_models = await service.get_active_models_by_type("ner")

    return ModelAvailableResponse(
        embedding_models=[_model_to_summary(m, service) for m in embedding_models],
        generation_models=[_model_to_summary(m, service) for m in generation_models],
        ner_models=[_model_to_summary(m, service) for m in ner_models],
    )


@public_router.get("/embedding", response_model=list[ModelPublicInfo])
async def get_embedding_models(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _user: Annotated[User, Depends(current_active_user)],
) -> list[ModelPublicInfo]:
    """Get active embedding models.

    Returns list of active embedding models with their configurations
    including dimensions and distance metrics.

    Requires authentication.
    """
    service = ModelRegistryService(db)
    models = await service.get_active_models_by_type("embedding")

    return [
        ModelPublicInfo(
            id=m.id,
            name=m.name,
            provider=m.provider,
            model_id=m.model_id,
            config=m.config,
        )
        for m in models
    ]


@public_router.get("/generation", response_model=list[ModelPublicInfo])
async def get_generation_models(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _user: Annotated[User, Depends(current_active_user)],
) -> list[ModelPublicInfo]:
    """Get active generation models.

    Returns list of active generation models with their configurations.

    Requires authentication.
    """
    service = ModelRegistryService(db)
    models = await service.get_active_models_by_type("generation")

    return [
        ModelPublicInfo(
            id=m.id,
            name=m.name,
            provider=m.provider,
            model_id=m.model_id,
            config=m.config,
        )
        for m in models
    ]


@public_router.get("/ner", response_model=list[ModelPublicInfo])
async def get_ner_models(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _user: Annotated[User, Depends(current_active_user)],
) -> list[ModelPublicInfo]:
    """Get active NER (Named Entity Recognition) models.

    Returns list of active NER models with their configurations
    for use in GraphRAG entity extraction pipelines.

    Requires authentication.
    """
    service = ModelRegistryService(db)
    models = await service.get_active_models_by_type("ner")

    return [
        ModelPublicInfo(
            id=m.id,
            name=m.name,
            provider=m.provider,
            model_id=m.model_id,
            config=m.config,
        )
        for m in models
    ]
