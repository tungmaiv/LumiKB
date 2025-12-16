"""Draft API endpoints for editing and managing generated drafts."""

import re
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.permission import PermissionLevel
from app.models.user import User
from app.schemas.draft import (
    AlternativeResponse,
    DraftCreate,
    DraftListResponse,
    DraftResponse,
    DraftUpdate,
    ExportRequest,
    FeedbackRequest,
    RegenerateRequest,
    RegenerateResponse,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.draft_service import DraftService
from app.services.feedback_service import FeedbackService, get_feedback_service
from app.services.kb_service import KBService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/drafts", tags=["drafts"])


def get_draft_service(
    session: AsyncSession = Depends(get_async_session),
) -> DraftService:
    """Dependency injection for DraftService."""
    return DraftService(session)


def get_kb_service(
    session: AsyncSession = Depends(get_async_session),
) -> KBService:
    """Dependency injection for KBService."""
    return KBService(session)


@router.post(
    "",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Knowledge Base not found or no permission"},
        403: {"description": "Insufficient permissions (requires WRITE)"},
    },
)
async def create_draft(
    request: DraftCreate,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> DraftResponse:
    """Create a new draft.

    Creates a new draft associated with a Knowledge Base. Used during
    generation streaming to initialize draft before SSE starts.

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Status State Machine:**
    - Initial: streaming (during generation)
    - After cancel: partial
    - After completion: complete
    - After first edit: editing
    - After export: exported
    """
    # Check WRITE permission
    await kb_service.check_permission(
        user=current_user,
        kb_id=UUID(request.kb_id),
        required_level=PermissionLevel.WRITE,
    )

    draft = await draft_service.create_draft(
        kb_id=UUID(request.kb_id),
        user_id=current_user.id,
        title=request.title,
        template_type=request.template_type,
        content=request.content,
        citations=request.citations,
        status=request.status,
        word_count=request.word_count,
    )

    return DraftResponse.model_validate(draft)


@router.get(
    "",
    response_model=DraftListResponse,
    responses={
        404: {"description": "Knowledge Base not found or no permission"},
    },
)
async def list_drafts(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> DraftListResponse:
    """List all drafts for a Knowledge Base.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Query Parameters:**
    - kb_id: Knowledge Base UUID

    **Response:**
    - drafts: Array of draft responses
    - total: Total number of drafts
    """
    # Check READ permission
    await kb_service.check_permission(
        user=current_user,
        kb_id=UUID(kb_id),
        required_level=PermissionLevel.READ,
    )

    drafts = await draft_service.list_drafts(kb_id=UUID(kb_id))

    return DraftListResponse(
        drafts=[DraftResponse.model_validate(d) for d in drafts],
        total=len(drafts),
    )


@router.get(
    "/{draft_id}",
    response_model=DraftResponse,
    responses={
        404: {"description": "Draft not found or no permission"},
    },
)
async def get_draft(
    draft_id: UUID,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> DraftResponse:
    """Get a single draft by ID.

    **Permissions:** Requires READ permission on the draft's Knowledge Base.
    """
    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check READ permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.READ,
    )

    return DraftResponse.model_validate(draft)


@router.patch(
    "/{draft_id}",
    response_model=DraftResponse,
    responses={
        404: {"description": "Draft not found or no permission"},
        403: {"description": "Insufficient permissions (requires WRITE)"},
        409: {"description": "Conflict: Draft has been modified (optimistic locking)"},
    },
)
async def update_draft(
    draft_id: UUID,
    request: DraftUpdate,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> DraftResponse:
    """Update draft content, citations, and status.

    Used for:
    - Auto-save (every 5s during editing)
    - Manual save (Ctrl+S)
    - Status transitions (complete → editing)

    **Permissions:** Requires WRITE permission on the draft's Knowledge Base.

    **Status Transitions:**
    - complete → editing (on first edit)
    - editing → editing (subsequent saves)

    **Optimistic Locking:**
    Uses `updated_at` for concurrent edit detection. Returns 409 if draft
    was modified by another user/tab since last read.

    **Validation:**
    - Citation markers [n] must match citation numbers in citations array
    - Word count calculated automatically if not provided
    """
    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check WRITE permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.WRITE,
    )

    # Validate citation markers match citations
    citation_numbers = {c.number for c in request.citations}
    marker_regex = r"\[(\d+)\]"
    markers_in_content = {
        int(m.group(1)) for m in re.finditer(marker_regex, request.content)
    }

    if citation_numbers != markers_in_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Citation markers {markers_in_content} do not match citation data {citation_numbers}",
        )

    updated_draft = await draft_service.update_draft(
        draft_id=draft_id,
        content=request.content,
        citations=[c.model_dump() for c in request.citations],
        status=request.status,
        word_count=request.word_count,
    )

    return DraftResponse.model_validate(updated_draft)


@router.post(
    "/{draft_id}/regenerate",
    response_model=RegenerateResponse,
    responses={
        404: {"description": "Draft not found or no permission"},
        403: {"description": "Insufficient permissions (requires WRITE)"},
        400: {"description": "Invalid selection range or request"},
    },
)
async def regenerate_section(
    draft_id: UUID,
    request: RegenerateRequest,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> RegenerateResponse:
    """Regenerate a section of the draft with user instructions.

    Allows users to select text and ask LLM to regenerate it with
    specific instructions (e.g., "Make it more technical").

    **Permissions:** Requires WRITE permission on the draft's Knowledge Base.

    **Request:**
    - selected_text: Original text to regenerate
    - instructions: User instructions for regeneration
    - keep_citations: Preserve existing [n] markers
    - selection_start: Character offset where selection starts
    - selection_end: Character offset where selection ends

    **Response:**
    - regenerated_text: New section content
    - citations: Citations for regenerated section

    **Behavior:**
    - If keep_citations=true: Preserve existing markers, add new ones
    - If keep_citations=false: Replace section entirely with new citations
    - Only selected portion is regenerated, rest of draft preserved
    """
    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check WRITE permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.WRITE,
    )

    # Validate selection range
    if request.selection_start >= request.selection_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="selection_start must be less than selection_end",
        )

    if request.selection_end > len(draft.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"selection_end ({request.selection_end}) exceeds content length ({len(draft.content)})",
        )

    # TODO: Implement actual regeneration with LLM
    # For now, return mock response
    regenerated_text = f"[Regenerated section based on: {request.instructions}]\n{request.selected_text}"
    citations = []

    return RegenerateResponse(
        regenerated_text=regenerated_text,
        citations=citations,
    )


