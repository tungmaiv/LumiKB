"""Document generation API endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.generation import (
    GenerationRequest,
    GenerationResponse,
    TemplateListResponse,
    TemplateSchema,
)
from app.services.generation_service import (
    GenerationService,
    InsufficientSourcesError,
)
from app.services.kb_service import KBPermissionService
from app.services.template_registry import get_template, list_templates

router = APIRouter(prefix="/generate", tags=["generation"])
logger = structlog.get_logger(__name__)


@router.post(
    "",
    response_model=GenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate document from selected sources",
    description="""Generate a professional document using template-based LLM synthesis.

**Requirements:**
- User must have READ permission on the Knowledge Base
- At least 1 source chunk must be selected
- Generation mode must be one of: rfp_response, technical_checklist, requirements_summary, custom

**Process:**
1. Validates user permissions on KB
2. Retrieves selected source chunks from database
3. Builds context using template system prompt + user instructions
4. Calls LLM to generate document with citations
5. Extracts and validates citations
6. Logs generation event for audit trail

**Returns:**
- Generated document with citation markers [1], [2], etc.
- Full citation details for each marker
- Confidence score (0.0-1.0)
- Unique generation_id for audit logging
""",
)
async def generate_document(
    request: GenerationRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> GenerationResponse:
    """Generate document from selected source chunks using template."""
    try:
        # Validate KB exists and user has permission
        kb = await session.get(KnowledgeBase, request.kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge Base {request.kb_id} not found",
            )

        # Check user has READ permission
        permission_service = KBPermissionService()
        has_permission = await permission_service.check_permission(
            session=session,
            user_id=str(current_user.id),
            kb_id=request.kb_id,
            required_permission="READ",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have READ permission for Knowledge Base {request.kb_id}",
            )

        # Generate document
        generation_service = GenerationService()
        result = await generation_service.generate_document(
            session=session,
            request=request,
            user_id=str(current_user.id),
        )

        logger.info(
            "api.generate.success",
            user_id=str(current_user.id),
            kb_id=request.kb_id,
            generation_id=result["generation_id"],
        )

        return GenerationResponse(**result)

    except InsufficientSourcesError as e:
        logger.warning(
            "api.generate.insufficient_sources",
            user_id=str(current_user.id),
            kb_id=request.kb_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e

    except ValueError as e:
        # Invalid generation mode or other validation errors
        logger.warning(
            "api.generate.invalid_request",
            user_id=str(current_user.id),
            kb_id=request.kb_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(
            "api.generate.error",
            user_id=str(current_user.id),
            kb_id=request.kb_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate document. Please try again.",
        ) from e


# Story 4.9: Template endpoints


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all available templates",
    description="""Returns all available document generation templates.

**Authentication:**
- Requires valid Bearer token

**Returns:**
- List of templates with id, name, description, system_prompt, sections, example_output
""",
)
async def get_templates(
    current_user: User = Depends(current_active_user),
) -> TemplateListResponse:
    """List all available templates."""
    templates = list_templates()
    template_schemas = [TemplateSchema(**t.model_dump()) for t in templates]

    logger.info(
        "api.templates.list",
        user_id=str(current_user.id),
        template_count=len(templates),
    )

    return TemplateListResponse(templates=template_schemas)


@router.get(
    "/templates/{template_id}",
    response_model=TemplateSchema,
    status_code=status.HTTP_200_OK,
    summary="Get a specific template by ID",
    description="""Returns a single template by its ID.

**Authentication:**
- Requires valid Bearer token

**Parameters:**
- template_id: One of rfp_response, checklist, gap_analysis, custom

**Returns:**
- Template configuration with all fields

**Errors:**
- 404: Template not found
""",
)
async def get_template_by_id(
    template_id: str,
    current_user: User = Depends(current_active_user),
) -> TemplateSchema:
    """Get a specific template by ID."""
    try:
        template = get_template(template_id)

        logger.info(
            "api.templates.get",
            user_id=str(current_user.id),
            template_id=template_id,
        )

        return TemplateSchema(**template.model_dump())

    except ValueError as e:
        logger.warning(
            "api.templates.not_found",
            user_id=str(current_user.id),
            template_id=template_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        ) from e
