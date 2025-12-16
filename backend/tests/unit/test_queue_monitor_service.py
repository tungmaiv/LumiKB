"""Unit tests for QueueMonitorService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.queue_monitor_service import QueueMonitorService


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


@pytest.fixture
def mock_celery_inspect():
    """Mock Celery inspect API."""
    inspect = MagicMock()
    inspect.active = MagicMock(
        return_value={
            "worker1@localhost": [
                {
                    "id": "task-1",
                    "name": "app.workers.document_tasks.process_document",
                    "time_start": 1701523200.0,
                    "delivery_info": {"routing_key": "document_processing"},
                }
            ],
            "worker2@localhost": [],
        }
    )
    inspect.reserved = MagicMock(
        return_value={
            "worker1@localhost": [
                {
                    "id": "task-2",
                    "name": "app.workers.document_tasks.process_document",
                    "delivery_info": {"routing_key": "document_processing"},
                }
            ],
        }
    )
    inspect.stats = MagicMock(
        return_value={
            "worker1@localhost": {"total": {"tasks.process_document": 42}},
            "worker2@localhost": {"total": {"tasks.process_document": 10}},
        }
    )
    return inspect


class TestQueueMonitorService:
    """Test suite for QueueMonitorService."""

    @pytest.mark.asyncio
    async def test_get_all_queues_cache_hit(self, mock_redis):
        """Test cache hit returns cached queue status."""
        import json

        cached_data = [
            {
                "queue_name": "document_processing",
                "pending_tasks": 5,
                "active_tasks": 2,
                "workers": [],
                "status": "available",
            }
        ]
        mock_redis.get.return_value = json.dumps(cached_data)

        with patch(
            "app.services.queue_monitor_service.get_redis_client",
            return_value=mock_redis,
        ):
            service = QueueMonitorService()
            result = await service.get_all_queues()

        assert len(result) == 1
        assert result[0].queue_name == "document_processing"
        assert result[0].pending_tasks == 5
        assert result[0].active_tasks == 2
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_queues_cache_miss(self, mock_redis, mock_celery_inspect):
        """Test cache miss queries Celery inspect API."""
        mock_redis.get.return_value = None

        with (
            patch(
                "app.services.queue_monitor_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch.object(
                QueueMonitorService,
                "_get_celery_inspect",
                return_value=mock_celery_inspect,
            ),
        ):
            service = QueueMonitorService()
            result = await service.get_all_queues()

        assert len(result) >= 1
        # Find document_processing queue
        doc_queue = next(
            (q for q in result if q.queue_name == "document_processing"), None
        )
        assert doc_queue is not None
        assert doc_queue.active_tasks == 1
        assert doc_queue.pending_tasks == 1
        assert doc_queue.status == "available"
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_queues_redis_unavailable(self, mock_celery_inspect):
        """Test fallback to direct Celery inspect when Redis unavailable."""
        mock_redis_error = AsyncMock()
        mock_redis_error.get.side_effect = ConnectionError("Redis down")

        with (
            patch(
                "app.services.queue_monitor_service.get_redis_client",
                return_value=mock_redis_error,
            ),
            patch.object(
                QueueMonitorService,
                "_get_celery_inspect",
                return_value=mock_celery_inspect,
            ),
        ):
            service = QueueMonitorService()
            result = await service.get_all_queues()

        assert len(result) >= 1
        # Verify we still get results despite Redis failure
        doc_queue = next(
            (q for q in result if q.queue_name == "document_processing"), None
        )
        assert doc_queue is not None

    @pytest.mark.asyncio
    async def test_get_all_queues_celery_broker_unavailable(self, mock_redis):
        """Test graceful degradation when Celery broker unavailable."""
        mock_redis.get.return_value = None
        mock_inspect_none = MagicMock()
        mock_inspect_none.active.return_value = None
        mock_inspect_none.reserved.return_value = None
        mock_inspect_none.stats.return_value = None

        with (
            patch(
                "app.services.queue_monitor_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch.object(
                QueueMonitorService,
                "_get_celery_inspect",
                return_value=mock_inspect_none,
            ),
        ):
            service = QueueMonitorService()
            result = await service.get_all_queues()

        # Should return configured queues with unavailable status
        assert len(result) >= 1
        for queue in result:
            assert queue.status == "unavailable"
            assert queue.pending_tasks == 0
            assert queue.active_tasks == 0
            assert queue.workers == []

    @pytest.mark.asyncio
    async def test_get_queue_tasks_success(self, mock_celery_inspect):
        """Test getting task details for a specific queue."""
        with patch.object(
            QueueMonitorService, "_get_celery_inspect", return_value=mock_celery_inspect
        ):
            service = QueueMonitorService()
            result = await service.get_queue_tasks("document_processing")

        assert len(result) == 1
        task = result[0]
        assert task.task_id == "task-1"
        assert task.task_name == "app.workers.document_tasks.process_document"
        assert task.status == "active"
        assert task.started_at is not None
        assert task.estimated_duration is not None

    @pytest.mark.asyncio
    async def test_get_queue_tasks_empty_queue(self, mock_celery_inspect):
        """Test empty task list for queue with no active tasks."""
        with patch.object(
            QueueMonitorService, "_get_celery_inspect", return_value=mock_celery_inspect
        ):
            service = QueueMonitorService()
            result = await service.get_queue_tasks("default")

        # No tasks in default queue based on mock data
        assert result == []

    @pytest.mark.asyncio
    async def test_get_queue_tasks_broker_unavailable(self):
        """Test graceful degradation when Celery broker unavailable."""
        mock_inspect_none = MagicMock()
        mock_inspect_none.active.return_value = None

        with patch.object(
            QueueMonitorService, "_get_celery_inspect", return_value=mock_inspect_none
        ):
            service = QueueMonitorService()
            result = await service.get_queue_tasks("document_processing")

        assert result == []

    def test_is_worker_online_with_stats(self):
        """Test worker marked online if stats available."""
        service = QueueMonitorService()
        worker_stats = {"total": {"tasks": 10}}
        assert service._is_worker_online(worker_stats) is True

    def test_is_worker_online_without_stats(self):
        """Test worker marked offline if no stats."""
        service = QueueMonitorService()
        worker_stats = {}
        assert service._is_worker_online(worker_stats) is False

    def test_parse_timestamp_valid(self):
        """Test parsing valid Unix timestamp."""
        service = QueueMonitorService()
        timestamp = 1701523200.0
        result = service._parse_timestamp(timestamp)
        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC

    def test_parse_timestamp_none(self):
        """Test parsing None timestamp."""
        service = QueueMonitorService()
        result = service._parse_timestamp(None)
        assert result is None

    def test_calculate_duration_valid(self):
        """Test calculating elapsed duration."""
        service = QueueMonitorService()
        # Recent timestamp (should be < 60s ago for test to pass)
        recent = datetime.now(UTC).timestamp() - 5.0
        result = service._calculate_duration(recent)
        assert result is not None
        assert result >= 5000  # At least 5 seconds in ms
        assert result < 10000  # Less than 10 seconds

    def test_calculate_duration_none(self):
        """Test calculating duration with None timestamp."""
        service = QueueMonitorService()
        result = service._calculate_duration(None)
        assert result is None


# =============================================================================
# Story 7-27: Queue Monitoring Enhancement Tests
# =============================================================================


class TestExtractDocumentId:
    """Tests for _extract_document_id (Story 7-27)."""

    def test_extract_from_args(self):
        """
        GIVEN: Task with document_id as first positional arg
        WHEN: _extract_document_id is called
        THEN: Returns UUID
        """
        from uuid import uuid4

        service = QueueMonitorService()
        doc_id = uuid4()
        task = {"args": [str(doc_id), "kb-id-456"]}

        result = service._extract_document_id(task)
        assert result == doc_id

    def test_extract_from_kwargs(self):
        """
        GIVEN: Task with document_id in kwargs
        WHEN: _extract_document_id is called
        THEN: Returns UUID
        """
        from uuid import uuid4

        service = QueueMonitorService()
        doc_id = uuid4()
        task = {"args": [], "kwargs": {"document_id": str(doc_id)}}

        result = service._extract_document_id(task)
        assert result == doc_id

    def test_returns_none_for_invalid_uuid(self):
        """
        GIVEN: Task with invalid UUID in args
        WHEN: _extract_document_id is called
        THEN: Returns None
        """
        service = QueueMonitorService()
        task = {"args": ["not-a-uuid", "kb-id"]}

        result = service._extract_document_id(task)
        assert result is None

    def test_returns_none_for_empty_args(self):
        """
        GIVEN: Task with empty args and kwargs
        WHEN: _extract_document_id is called
        THEN: Returns None
        """
        service = QueueMonitorService()
        task = {"args": [], "kwargs": {}}

        result = service._extract_document_id(task)
        assert result is None


class TestBuildStepInfo:
    """Tests for _build_step_info (Story 7-27 AC-7.27.2)."""

    def test_builds_all_steps(self):
        """
        GIVEN: Document with processing_steps
        WHEN: _build_step_info is called
        THEN: Returns StepInfo for parse, chunk, embed, index
        """
        service = QueueMonitorService()

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "parse": {
                "status": "done",
                "started_at": "2024-01-01T12:00:00+00:00",
                "completed_at": "2024-01-01T12:00:05+00:00",
            },
            "chunk": {
                "status": "done",
                "started_at": "2024-01-01T12:00:05+00:00",
                "completed_at": "2024-01-01T12:00:10+00:00",
            },
            "embed": {
                "status": "in_progress",
                "started_at": "2024-01-01T12:00:10+00:00",
            },
            "index": {"status": "pending"},
        }
        mock_doc.step_errors = {}

        result = service._build_step_info(mock_doc)

        assert len(result) == 4
        assert result[0].step == "parse"
        assert result[0].status.value == "done"
        assert result[1].step == "chunk"
        assert result[1].status.value == "done"
        assert result[2].step == "embed"
        assert result[2].status.value == "in_progress"
        assert result[3].step == "index"
        assert result[3].status.value == "pending"

    def test_includes_error_messages(self):
        """
        GIVEN: Document with step_errors
        WHEN: _build_step_info is called
        THEN: StepInfo includes error_message for failed step (AC-7.27.5)
        """
        service = QueueMonitorService()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "parse": {"status": "error", "started_at": "2024-01-01T12:00:00+00:00"},
        }
        mock_doc.step_errors = {"parse": "PDF parsing failed: corrupted file"}

        result = service._build_step_info(mock_doc)

        assert result[0].step == "parse"
        assert result[0].status.value == "error"
        assert result[0].error_message == "PDF parsing failed: corrupted file"

    def test_handles_empty_processing_steps(self):
        """
        GIVEN: Document with empty processing_steps
        WHEN: _build_step_info is called
        THEN: Returns steps with pending status
        """
        service = QueueMonitorService()

        mock_doc = MagicMock()
        mock_doc.processing_steps = None
        mock_doc.step_errors = None

        result = service._build_step_info(mock_doc)

        assert len(result) == 4
        for step_info in result:
            assert step_info.status.value == "pending"

    def test_calculates_duration(self):
        """
        GIVEN: Document step with started_at and completed_at
        WHEN: _build_step_info is called
        THEN: duration_ms is calculated correctly
        """
        service = QueueMonitorService()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "parse": {
                "status": "done",
                "started_at": "2024-01-01T12:00:00+00:00",
                "completed_at": "2024-01-01T12:00:05+00:00",
            },
        }
        mock_doc.step_errors = {}

        result = service._build_step_info(mock_doc)

        assert result[0].duration_ms == 5000  # 5 seconds = 5000ms


class TestBulkRetryFailed:
    """Tests for bulk_retry_failed (Story 7-27 AC-7.27.6-10)."""

    @pytest.mark.asyncio
    async def test_retry_specific_documents(self):
        """
        GIVEN: Specific document IDs to retry
        WHEN: bulk_retry_failed is called with document_ids
        THEN: Only those documents are queued for retry
        """
        from uuid import uuid4

        # Mock session
        mock_session = AsyncMock()
        doc1_id = uuid4()
        doc2_id = uuid4()
        kb_id = uuid4()

        # Mock failed documents
        mock_doc1 = MagicMock()
        mock_doc1.id = doc1_id
        mock_doc1.kb_id = kb_id
        mock_doc1.retry_count = 0
        mock_doc1.status = MagicMock()
        mock_doc1.status.value = "FAILED"

        mock_doc2 = MagicMock()
        mock_doc2.id = doc2_id
        mock_doc2.kb_id = kb_id
        mock_doc2.retry_count = 1
        mock_doc2.status = MagicMock()
        mock_doc2.status.value = "FAILED"

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc1, mock_doc2]
        mock_session.execute.return_value = mock_result

        with patch("app.workers.document_tasks.process_document") as mock_process:
            mock_process.delay = MagicMock()

            service = QueueMonitorService()
            result = await service.bulk_retry_failed(
                session=mock_session,
                document_ids=[doc1_id, doc2_id],
            )

        assert result.queued == 2
        assert result.failed == 0
        assert len(result.errors) == 0
        assert mock_process.delay.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_all_failed_in_kb(self):
        """
        GIVEN: retry_all_failed=True with kb_id filter
        WHEN: bulk_retry_failed is called
        THEN: All FAILED documents in that KB are retried
        """
        from uuid import uuid4

        mock_session = AsyncMock()
        kb_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = uuid4()
        mock_doc.kb_id = kb_id
        mock_doc.retry_count = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc]
        mock_session.execute.return_value = mock_result

        with patch("app.workers.document_tasks.process_document") as mock_process:
            mock_process.delay = MagicMock()

            service = QueueMonitorService()
            result = await service.bulk_retry_failed(
                session=mock_session,
                retry_all_failed=True,
                kb_id=kb_id,
            )

        assert result.queued == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_documents(self):
        """
        GIVEN: No document_ids and retry_all_failed=False
        WHEN: bulk_retry_failed is called
        THEN: Returns empty response (no action)
        """
        mock_session = AsyncMock()

        service = QueueMonitorService()
        result = await service.bulk_retry_failed(
            session=mock_session,
            document_ids=None,
            retry_all_failed=False,
        )

        assert result.queued == 0
        assert result.failed == 0
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_captures_errors_on_failure(self):
        """
        GIVEN: Document that fails to queue
        WHEN: bulk_retry_failed is called
        THEN: Error is captured in response.errors
        """
        from uuid import uuid4

        mock_session = AsyncMock()
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.kb_id = uuid4()
        mock_doc.retry_count = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc]
        mock_session.execute.return_value = mock_result

        with patch("app.workers.document_tasks.process_document") as mock_process:
            mock_process.delay.side_effect = Exception("Celery broker down")

            service = QueueMonitorService()
            result = await service.bulk_retry_failed(
                session=mock_session,
                document_ids=[doc_id],
            )

        assert result.queued == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert result.errors[0].document_id == doc_id
        assert "Celery broker down" in result.errors[0].error

    @pytest.mark.asyncio
    async def test_resets_document_state(self):
        """
        GIVEN: Failed document
        WHEN: bulk_retry_failed is called
        THEN: Document state is reset (AC-7.27.10)
        """
        from uuid import uuid4

        from app.models.document import DocumentStatus

        mock_session = AsyncMock()
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.kb_id = uuid4()
        mock_doc.retry_count = 2
        mock_doc.last_error = "Previous error"
        mock_doc.processing_steps = {"parse": {"status": "error"}}
        mock_doc.step_errors = {"parse": "error message"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc]
        mock_session.execute.return_value = mock_result

        with patch("app.workers.document_tasks.process_document") as mock_process:
            mock_process.delay = MagicMock()

            service = QueueMonitorService()
            await service.bulk_retry_failed(
                session=mock_session,
                document_ids=[doc_id],
            )

        # Verify state reset
        assert mock_doc.status == DocumentStatus.PENDING
        assert mock_doc.retry_count == 3  # Incremented
        assert mock_doc.last_error is None
        assert mock_doc.processing_steps == {}
        assert mock_doc.step_errors == {}
        assert mock_doc.current_step == "upload"


class TestGetQueueTasksWithDocumentStatus:
    """Tests for get_queue_tasks with document_status filter (AC-7.27.15)."""

    @pytest.mark.asyncio
    async def test_filters_by_document_status(self, mock_celery_inspect):
        """
        GIVEN: Tasks with documents of mixed status
        WHEN: get_queue_tasks with document_status=FAILED
        THEN: Only tasks for FAILED documents are returned
        """
        from uuid import uuid4

        from app.schemas.admin import DocumentStatusFilter

        doc_id_1 = uuid4()
        doc_id_2 = uuid4()

        # Mock active tasks with two documents
        mock_celery_inspect.active.return_value = {
            "worker1@localhost": [
                {
                    "id": "task-1",
                    "name": "process_document",
                    "time_start": 1701523200.0,
                    "args": [str(doc_id_1), "kb-id"],
                    "delivery_info": {"routing_key": "document_processing"},
                },
                {
                    "id": "task-2",
                    "name": "process_document",
                    "time_start": 1701523201.0,
                    "args": [str(doc_id_2), "kb-id"],
                    "delivery_info": {"routing_key": "document_processing"},
                },
            ],
        }

        # Mock session
        mock_session = AsyncMock()

        # Create mock documents with different statuses
        mock_doc_1 = MagicMock()
        mock_doc_1.id = doc_id_1
        mock_doc_1.status = MagicMock()
        mock_doc_1.status.value = "FAILED"
        mock_doc_1.original_filename = "doc1.pdf"
        mock_doc_1.current_step = "parse"
        mock_doc_1.processing_steps = {}
        mock_doc_1.step_errors = {"parse": "Error"}

        mock_doc_2 = MagicMock()
        mock_doc_2.id = doc_id_2
        mock_doc_2.status = MagicMock()
        mock_doc_2.status.value = "PROCESSING"
        mock_doc_2.original_filename = "doc2.pdf"
        mock_doc_2.current_step = "chunk"
        mock_doc_2.processing_steps = {}
        mock_doc_2.step_errors = {}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc_1, mock_doc_2]
        mock_session.execute.return_value = mock_result

        with patch.object(
            QueueMonitorService, "_get_celery_inspect", return_value=mock_celery_inspect
        ):
            service = QueueMonitorService()
            result = await service.get_queue_tasks(
                "document_processing",
                session=mock_session,
                document_status=DocumentStatusFilter.FAILED,
            )

        # Only task-1 (FAILED document) should be returned
        assert len(result) == 1
        assert result[0].document_id == doc_id_1
        assert result[0].document_name == "doc1.pdf"

    @pytest.mark.asyncio
    async def test_returns_all_without_filter(self, mock_celery_inspect):
        """
        GIVEN: Tasks with documents
        WHEN: get_queue_tasks with document_status=ALL
        THEN: All tasks are returned
        """
        from uuid import uuid4

        from app.schemas.admin import DocumentStatusFilter

        doc_id = uuid4()

        mock_celery_inspect.active.return_value = {
            "worker1@localhost": [
                {
                    "id": "task-1",
                    "name": "process_document",
                    "time_start": 1701523200.0,
                    "args": [str(doc_id), "kb-id"],
                    "delivery_info": {"routing_key": "document_processing"},
                },
            ],
        }

        mock_session = AsyncMock()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.status = MagicMock()
        mock_doc.status.value = "PROCESSING"
        mock_doc.original_filename = "doc.pdf"
        mock_doc.current_step = "chunk"
        mock_doc.processing_steps = {}
        mock_doc.step_errors = {}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc]
        mock_session.execute.return_value = mock_result

        with patch.object(
            QueueMonitorService, "_get_celery_inspect", return_value=mock_celery_inspect
        ):
            service = QueueMonitorService()
            result = await service.get_queue_tasks(
                "document_processing",
                session=mock_session,
                document_status=DocumentStatusFilter.ALL,
            )

        assert len(result) == 1
        assert result[0].document_id == doc_id
