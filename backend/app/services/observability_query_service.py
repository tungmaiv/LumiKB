"""Observability Query Service for Admin API.

Story 9-7: Observability Admin API

Provides read-only query methods for observability data. Separated from the
main ObservabilityService which handles fire-and-forget writes.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import (
    DocumentEvent,
    ObsChatMessage,
    Span,
    Trace,
)
from app.schemas.observability import (
    ChatHistoryResponse,
    ChatMessageItem,
    ChatMetrics,
    ChatSessionItem,
    ChatSessionsResponse,
    CitationItem,
    DocumentEventItem,
    DocumentTimelineResponse,
    LLMUsageStats,
    ObservabilityStatsResponse,
    ProcessingMetrics,
    SpanDetail,
    TraceDetailResponse,
    TraceListItem,
    TraceListResponse,
)

logger = structlog.get_logger(__name__)


class ObservabilityQueryService:
    """Query service for observability data.

    Provides read-only methods for querying traces, spans, chat messages,
    document events, and aggregated statistics.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the query service.

        Args:
            session: Async SQLAlchemy session for database queries.
        """
        self.session = session

    async def list_traces(
        self,
        operation_type: str | None = None,
        status: str | None = None,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> TraceListResponse:
        """List traces with filters and pagination.

        Args:
            operation_type: Filter by trace name/operation type.
            status: Filter by trace status.
            user_id: Filter by user ID.
            kb_id: Filter by knowledge base ID.
            start_date: Filter traces starting after this date.
            end_date: Filter traces starting before this date.
            search: Search in trace ID or name (case-insensitive).
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            TraceListResponse with paginated trace items.
        """
        from sqlalchemy import or_

        # Build base query
        query = select(Trace)

        # Apply filters
        if operation_type:
            query = query.where(Trace.name == operation_type)
        if status:
            query = query.where(Trace.status == status)
        if user_id:
            query = query.where(Trace.user_id == user_id)
        if kb_id:
            query = query.where(Trace.kb_id == kb_id)
        if start_date:
            query = query.where(Trace.timestamp >= start_date)
        if end_date:
            query = query.where(Trace.timestamp <= end_date)
        if search:
            # Search in trace_id, name, or document_id (case-insensitive)
            search_pattern = f"%{search}%"
            # Use JSONB ->> operator to extract document_id as text for searching
            query = query.where(
                or_(
                    Trace.trace_id.ilike(search_pattern),
                    Trace.name.ilike(search_pattern),
                    Trace.attributes["document_id"].astext.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Trace.timestamp.desc()).offset(skip).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        traces = result.scalars().all()

        # Get span counts for each trace
        trace_ids = [t.trace_id for t in traces]
        span_counts: dict[str, int] = {}

        if trace_ids:
            span_count_query = (
                select(Span.trace_id, func.count(Span.span_id))
                .where(Span.trace_id.in_(trace_ids))
                .group_by(Span.trace_id)
            )
            span_result = await self.session.execute(span_count_query)
            span_counts = {row[0]: row[1] for row in span_result.all()}

        # Build response items
        items = [
            TraceListItem(
                trace_id=trace.trace_id,
                name=trace.name,
                status=trace.status,
                user_id=trace.user_id,
                kb_id=trace.kb_id,
                document_id=self._extract_document_id(trace.attributes),
                started_at=trace.timestamp,
                ended_at=self._calculate_end_time(trace.timestamp, trace.duration_ms),
                duration_ms=trace.duration_ms,
                span_count=span_counts.get(trace.trace_id, 0),
            )
            for trace in traces
        ]

        return TraceListResponse(items=items, total=total, skip=skip, limit=limit)

    async def get_trace_with_spans(self, trace_id: str) -> TraceDetailResponse | None:
        """Get trace detail with all child spans.

        Args:
            trace_id: W3C trace ID (32 hex characters).

        Returns:
            TraceDetailResponse with spans, or None if not found.
        """
        # Get trace
        trace_query = select(Trace).where(Trace.trace_id == trace_id)
        trace_result = await self.session.execute(trace_query)
        trace = trace_result.scalar_one_or_none()

        if trace is None:
            return None

        # Get spans ordered by timestamp
        spans_query = (
            select(Span).where(Span.trace_id == trace_id).order_by(Span.timestamp.asc())
        )
        spans_result = await self.session.execute(spans_query)
        spans = spans_result.scalars().all()

        # Build span details
        span_details = [
            SpanDetail(
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                name=span.name,
                span_type=span.span_type,
                status=span.status,
                started_at=span.timestamp,
                ended_at=self._calculate_end_time(span.timestamp, span.duration_ms),
                duration_ms=span.duration_ms,
                input_tokens=span.input_tokens,
                output_tokens=span.output_tokens,
                model=span.model,
                error_message=span.error_message,
                metadata=span.attributes,
            )
            for span in spans
        ]

        return TraceDetailResponse(
            trace_id=trace.trace_id,
            name=trace.name,
            status=trace.status,
            user_id=trace.user_id,
            kb_id=trace.kb_id,
            started_at=trace.timestamp,
            ended_at=self._calculate_end_time(trace.timestamp, trace.duration_ms),
            duration_ms=trace.duration_ms,
            metadata=trace.attributes,
            spans=span_details,
        )

    async def list_chat_messages(
        self,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        session_id: str | None = None,
        search_query: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ChatHistoryResponse:
        """List chat messages with filters and pagination.

        Args:
            user_id: Filter by user ID.
            kb_id: Filter by knowledge base ID.
            session_id: Filter by conversation session ID.
            search_query: Search within message content (case-insensitive).
            start_date: Filter messages after this date.
            end_date: Filter messages before this date.
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            ChatHistoryResponse with paginated message items.
        """
        # Build base query
        query = select(ObsChatMessage)

        # Apply filters
        if user_id:
            query = query.where(ObsChatMessage.user_id == user_id)
        if kb_id:
            query = query.where(ObsChatMessage.kb_id == kb_id)
        if session_id:
            query = query.where(ObsChatMessage.conversation_id == session_id)
        if search_query:
            # Use ILIKE for case-insensitive search
            query = query.where(ObsChatMessage.content.ilike(f"%{search_query}%"))
        if start_date:
            query = query.where(ObsChatMessage.timestamp >= start_date)
        if end_date:
            query = query.where(ObsChatMessage.timestamp <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(ObsChatMessage.timestamp.desc()).offset(skip).limit(limit)
        )

        # Execute query
        result = await self.session.execute(query)
        messages = result.scalars().all()

        # Build response items
        items = [
            ChatMessageItem(
                id=msg.id,
                trace_id=msg.trace_id,
                session_id=str(msg.conversation_id) if msg.conversation_id else None,
                role=msg.role,
                content=msg.content,
                user_id=msg.user_id,
                kb_id=msg.kb_id,
                created_at=msg.timestamp,
                token_count=(
                    (msg.input_tokens or 0) + (msg.output_tokens or 0)
                    if msg.role == "assistant"
                    else None
                ),
                response_time_ms=msg.latency_ms if msg.role == "assistant" else None,
                citations=self._extract_citations(msg.attributes),
                debug_info=self._extract_debug_info(msg.attributes),
            )
            for msg in messages
        ]

        return ChatHistoryResponse(items=items, total=total, skip=skip, limit=limit)

    async def list_chat_sessions(
        self,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        search_query: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> ChatSessionsResponse:
        """List chat sessions (grouped by conversation_id) with filters and pagination.

        Args:
            user_id: Filter by user ID.
            kb_id: Filter by knowledge base ID.
            search_query: Search within message content (case-insensitive).
            start_date: Filter sessions with messages after this date.
            end_date: Filter sessions with messages before this date.
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            ChatSessionsResponse with paginated session items.
        """
        from app.models.knowledge_base import KnowledgeBase
        from app.models.user import User

        # Build base filter conditions
        base_filter = []
        if user_id:
            base_filter.append(ObsChatMessage.user_id == user_id)
        if kb_id:
            base_filter.append(ObsChatMessage.kb_id == kb_id)
        if search_query:
            base_filter.append(ObsChatMessage.content.ilike(f"%{search_query}%"))
        if start_date:
            base_filter.append(ObsChatMessage.timestamp >= start_date)
        if end_date:
            base_filter.append(ObsChatMessage.timestamp <= end_date)

        # Get unique conversation IDs with aggregated data
        session_query = select(
            ObsChatMessage.conversation_id,
            ObsChatMessage.user_id,
            ObsChatMessage.kb_id,
            func.count(ObsChatMessage.id).label("message_count"),
            func.max(ObsChatMessage.timestamp).label("last_message_at"),
            func.min(ObsChatMessage.timestamp).label("first_message_at"),
        ).where(ObsChatMessage.conversation_id.isnot(None))

        if base_filter:
            session_query = session_query.where(*base_filter)

        session_query = session_query.group_by(
            ObsChatMessage.conversation_id,
            ObsChatMessage.user_id,
            ObsChatMessage.kb_id,
        )

        # Get total count
        count_subquery = session_query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering (newest sessions first)
        session_query = (
            session_query.order_by(func.max(ObsChatMessage.timestamp).desc())
            .offset(skip)
            .limit(limit)
        )

        # Execute query
        result = await self.session.execute(session_query)
        sessions = result.all()

        # Collect user_ids and kb_ids for name lookup
        user_ids = {s.user_id for s in sessions if s.user_id}
        kb_ids = {s.kb_id for s in sessions if s.kb_id}

        # Fetch user names (User model only has email, no full_name)
        user_names: dict[UUID, str] = {}
        if user_ids:
            user_query = select(User.id, User.email).where(User.id.in_(user_ids))
            user_result = await self.session.execute(user_query)
            for row in user_result.all():
                user_names[row.id] = row.email

        # Fetch KB names
        kb_names: dict[UUID, str] = {}
        if kb_ids:
            kb_query = select(KnowledgeBase.id, KnowledgeBase.name).where(
                KnowledgeBase.id.in_(kb_ids)
            )
            kb_result = await self.session.execute(kb_query)
            for row in kb_result.all():
                kb_names[row.id] = row.name

        # Build response items
        items = [
            ChatSessionItem(
                session_id=str(s.conversation_id),
                user_id=s.user_id,
                user_name=user_names.get(s.user_id) if s.user_id else None,
                kb_id=s.kb_id,
                kb_name=kb_names.get(s.kb_id) if s.kb_id else None,
                message_count=s.message_count,
                last_message_at=s.last_message_at,
                first_message_at=s.first_message_at,
            )
            for s in sessions
        ]

        return ChatSessionsResponse(items=items, total=total, skip=skip, limit=limit)

    async def get_document_timeline(
        self, document_id: UUID
    ) -> DocumentTimelineResponse:
        """Get document processing events timeline.

        Args:
            document_id: Document UUID.

        Returns:
            DocumentTimelineResponse with events ordered by timestamp.
        """
        # Get all events for the document
        query = (
            select(DocumentEvent)
            .where(DocumentEvent.document_id == document_id)
            .order_by(DocumentEvent.timestamp.asc())
        )
        result = await self.session.execute(query)
        events = result.scalars().all()

        # Build event items
        event_items = [
            DocumentEventItem(
                id=event.id,
                trace_id=event.trace_id,
                step_name=event.event_type,
                status=event.status,
                started_at=event.timestamp,
                ended_at=self._calculate_end_time(event.timestamp, event.duration_ms),
                duration_ms=event.duration_ms,
                metrics=self._build_event_metrics(event),
                error_message=event.error_message,
            )
            for event in events
        ]

        # Calculate total duration
        total_duration_ms = None
        if events:
            completed_events = [e for e in events if e.duration_ms is not None]
            if completed_events:
                total_duration_ms = sum(
                    e.duration_ms for e in completed_events if e.duration_ms
                )

        return DocumentTimelineResponse(
            document_id=document_id,
            events=event_items,
            total_duration_ms=total_duration_ms,
        )

    async def get_aggregated_stats(
        self,
        time_period: str = "day",
        kb_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> ObservabilityStatsResponse:
        """Get aggregated observability statistics.

        Args:
            time_period: Aggregation period (hour, day, week, month).
            kb_id: Optional filter by knowledge base ID.
            user_id: Optional filter by user ID.

        Returns:
            ObservabilityStatsResponse with aggregated metrics.
        """
        # Calculate date range based on time period
        now = datetime.now(UTC)
        period_deltas = {
            "hour": timedelta(hours=1),
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
            "month": timedelta(days=30),
        }
        delta = period_deltas.get(time_period, timedelta(days=1))
        start_date = now - delta
        end_date = now

        # Get LLM usage stats from spans
        llm_usage = await self._get_llm_usage_stats(
            start_date, end_date, kb_id, user_id
        )

        # Get processing metrics from document events
        processing_metrics = await self._get_processing_metrics(
            start_date, end_date, kb_id, user_id
        )

        # Get chat metrics from chat messages
        chat_metrics = await self._get_chat_metrics(
            start_date, end_date, kb_id, user_id
        )

        # Get error rate from traces
        error_rate = await self._get_error_rate(start_date, end_date, kb_id, user_id)

        return ObservabilityStatsResponse(
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            llm_usage=llm_usage,
            processing_metrics=processing_metrics,
            chat_metrics=chat_metrics,
            error_rate=error_rate,
        )

    # ========================================================================
    # Private helper methods
    # ========================================================================

    def _calculate_end_time(
        self, start_time: datetime, duration_ms: int | None
    ) -> datetime | None:
        """Calculate end time from start time and duration."""
        if duration_ms is None:
            return None
        return start_time + timedelta(milliseconds=duration_ms)

    def _extract_document_id(self, attributes: dict[str, Any] | None) -> UUID | None:
        """Extract document_id from trace attributes/metadata."""
        if not attributes:
            return None
        doc_id = attributes.get("document_id")
        if doc_id is None:
            return None
        if isinstance(doc_id, UUID):
            return doc_id
        try:
            return UUID(str(doc_id))
        except (ValueError, TypeError):
            return None

    def _extract_citations(
        self, attributes: dict[str, Any] | None
    ) -> list[CitationItem] | None:
        """Extract citation items from message attributes."""
        if not attributes or "citations" not in attributes:
            return None

        citations = attributes.get("citations", [])
        if not citations:
            return None

        return [
            CitationItem(
                index=c.get("index", i + 1),
                document_id=c.get("document_id", ""),
                document_name=c.get("document_name"),
                chunk_id=c.get("chunk_id"),
                relevance_score=c.get("relevance_score"),
            )
            for i, c in enumerate(citations)
        ]

    def _extract_debug_info(
        self, attributes: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Extract debug info from message attributes.

        Debug info is stored when KB has debug_mode enabled and includes:
        - kb_params: System prompt preview, citation style, response language
        - chunks_retrieved: List of chunks with document IDs and scores
        - timing: Retrieval and context assembly timing in ms
        """
        if not attributes or "debug_info" not in attributes:
            return None

        return attributes.get("debug_info")

    def _build_event_metrics(self, event: DocumentEvent) -> dict[str, Any] | None:
        """Build metrics dict from document event fields."""
        metrics: dict[str, Any] = {}

        if event.chunk_count is not None:
            metrics["chunk_count"] = event.chunk_count
        if event.token_count is not None:
            metrics["token_count"] = event.token_count
        if event.attributes:
            metrics.update(event.attributes)

        return metrics if metrics else None

    async def _get_llm_usage_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        kb_id: UUID | None,  # noqa: ARG002 - reserved for future filtering via trace join
        user_id: UUID | None,  # noqa: ARG002 - reserved for future filtering via trace join
    ) -> LLMUsageStats:
        """Get LLM usage statistics from spans.

        Note: kb_id and user_id are reserved for future filtering via trace join.
        Currently spans don't directly reference kb/user but traces do.
        """
        # Query LLM spans
        query = (
            select(
                func.count(Span.span_id).label("total_requests"),
                func.coalesce(func.sum(Span.input_tokens), 0).label(
                    "total_input_tokens"
                ),
                func.coalesce(func.sum(Span.output_tokens), 0).label(
                    "total_output_tokens"
                ),
                func.avg(Span.duration_ms).label("avg_latency_ms"),
            )
            .where(Span.span_type == "llm")
            .where(Span.timestamp >= start_date)
            .where(Span.timestamp <= end_date)
        )

        result = await self.session.execute(query)
        row = result.one()

        # Get breakdown by model
        model_query = (
            select(
                Span.model,
                func.count(Span.span_id).label("requests"),
                func.coalesce(func.sum(Span.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(Span.output_tokens), 0).label("output_tokens"),
            )
            .where(Span.span_type == "llm")
            .where(Span.timestamp >= start_date)
            .where(Span.timestamp <= end_date)
            .where(Span.model.isnot(None))
            .group_by(Span.model)
        )

        model_result = await self.session.execute(model_query)
        by_model = {
            model_row.model: {
                "requests": model_row.requests,
                "input_tokens": model_row.input_tokens,
                "output_tokens": model_row.output_tokens,
            }
            for model_row in model_result.all()
            if model_row.model
        }

        return LLMUsageStats(
            total_requests=row.total_requests or 0,
            total_input_tokens=row.total_input_tokens or 0,
            total_output_tokens=row.total_output_tokens or 0,
            avg_latency_ms=float(row.avg_latency_ms) if row.avg_latency_ms else None,
            by_model=by_model,
        )

    async def _get_processing_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        kb_id: UUID | None,
        user_id: UUID | None,  # noqa: ARG002 - document events don't have user_id
    ) -> ProcessingMetrics:
        """Get document processing metrics from events.

        Note: user_id is not used because DocumentEvent doesn't track user_id directly.
        """
        # Base filter
        base_filter = [
            DocumentEvent.timestamp >= start_date,
            DocumentEvent.timestamp <= end_date,
        ]
        if kb_id:
            base_filter.append(DocumentEvent.kb_id == kb_id)

        # Count unique documents
        doc_count_query = select(
            func.count(func.distinct(DocumentEvent.document_id))
        ).where(*base_filter)
        doc_result = await self.session.execute(doc_count_query)
        total_documents = doc_result.scalar() or 0

        # Count total chunks from chunk events
        chunk_query = (
            select(func.coalesce(func.sum(DocumentEvent.chunk_count), 0))
            .where(*base_filter)
            .where(DocumentEvent.event_type == "chunk")
        )
        chunk_result = await self.session.execute(chunk_query)
        total_chunks = chunk_result.scalar() or 0

        # Average processing time
        avg_time_query = (
            select(func.avg(DocumentEvent.duration_ms))
            .where(*base_filter)
            .where(DocumentEvent.duration_ms.isnot(None))
        )
        avg_result = await self.session.execute(avg_time_query)
        avg_processing_time_ms = avg_result.scalar()

        # Success/failure counts
        status_query = (
            select(DocumentEvent.status, func.count(DocumentEvent.id))
            .where(*base_filter)
            .group_by(DocumentEvent.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}

        return ProcessingMetrics(
            total_documents=total_documents,
            total_chunks=total_chunks,
            avg_processing_time_ms=float(avg_processing_time_ms)
            if avg_processing_time_ms
            else None,
            success_count=status_counts.get("completed", 0),
            failure_count=status_counts.get("failed", 0),
        )

    async def _get_chat_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        kb_id: UUID | None,
        user_id: UUID | None,
    ) -> ChatMetrics:
        """Get chat activity metrics from messages."""
        # Base filter
        base_filter = [
            ObsChatMessage.timestamp >= start_date,
            ObsChatMessage.timestamp <= end_date,
        ]
        if kb_id:
            base_filter.append(ObsChatMessage.kb_id == kb_id)
        if user_id:
            base_filter.append(ObsChatMessage.user_id == user_id)

        # Total messages
        msg_count_query = select(func.count(ObsChatMessage.id)).where(*base_filter)
        msg_result = await self.session.execute(msg_count_query)
        total_messages = msg_result.scalar() or 0

        # Unique conversations
        conv_count_query = select(
            func.count(func.distinct(ObsChatMessage.conversation_id))
        ).where(*base_filter)
        conv_result = await self.session.execute(conv_count_query)
        total_conversations = conv_result.scalar() or 0

        # Average response time (assistant messages only)
        avg_time_query = (
            select(func.avg(ObsChatMessage.latency_ms))
            .where(*base_filter)
            .where(ObsChatMessage.role == "assistant")
            .where(ObsChatMessage.latency_ms.isnot(None))
        )
        avg_time_result = await self.session.execute(avg_time_query)
        avg_response_time_ms = avg_time_result.scalar()

        # Average tokens per response
        avg_tokens_query = (
            select(
                func.avg(
                    func.coalesce(ObsChatMessage.input_tokens, 0)
                    + func.coalesce(ObsChatMessage.output_tokens, 0)
                )
            )
            .where(*base_filter)
            .where(ObsChatMessage.role == "assistant")
        )
        avg_tokens_result = await self.session.execute(avg_tokens_query)
        avg_tokens = avg_tokens_result.scalar()

        return ChatMetrics(
            total_messages=total_messages,
            total_conversations=total_conversations,
            avg_response_time_ms=float(avg_response_time_ms)
            if avg_response_time_ms
            else None,
            avg_tokens_per_response=float(avg_tokens) if avg_tokens else None,
        )

    async def _get_error_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        kb_id: UUID | None,
        user_id: UUID | None,
    ) -> float:
        """Calculate error rate from traces."""
        # Base filter
        base_filter = [
            Trace.timestamp >= start_date,
            Trace.timestamp <= end_date,
        ]
        if kb_id:
            base_filter.append(Trace.kb_id == kb_id)
        if user_id:
            base_filter.append(Trace.user_id == user_id)

        # Total and failed counts
        count_query = select(
            func.count(Trace.trace_id).label("total"),
            func.count(Trace.trace_id).filter(Trace.status == "failed").label("failed"),
        ).where(*base_filter)
        result = await self.session.execute(count_query)
        row = result.one()

        total = row.total or 0
        failed = row.failed or 0

        if total == 0:
            return 0.0

        return round((failed / total) * 100, 2)
