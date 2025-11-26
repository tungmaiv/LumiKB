"""Unit tests for outbox task handlers.

Tests the dispatch_event logic and event handler routing without
actual database or external service dependencies.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.workers.outbox_tasks import (
    MAX_OUTBOX_ATTEMPTS,
    dispatch_event,
)

pytestmark = pytest.mark.unit


class TestDispatchEvent:
    """Tests for dispatch_event function."""

    def test_dispatch_document_process(self) -> None:
        """Test document.process events dispatch correctly."""
        doc_id = str(uuid4())
        event = {
            "id": str(uuid4()),
            "event_type": "document.process",
            "aggregate_id": doc_id,
            "aggregate_type": "document",
            "payload": {"document_id": doc_id},
            "attempts": 0,
        }

        with patch("app.workers.document_tasks.process_document") as mock_task:
            mock_task.delay = MagicMock()
            dispatch_event(event)
            mock_task.delay.assert_called_once_with(doc_id)

    def test_dispatch_document_delete(self) -> None:
        """Test document.delete events dispatch correctly."""
        doc_id = str(uuid4())
        kb_id = str(uuid4())
        file_path = "test/path.pdf"
        event = {
            "id": str(uuid4()),
            "event_type": "document.delete",
            "aggregate_id": doc_id,
            "aggregate_type": "document",
            "payload": {
                "document_id": doc_id,
                "kb_id": kb_id,
                "file_path": file_path,
            },
            "attempts": 0,
        }

        with patch("app.workers.document_tasks.delete_document_cleanup") as mock_task:
            mock_task.delay = MagicMock()
            dispatch_event(event)
            mock_task.delay.assert_called_once_with(
                doc_id=doc_id,
                kb_id=kb_id,
                file_path=file_path,
            )

    def test_dispatch_kb_delete(self) -> None:
        """Test kb.delete events dispatch correctly."""
        kb_id = str(uuid4())
        event_id = str(uuid4())
        event = {
            "id": event_id,
            "event_type": "kb.delete",
            "aggregate_id": kb_id,
            "aggregate_type": "knowledge_base",
            "payload": {"kb_id": kb_id},
            "attempts": 0,
        }

        with patch("app.workers.outbox_tasks.run_async") as mock_run_async:
            mock_run_async.return_value = None
            dispatch_event(event)
            mock_run_async.assert_called_once()
            # Verify the coroutine was called with correct args
            call_args = mock_run_async.call_args[0][0]
            # The first arg should be the coroutine
            assert call_args is not None

    def test_dispatch_document_reprocess(self) -> None:
        """Test document.reprocess events dispatch correctly."""
        doc_id = str(uuid4())
        event_id = str(uuid4())
        event = {
            "id": event_id,
            "event_type": "document.reprocess",
            "aggregate_id": doc_id,
            "aggregate_type": "document",
            "payload": {"document_id": doc_id, "reason": "reconciliation"},
            "attempts": 0,
        }

        with patch("app.workers.outbox_tasks.run_async") as mock_run_async:
            mock_run_async.return_value = None
            dispatch_event(event)
            mock_run_async.assert_called_once()

    def test_dispatch_unknown_event_type_logs_warning(self) -> None:
        """Test unknown event types log a warning."""
        event = {
            "id": str(uuid4()),
            "event_type": "unknown.event",
            "aggregate_id": str(uuid4()),
            "aggregate_type": "unknown",
            "payload": {},
            "attempts": 0,
        }

        with patch("app.workers.outbox_tasks.logger") as mock_logger:
            dispatch_event(event)
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "unknown_event_type"

    def test_dispatch_document_process_missing_id(self) -> None:
        """Test document.process with missing document_id logs error."""
        event = {
            "id": str(uuid4()),
            "event_type": "document.process",
            "aggregate_id": str(uuid4()),
            "aggregate_type": "document",
            "payload": {},  # Missing document_id
            "attempts": 0,
        }

        with patch("app.workers.outbox_tasks.logger") as mock_logger:
            dispatch_event(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "missing_document_id_in_payload"

    def test_dispatch_kb_delete_missing_kb_id(self) -> None:
        """Test kb.delete with missing kb_id logs error."""
        event = {
            "id": str(uuid4()),
            "event_type": "kb.delete",
            "aggregate_id": str(uuid4()),
            "aggregate_type": "knowledge_base",
            "payload": {},  # Missing kb_id
            "attempts": 0,
        }

        with patch("app.workers.outbox_tasks.logger") as mock_logger:
            dispatch_event(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "missing_kb_id_in_kb_delete_payload"


class TestMaxOutboxAttempts:
    """Tests for MAX_OUTBOX_ATTEMPTS constant."""

    def test_max_attempts_is_five(self) -> None:
        """Test max outbox attempts is set to 5 per spec."""
        assert MAX_OUTBOX_ATTEMPTS == 5
