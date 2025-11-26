"""Search API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.auth import current_active_user
from app.models.user import User
from app.schemas.search import (
    ExplainRequest,
    ExplanationResponse,
    QuickSearchRequest,
    QuickSearchResponse,
    SearchRequest,
    SearchResponse,
    SimilarSearchRequest,
)
from app.services.explanation_service import (
    ExplanationService,
    get_explanation_service,
)
from app.services.search_service import SearchService, get_search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
@router.post("/", response_model=SearchResponse)
async def search(
    request_body: SearchRequest,
    stream: bool = Query(
        default=False, description="Enable SSE streaming for real-time results"
    ),
    current_user: User = Depends(current_active_user),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse | StreamingResponse:
    """Semantic search endpoint with optional SSE streaming.

    Searches across specified Knowledge Bases using natural language queries.
    Returns relevant chunks with metadata, or optionally streams results via SSE.

    Args:
        request_body: Search request with query and optional filters
        stream: If True, return SSE stream. If False, return complete SearchResponse (AC1, AC8)
        current_user: Authenticated user
        service: Search service dependency

    Returns:
        If stream=False: SearchResponse with complete results (backward compatible)
        If stream=True: StreamingResponse with text/event-stream (SSE events)

    Raises:
        HTTPException: 404 if KB not found or unauthorized, 503 if services unavailable

    Example streaming request:
        POST /api/v1/search?stream=true
        {"query": "authentication approach", "kb_ids": ["kb-123"]}

    SSE Event Sequence:
        1. StatusEvent - "Searching knowledge bases..."
        2. StatusEvent - "Generating answer..."
        3. TokenEvent* - Answer tokens word-by-word
        4. CitationEvent* - Citation metadata when [n] detected
        5. DoneEvent - Completion with confidence and result_count
    """
    try:
        result = await service.search(
            query=request_body.query,
            kb_ids=request_body.kb_ids,
            user_id=str(current_user.id),
            limit=request_body.limit,
            stream=stream,
        )

        # If streaming, return SSE response (AC1)
        if stream and hasattr(result, "__aiter__"):

            async def event_generator():
                """Convert SSEEvent objects to SSE format strings."""
                try:
                    async for event in result:
                        yield event.to_sse_format()
                except Exception:
                    # If error occurs during streaming, yield error event
                    from app.schemas.sse import ErrorEvent

                    error_event = ErrorEvent(
                        message="Streaming error occurred", code="STREAM_ERROR"
                    )
                    yield error_event.to_sse_format()

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",  # AC1
                    "Connection": "keep-alive",  # AC1
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                },
            )

        # Non-streaming mode - return JSON (AC8, backward compatible)
        return result

    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail="Search temporarily unavailable. Please try again in a moment.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.post("/quick", response_model=QuickSearchResponse)
async def quick_search_route(
    request_body: QuickSearchRequest,
    current_user: User = Depends(current_active_user),
    service: SearchService = Depends(get_search_service),
) -> QuickSearchResponse:
    """Quick search endpoint for command palette (Story 3.7, AC2).

    Lightweight search that returns top 5 results without LLM answer synthesis.
    Optimized for speed - skips CitationService and answer generation.

    Args:
        request_body: Quick search request with query and optional kb_ids
        current_user: Authenticated user
        service: Search service dependency

    Returns:
        QuickSearchResponse with top 5 results, no answer/citations

    Raises:
        HTTPException: 404 if KB not found or unauthorized, 503 if services unavailable
    """
    try:
        result = await service.quick_search(
            query=request_body.query,
            kb_ids=request_body.kb_ids,
            user_id=str(current_user.id),
        )
        return result

    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail="Search temporarily unavailable. Please try again in a moment.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Quick search failed: {str(e)}"
        ) from e


@router.post("/similar", response_model=SearchResponse)
async def similar_search_route(
    request_body: SimilarSearchRequest,
    current_user: User = Depends(current_active_user),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Similar search endpoint (Story 3.8, AC5).

    Finds content similar to a specific chunk using its pre-computed embedding.
    Excludes the original chunk from results.

    Args:
        request_body: Similar search request with chunk_id and optional filters
        current_user: Authenticated user
        service: Search service dependency

    Returns:
        SearchResponse with similar chunks

    Raises:
        HTTPException: 404 if chunk not found or user lacks access
                      503 if services unavailable
    """
    try:
        result = await service.similar_search(
            chunk_id=request_body.chunk_id,
            kb_ids=request_body.kb_ids,
            user_id=str(current_user.id),
            limit=request_body.limit,
        )
        return result

    except ValueError as e:
        # Chunk not found (AC6)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        # User lacks access to KB containing chunk (AC6)
        raise HTTPException(
            status_code=404, detail="Source content no longer available"
        ) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail="Search temporarily unavailable. Please try again in a moment.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Similar search failed: {str(e)}"
        ) from e


@router.post("/explain", response_model=ExplanationResponse)
async def explain_relevance(
    request_body: ExplainRequest,
    current_user: User = Depends(current_active_user),  # noqa: ARG001 - required for auth
    service: ExplanationService = Depends(get_explanation_service),
) -> ExplanationResponse:
    """Explain why a search result is relevant (Story 3.9, AC4).

    Generates a relevance explanation for a specific chunk:
    - Matching keywords (with stemming)
    - Semantic similarity factors
    - Related documents from same KB
    - Section context

    Explanations are cached in Redis with 1 hour TTL (AC5).

    Args:
        request_body: Explanation request with query, chunk_id, chunk_text, etc.
        current_user: Authenticated user
        service: Explanation service dependency

    Returns:
        ExplanationResponse with keywords, explanation, concepts, related documents

    Raises:
        HTTPException: 404 if chunk not found
                      503 if services unavailable
    """
    try:
        result = await service.explain(
            query=request_body.query,
            chunk_id=request_body.chunk_id,
            chunk_text=request_body.chunk_text,
            relevance_score=request_body.relevance_score,
            kb_id=request_body.kb_id,
        )
        return result

    except ValueError as e:
        # Chunk not found (AC6)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail="Explanation service temporarily unavailable. Please try again in a moment.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Explanation failed: {str(e)}"
        ) from e