@router.delete(
    "/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Draft not found or no permission"},
        403: {"description": "Insufficient permissions (requires WRITE)"},
    },
)
async def delete_draft(
    draft_id: UUID,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
) -> None:
    """Delete a draft.

    **Permissions:** Requires WRITE permission on the draft's Knowledge Base.
    """
    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check WRITE permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.WRITE,
    )

    await draft_service.delete_draft(draft_id)


@router.post(
    "/{draft_id}/export",
    responses={
        404: {"description": "Draft not found or no permission"},
        403: {"description": "Insufficient permissions (requires READ)"},
        400: {"description": "Invalid export format"},
    },
)
async def export_draft(
    draft_id: UUID,
    request: ExportRequest,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Export draft to DOCX, PDF, or Markdown format.

    Returns file bytes with Content-Disposition header for download.

    **Permissions:** Requires READ permission on the draft's Knowledge Base.

    **Supported Formats:**
    - docx: Microsoft Word with citation footnotes
    - pdf: PDF with citation table at end
    - markdown: Markdown with [^n] footnote syntax

    **Request:**
    - format: "docx" | "pdf" | "markdown"

    **Response:**
    - File download with Content-Disposition header
    - MIME type appropriate for format

    **Audit Logging:**
    - Logs export event with metadata (format, title, citation count)
    - Does NOT log full content (privacy)
    """
    from app.services.export_service import ExportService

    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check READ permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.READ,
    )

    # Validate format
    if request.format not in ["docx", "pdf", "markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Must be docx, pdf, or markdown.",
        )

    # Export to requested format with error logging (AC-7.19.3)
    export_service = ExportService()

    try:
        if request.format == "docx":
            file_bytes = export_service.export_to_docx(draft)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            extension = "docx"
        elif request.format == "pdf":
            file_bytes = export_service.export_to_pdf(draft)
            media_type = "application/pdf"
            extension = "pdf"
        else:  # markdown
            file_content = export_service.export_to_markdown(draft)
            file_bytes = file_content.encode("utf-8")
            media_type = "text/markdown"
            extension = "md"
    except Exception as e:
        # Log export failure (AC-7.19.3)
        await audit_service.log_export_failed(
            user_id=current_user.id,
            draft_id=draft_id,
            export_format=request.format,
            error_message=str(e),
            kb_id=draft.kb_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {e!s}",
        ) from e

    # Generate safe filename
    safe_title = (
        re.sub(r"[^\w\s-]", "", draft.title or "draft").strip().replace(" ", "_")
    )
    filename = f"{safe_title}.{extension}"

    # Log successful export to audit service (AC-7.19.1, AC-7.19.2)
    await audit_service.log_export(
        user_id=current_user.id,
        draft_id=draft_id,
        export_format=request.format,
        citation_count=len(draft.citations) if draft.citations else 0,
        file_size_bytes=len(file_bytes),
        related_request_id=None,  # TODO: Link to generation request_id when Draft model includes it
    )

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/{draft_id}/feedback",
    response_model=AlternativeResponse,
    responses={
        404: {"description": "Draft not found or no permission"},
        403: {"description": "Insufficient permissions (requires READ)"},
        400: {"description": "Invalid feedback type"},
    },
)
async def submit_feedback(
    draft_id: UUID,
    request: FeedbackRequest,
    current_user: User = Depends(current_active_user),
    draft_service: DraftService = Depends(get_draft_service),
    kb_service: KBService = Depends(get_kb_service),
    feedback_service: FeedbackService = Depends(get_feedback_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> AlternativeResponse:
    """Submit feedback on a draft and receive recovery alternatives.

    Returns suggested actions based on feedback type to help users
    recover from poor generation results.

    **Permissions:** Requires READ permission on the draft's Knowledge Base.

    **Feedback Types:**
    - not_relevant: Draft doesn't address context
    - wrong_format: Need different template/structure
    - needs_more_detail: Too high-level, missing specifics
    - low_confidence: Citations seem weak or off-topic
    - other: Custom feedback (requires comments)

    **Response:**
    - alternatives: List of 3 suggested recovery actions

    **Audit Logging:**
    - Logs feedback event with metadata (type, comments, draft stats)
    - Does NOT log full content (privacy)
    """
    draft = await draft_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Check READ permission on KB
    await kb_service.check_permission(
        user=current_user,
        kb_id=draft.kb_id,
        required_level=PermissionLevel.READ,
    )

    # Validate feedback type (redundant with schema validation, but defensive)
    valid_types = [
        "not_relevant",
        "wrong_format",
        "needs_more_detail",
        "low_confidence",
        "other",
    ]
    if request.feedback_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feedback type. Must be one of: {', '.join(valid_types)}",
        )

    # Get alternative suggestions
    try:
        alternatives_list = feedback_service.suggest_alternatives(request.feedback_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log feedback to audit service
    await audit_service.log_feedback(
        user_id=current_user.id,
        draft_id=draft_id,
        feedback_type=request.feedback_type,
        feedback_comments=request.comments,
        related_request_id=None,  # TODO: Link to generation request_id when Draft model includes it
    )

    return AlternativeResponse(alternatives=alternatives_list)
