# ATDD Checklist - Story 5-23: Document Processing Progress Screen

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-23
**Status:** RED (Failing Tests Written)
**Generated:** 2025-12-06
**Priority:** HIGH

---

## Overview

This checklist tracks the ATDD (Acceptance Test-Driven Development) implementation for Story 5-23, which delivers a Document Processing Progress Screen for KB admins and writers.

**Test Coverage Target:** 61 tests total
- Backend Unit Tests: 20 tests
- Backend Integration Tests: 6 tests
- Frontend Unit Tests: 30 tests
- E2E Tests: 5 tests

---

## Acceptance Criteria Test Matrix

| AC ID | Acceptance Criteria | Backend Unit | Integration | Frontend Unit | E2E |
|-------|---------------------|--------------|-------------|---------------|-----|
| AC-5.23.1 | Processing tab visibility (permission-based) | 2 | 2 | 3 | 1 |
| AC-5.23.2 | Document list with processing columns | 4 | 1 | 6 | 1 |
| AC-5.23.3 | Filtering by name/type/date/status/step | 6 | 1 | 5 | 1 |
| AC-5.23.4 | Per-step details modal | 4 | 1 | 5 | 1 |
| AC-5.23.5 | Pagination with 50 per page | 2 | 1 | 4 | 0 |
| AC-5.23.6 | Auto-refresh every 10 seconds | 2 | 0 | 7 | 1 |

---

## Phase 1: RED - Write Failing Tests

### Backend Unit Tests

**File:** `backend/tests/unit/test_document_processing_service.py`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| UT-5.23.1.1 | `test_admin_permission_can_view_processing` | AC-1 | ⬜ |
| UT-5.23.1.2 | `test_writer_permission_can_view_processing` | AC-1 | ⬜ |
| UT-5.23.2.1 | `test_list_documents_returns_all_processing_columns` | AC-2 | ⬜ |
| UT-5.23.2.2 | `test_list_documents_includes_chunk_count` | AC-2 | ⬜ |
| UT-5.23.2.3 | `test_list_documents_includes_current_step` | AC-2 | ⬜ |
| UT-5.23.2.4 | `test_list_documents_sorted_by_column` | AC-2 | ⬜ |
| UT-5.23.3.1 | `test_filter_by_name_partial_match` | AC-3 | ⬜ |
| UT-5.23.3.2 | `test_filter_by_file_type` | AC-3 | ⬜ |
| UT-5.23.3.3 | `test_filter_by_date_range` | AC-3 | ⬜ |
| UT-5.23.3.4 | `test_filter_by_status` | AC-3 | ⬜ |
| UT-5.23.3.5 | `test_filter_by_current_step` | AC-3 | ⬜ |
| UT-5.23.3.6 | `test_filter_combined_multiple_criteria` | AC-3 | ⬜ |
| UT-5.23.4.1 | `test_get_processing_details_returns_all_steps` | AC-4 | ⬜ |
| UT-5.23.4.2 | `test_get_processing_details_includes_duration` | AC-4 | ⬜ |
| UT-5.23.4.3 | `test_get_processing_details_includes_error_message` | AC-4 | ⬜ |
| UT-5.23.4.4 | `test_get_processing_details_includes_timestamps` | AC-4 | ⬜ |
| UT-5.23.5.1 | `test_pagination_default_50_per_page` | AC-5 | ⬜ |
| UT-5.23.5.2 | `test_pagination_returns_correct_page` | AC-5 | ⬜ |
| UT-5.23.6.1 | `test_update_step_status_in_progress` | AC-6 | ⬜ |
| UT-5.23.6.2 | `test_update_step_status_completed_with_duration` | AC-6 | ⬜ |

```python
# backend/tests/unit/test_document_processing_service.py
"""
Story 5-23 Backend Unit Tests - RED Phase
Document Processing Progress Service Tests
"""
import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.document_service import DocumentService
from app.models.document import Document, DocumentStatus
from app.schemas.document import ProcessingStep, StepStatus


class TestDocumentProcessingPermissions:
    """AC-5.23.1: Permission-based access to processing tab"""

    @pytest.mark.asyncio
    async def test_admin_permission_can_view_processing(self, mock_db_session):
        """[UT-5.23.1.1] Admin users should be able to view processing status"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user_id = uuid4()

        # Mock KB service to return ADMIN permission
        mock_kb_service = AsyncMock()
        mock_kb_service.get_user_permission.return_value = "ADMIN"
        service.kb_service = mock_kb_service

        # Act
        can_view = await service.can_view_processing_status(kb_id, user_id)

        # Assert
        assert can_view is True
        mock_kb_service.get_user_permission.assert_called_once_with(kb_id, user_id)

    @pytest.mark.asyncio
    async def test_writer_permission_can_view_processing(self, mock_db_session):
        """[UT-5.23.1.2] Writer users should be able to view processing status"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user_id = uuid4()

        mock_kb_service = AsyncMock()
        mock_kb_service.get_user_permission.return_value = "WRITE"
        service.kb_service = mock_kb_service

        # Act
        can_view = await service.can_view_processing_status(kb_id, user_id)

        # Assert
        assert can_view is True


class TestDocumentProcessingList:
    """AC-5.23.2: Document list with processing status columns"""

    @pytest.mark.asyncio
    async def test_list_documents_returns_all_processing_columns(self, mock_db_session):
        """[UT-5.23.2.1] Document list returns all required processing columns"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = uuid4()
        mock_doc.original_filename = "test.pdf"
        mock_doc.content_type = "application/pdf"
        mock_doc.status = DocumentStatus.PROCESSING
        mock_doc.current_step = "parse"
        mock_doc.chunk_count = 0
        mock_doc.created_at = datetime.now(UTC)
        mock_doc.processing_steps = {"upload": {"status": "done"}}

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

        # Act
        documents, total = await service.list_with_processing_status(kb_id)

        # Assert
        assert len(documents) == 1
        doc = documents[0]
        assert hasattr(doc, 'original_filename')
        assert hasattr(doc, 'content_type')
        assert hasattr(doc, 'status')
        assert hasattr(doc, 'current_step')
        assert hasattr(doc, 'chunk_count')
        assert hasattr(doc, 'created_at')

    @pytest.mark.asyncio
    async def test_list_documents_includes_chunk_count(self, mock_db_session):
        """[UT-5.23.2.2] Document list includes chunk count for processed documents"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = uuid4()
        mock_doc.status = DocumentStatus.READY
        mock_doc.chunk_count = 42
        mock_doc.current_step = "complete"

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

        # Act
        documents, _ = await service.list_with_processing_status(kb_id)

        # Assert
        assert documents[0].chunk_count == 42

    @pytest.mark.asyncio
    async def test_list_documents_includes_current_step(self, mock_db_session):
        """[UT-5.23.2.3] Document list shows current processing step"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.current_step = "embed"
        mock_doc.status = DocumentStatus.PROCESSING

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

        # Act
        documents, _ = await service.list_with_processing_status(kb_id)

        # Assert
        assert documents[0].current_step == "embed"

    @pytest.mark.asyncio
    async def test_list_documents_sorted_by_column(self, mock_db_session):
        """[UT-5.23.2.4] Document list supports sorting by different columns"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(
            kb_id,
            sort_by="created_at",
            sort_order="desc"
        )

        # Assert - verify ORDER BY was applied
        call_args = mock_db_session.execute.call_args
        # The query should include ORDER BY clause
        assert call_args is not None


class TestDocumentProcessingFilters:
    """AC-5.23.3: Filtering capabilities"""

    @pytest.mark.asyncio
    async def test_filter_by_name_partial_match(self, mock_db_session):
        """[UT-5.23.3.1] Filter by name uses case-insensitive partial match"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id, name="report")

        # Assert - verify ILIKE clause was applied
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_by_file_type(self, mock_db_session):
        """[UT-5.23.3.2] Filter by file type"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id, file_type="pdf")

        # Assert
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, mock_db_session):
        """[UT-5.23.3.3] Filter by upload date range"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        date_from = datetime.now(UTC) - timedelta(days=7)
        date_to = datetime.now(UTC)

        # Act
        await service.list_with_processing_status(
            kb_id,
            date_from=date_from,
            date_to=date_to
        )

        # Assert
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_by_status(self, mock_db_session):
        """[UT-5.23.3.4] Filter by processing status"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id, status=DocumentStatus.FAILED)

        # Assert
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_by_current_step(self, mock_db_session):
        """[UT-5.23.3.5] Filter by current processing step"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id, current_step=ProcessingStep.EMBED)

        # Assert
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_combined_multiple_criteria(self, mock_db_session):
        """[UT-5.23.3.6] Multiple filters can be combined"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(
            kb_id,
            name="report",
            file_type="pdf",
            status=DocumentStatus.PROCESSING,
            current_step=ProcessingStep.CHUNK
        )

        # Assert - all filters should be applied
        call_args = mock_db_session.execute.call_args
        assert call_args is not None


class TestDocumentProcessingDetails:
    """AC-5.23.4: Per-step details"""

    @pytest.mark.asyncio
    async def test_get_processing_details_returns_all_steps(self, mock_db_session):
        """[UT-5.23.4.1] Processing details include all 5 pipeline steps"""
        # Arrange
        service = DocumentService(mock_db_session)
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.processing_steps = {
            "upload": {"status": "done", "duration_ms": 1000},
            "parse": {"status": "done", "duration_ms": 2000},
            "chunk": {"status": "in_progress"},
            "embed": {"status": "pending"},
            "index": {"status": "pending"},
        }
        mock_doc.step_errors = {}

        mock_db_session.get.return_value = mock_doc

        # Act
        details = await service.get_processing_details(doc_id)

        # Assert
        assert len(details.steps) == 5
        step_names = [s.step for s in details.steps]
        assert "upload" in step_names
        assert "parse" in step_names
        assert "chunk" in step_names
        assert "embed" in step_names
        assert "index" in step_names

    @pytest.mark.asyncio
    async def test_get_processing_details_includes_duration(self, mock_db_session):
        """[UT-5.23.4.2] Processing details include step duration in ms"""
        # Arrange
        service = DocumentService(mock_db_session)
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "upload": {"status": "done", "duration_ms": 1500},
        }
        mock_doc.step_errors = {}

        mock_db_session.get.return_value = mock_doc

        # Act
        details = await service.get_processing_details(doc_id)

        # Assert
        upload_step = next(s for s in details.steps if s.step == "upload")
        assert upload_step.duration_ms == 1500

    @pytest.mark.asyncio
    async def test_get_processing_details_includes_error_message(self, mock_db_session):
        """[UT-5.23.4.3] Processing details include error message for failed steps"""
        # Arrange
        service = DocumentService(mock_db_session)
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "parse": {"status": "error"},
        }
        mock_doc.step_errors = {
            "parse": {"error": "Failed to extract text from PDF", "timestamp": "2025-12-06T10:00:00Z"}
        }

        mock_db_session.get.return_value = mock_doc

        # Act
        details = await service.get_processing_details(doc_id)

        # Assert
        parse_step = next(s for s in details.steps if s.step == "parse")
        assert parse_step.error == "Failed to extract text from PDF"

    @pytest.mark.asyncio
    async def test_get_processing_details_includes_timestamps(self, mock_db_session):
        """[UT-5.23.4.4] Processing details include start/complete timestamps"""
        # Arrange
        service = DocumentService(mock_db_session)
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "upload": {
                "status": "done",
                "started_at": "2025-12-06T10:00:00Z",
                "completed_at": "2025-12-06T10:00:02Z",
            },
        }
        mock_doc.step_errors = {}

        mock_db_session.get.return_value = mock_doc

        # Act
        details = await service.get_processing_details(doc_id)

        # Assert
        upload_step = next(s for s in details.steps if s.step == "upload")
        assert upload_step.started_at is not None
        assert upload_step.completed_at is not None


class TestDocumentProcessingPagination:
    """AC-5.23.5: Pagination"""

    @pytest.mark.asyncio
    async def test_pagination_default_50_per_page(self, mock_db_session):
        """[UT-5.23.5.1] Default page size is 50 documents"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id)

        # Assert - verify LIMIT 50 was applied
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_pagination_returns_correct_page(self, mock_db_session):
        """[UT-5.23.5.2] Pagination returns correct page of results"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()

        # Act
        await service.list_with_processing_status(kb_id, page=2, page_size=50)

        # Assert - verify OFFSET 50 was applied for page 2
        call_args = mock_db_session.execute.call_args
        assert call_args is not None


class TestStepStatusUpdates:
    """AC-5.23.6: Real-time updates - step status tracking"""

    @pytest.mark.asyncio
    async def test_update_step_status_in_progress(self, mock_db_session):
        """[UT-5.23.6.1] Update step to in_progress sets started_at timestamp"""
        # Arrange
        from app.workers.document_tasks import update_step_status
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.processing_steps = {}
        mock_doc.step_errors = {}

        mock_db_session.get.return_value = mock_doc

        # Act
        await update_step_status(mock_db_session, doc_id, "parse", "in_progress")

        # Assert
        assert mock_doc.processing_steps["parse"]["status"] == "in_progress"
        assert "started_at" in mock_doc.processing_steps["parse"]
        assert mock_doc.current_step == "parse"

    @pytest.mark.asyncio
    async def test_update_step_status_completed_with_duration(self, mock_db_session):
        """[UT-5.23.6.2] Update step to done calculates duration_ms"""
        # Arrange
        from app.workers.document_tasks import update_step_status
        doc_id = uuid4()

        started = (datetime.now(UTC) - timedelta(seconds=2)).isoformat()
        mock_doc = MagicMock()
        mock_doc.processing_steps = {
            "parse": {"status": "in_progress", "started_at": started}
        }
        mock_doc.step_errors = {}

        mock_db_session.get.return_value = mock_doc

        # Act
        await update_step_status(mock_db_session, doc_id, "parse", "done")

        # Assert
        assert mock_doc.processing_steps["parse"]["status"] == "done"
        assert mock_doc.processing_steps["parse"]["duration_ms"] >= 2000
```

---

### Backend Integration Tests

**File:** `backend/tests/integration/test_document_processing_api.py`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| IT-5.23.1.1 | `test_processing_endpoint_requires_write_permission` | AC-1 | ⬜ |
| IT-5.23.1.2 | `test_processing_endpoint_denies_read_only_user` | AC-1 | ⬜ |
| IT-5.23.2.1 | `test_get_processing_list_returns_all_fields` | AC-2 | ⬜ |
| IT-5.23.3.1 | `test_get_processing_list_with_filters` | AC-3 | ⬜ |
| IT-5.23.4.1 | `test_get_processing_details_endpoint` | AC-4 | ⬜ |
| IT-5.23.5.1 | `test_get_processing_list_pagination` | AC-5 | ⬜ |

```python
# backend/tests/integration/test_document_processing_api.py
"""
Story 5-23 Backend Integration Tests - RED Phase
Document Processing Progress API Tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from tests.factories import KnowledgeBaseFactory, DocumentFactory, UserFactory


@pytest.mark.integration
class TestDocumentProcessingEndpoints:
    """Integration tests for document processing progress endpoints"""

    @pytest.mark.asyncio
    async def test_processing_endpoint_requires_write_permission(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """[IT-5.23.1.1] Processing endpoint accessible with ADMIN/WRITE permission"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            headers=auth_headers_admin
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_processing_endpoint_denies_read_only_user(
        self, async_client: AsyncClient, auth_headers_reader
    ):
        """[IT-5.23.1.2] Processing endpoint returns 403 for READ-only users"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            headers=auth_headers_reader
        )

        # Assert
        assert response.status_code == 403
        assert "Admin or Write permission required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_processing_list_returns_all_fields(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """[IT-5.23.2.1] Processing list returns all required document fields"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        doc = await DocumentFactory.create(
            kb_id=kb.id,
            status="processing",
            current_step="chunk",
            processing_steps={
                "upload": {"status": "done", "duration_ms": 1000},
                "parse": {"status": "done", "duration_ms": 2000},
                "chunk": {"status": "in_progress"},
            }
        )

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            headers=auth_headers_admin
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) >= 1

        doc_data = next(d for d in data["documents"] if d["id"] == str(doc.id))
        assert "original_filename" in doc_data
        assert "file_type" in doc_data
        assert "status" in doc_data
        assert "current_step" in doc_data
        assert "chunk_count" in doc_data
        assert "created_at" in doc_data

    @pytest.mark.asyncio
    async def test_get_processing_list_with_filters(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """[IT-5.23.3.1] Processing list supports filtering by multiple criteria"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        await DocumentFactory.create(kb_id=kb.id, status="failed", current_step="parse")
        await DocumentFactory.create(kb_id=kb.id, status="processing", current_step="embed")
        await DocumentFactory.create(kb_id=kb.id, status="ready", current_step="complete")

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            params={"status": "failed", "current_step": "parse"},
            headers=auth_headers_admin
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for doc in data["documents"]:
            assert doc["status"] == "failed"
            assert doc["current_step"] == "parse"

    @pytest.mark.asyncio
    async def test_get_processing_details_endpoint(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """[IT-5.23.4.1] Processing details endpoint returns step-by-step status"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        doc = await DocumentFactory.create(
            kb_id=kb.id,
            status="processing",
            current_step="chunk",
            processing_steps={
                "upload": {"status": "done", "started_at": "2025-12-06T10:00:00Z", "completed_at": "2025-12-06T10:00:02Z", "duration_ms": 2000},
                "parse": {"status": "done", "started_at": "2025-12-06T10:00:02Z", "completed_at": "2025-12-06T10:00:05Z", "duration_ms": 3000},
                "chunk": {"status": "in_progress", "started_at": "2025-12-06T10:00:05Z"},
                "embed": {"status": "pending"},
                "index": {"status": "pending"},
            }
        )

        # Act
        response = await async_client.get(
            f"/api/v1/documents/{doc.id}/processing-details",
            headers=auth_headers_admin
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(doc.id)
        assert "steps" in data
        assert len(data["steps"]) == 5

        # Verify step details
        upload_step = next(s for s in data["steps"] if s["step"] == "upload")
        assert upload_step["status"] == "done"
        assert upload_step["duration_ms"] == 2000

    @pytest.mark.asyncio
    async def test_get_processing_list_pagination(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """[IT-5.23.5.1] Processing list supports pagination"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        # Create 60 documents
        for i in range(60):
            await DocumentFactory.create(kb_id=kb.id)

        # Act - get page 1
        response1 = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            params={"page": 1, "page_size": 50},
            headers=auth_headers_admin
        )

        # Act - get page 2
        response2 = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents/processing",
            params={"page": 2, "page_size": 50},
            headers=auth_headers_admin
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["total"] == 60
        assert len(data1["documents"]) == 50
        assert data1["page"] == 1

        assert len(data2["documents"]) == 10
        assert data2["page"] == 2
```

---

### Frontend Unit Tests

**File:** `frontend/src/components/processing/__tests__/processing-tab.test.tsx`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| FUT-5.23.1.1 | `shows_processing_tab_for_admin` | AC-1 | ⬜ |
| FUT-5.23.1.2 | `shows_processing_tab_for_writer` | AC-1 | ⬜ |
| FUT-5.23.1.3 | `hides_processing_tab_for_reader` | AC-1 | ⬜ |
| FUT-5.23.2.1 | `renders_document_table_with_all_columns` | AC-2 | ⬜ |
| FUT-5.23.2.2 | `displays_status_badges_with_colors` | AC-2 | ⬜ |
| FUT-5.23.2.3 | `displays_current_step_indicator` | AC-2 | ⬜ |
| FUT-5.23.2.4 | `displays_chunk_count_for_ready_docs` | AC-2 | ⬜ |
| FUT-5.23.2.5 | `supports_column_sorting` | AC-2 | ⬜ |
| FUT-5.23.2.6 | `opens_details_modal_on_row_click` | AC-2 | ⬜ |
| FUT-5.23.3.1 | `renders_filter_bar_with_all_controls` | AC-3 | ⬜ |
| FUT-5.23.3.2 | `filters_by_name_with_debounce` | AC-3 | ⬜ |
| FUT-5.23.3.3 | `filters_by_status_dropdown` | AC-3 | ⬜ |
| FUT-5.23.3.4 | `filters_by_step_dropdown` | AC-3 | ⬜ |
| FUT-5.23.3.5 | `syncs_filters_with_url_params` | AC-3 | ⬜ |
| FUT-5.23.4.1 | `details_modal_shows_step_timeline` | AC-4 | ⬜ |
| FUT-5.23.4.2 | `details_modal_shows_error_message` | AC-4 | ⬜ |
| FUT-5.23.4.3 | `details_modal_shows_duration_metrics` | AC-4 | ⬜ |
| FUT-5.23.4.4 | `details_modal_shows_chunk_count` | AC-4 | ⬜ |
| FUT-5.23.4.5 | `details_modal_closes_on_escape` | AC-4 | ⬜ |
| FUT-5.23.5.1 | `renders_pagination_controls` | AC-5 | ⬜ |
| FUT-5.23.5.2 | `displays_total_document_count` | AC-5 | ⬜ |
| FUT-5.23.5.3 | `navigates_between_pages` | AC-5 | ⬜ |
| FUT-5.23.5.4 | `changes_page_size` | AC-5 | ⬜ |
| FUT-5.23.6.1 | `auto_refreshes_every_10_seconds` | AC-6 | ⬜ |
| FUT-5.23.6.2 | `displays_last_updated_timestamp` | AC-6 | ⬜ |
| FUT-5.23.6.3 | `shows_refresh_now_button` | AC-6 | ⬜ |
| FUT-5.23.6.4 | `manual_refresh_updates_data` | AC-6 | ⬜ |
| FUT-5.23.6.5 | `pauses_auto_refresh_when_modal_open` | AC-6 | ⬜ |
| FUT-5.23.6.6 | `resumes_auto_refresh_when_modal_closed` | AC-6 | ⬜ |
| FUT-5.23.6.7 | `shows_loading_indicator_during_refresh` | AC-6 | ⬜ |

```typescript
// frontend/src/components/processing/__tests__/processing-tab.test.tsx
/**
 * Story 5-23 Frontend Unit Tests - RED Phase
 * Document Processing Progress Tab Tests
 */
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ProcessingTab } from '../processing-tab';
import { DocumentProcessingTable } from '../document-processing-table';
import { ProcessingFilterBar } from '../processing-filter-bar';
import { ProcessingDetailsModal } from '../processing-details-modal';
import {
  createMockProcessingList,
  createMockProcessingDocument,
  createReadyDocument,
  createFailedParsingDocument,
} from '@/e2e/fixtures/processing-progress.factory';

// Mock hooks
vi.mock('@/hooks/useDocumentProcessing', () => ({
  useDocumentProcessing: vi.fn(),
}));

vi.mock('@/hooks/useDocumentProcessingDetails', () => ({
  useDocumentProcessingDetails: vi.fn(),
}));

// Mock router
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/dashboard',
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('ProcessingTab - Permission Visibility', () => {
  it('[FUT-5.23.1.1] shows processing tab for admin users', () => {
    render(
      <ProcessingTab kbId="kb-1" userPermission="ADMIN" />,
      { wrapper }
    );

    expect(screen.getByRole('tab', { name: /processing/i })).toBeInTheDocument();
  });

  it('[FUT-5.23.1.2] shows processing tab for writer users', () => {
    render(
      <ProcessingTab kbId="kb-1" userPermission="WRITE" />,
      { wrapper }
    );

    expect(screen.getByRole('tab', { name: /processing/i })).toBeInTheDocument();
  });

  it('[FUT-5.23.1.3] hides processing tab for reader users', () => {
    render(
      <ProcessingTab kbId="kb-1" userPermission="READ" />,
      { wrapper }
    );

    expect(screen.queryByRole('tab', { name: /processing/i })).not.toBeInTheDocument();
  });
});

describe('DocumentProcessingTable - Columns and Display', () => {
  const mockDocuments = createMockProcessingList(5);

  it('[FUT-5.23.2.1] renders document table with all required columns', () => {
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        onRowClick={vi.fn()}
        onSort={vi.fn()}
      />,
      { wrapper }
    );

    // Verify column headers
    expect(screen.getByText(/document name/i)).toBeInTheDocument();
    expect(screen.getByText(/file type/i)).toBeInTheDocument();
    expect(screen.getByText(/upload date/i)).toBeInTheDocument();
    expect(screen.getByText(/status/i)).toBeInTheDocument();
    expect(screen.getByText(/current step/i)).toBeInTheDocument();
    expect(screen.getByText(/chunk count/i)).toBeInTheDocument();
    expect(screen.getByText(/actions/i)).toBeInTheDocument();
  });

  it('[FUT-5.23.2.2] displays status badges with appropriate colors', () => {
    const documents = [
      createMockProcessingDocument({ status: 'ready' }),
      createMockProcessingDocument({ status: 'processing' }),
      createMockProcessingDocument({ status: 'failed' }),
      createMockProcessingDocument({ status: 'pending' }),
    ];

    render(
      <DocumentProcessingTable
        documents={documents}
        onRowClick={vi.fn()}
        onSort={vi.fn()}
      />,
      { wrapper }
    );

    // Verify status badges have correct styling
    const readyBadge = screen.getByTestId('status-badge-ready');
    const processingBadge = screen.getByTestId('status-badge-processing');
    const failedBadge = screen.getByTestId('status-badge-failed');

    expect(readyBadge).toHaveClass('bg-green');
    expect(processingBadge).toHaveClass('bg-yellow');
    expect(failedBadge).toHaveClass('bg-red');
  });

  it('[FUT-5.23.2.3] displays current step indicator', () => {
    const doc = createMockProcessingDocument({ current_step: 'embed' });

    render(
      <DocumentProcessingTable
        documents={[doc]}
        onRowClick={vi.fn()}
        onSort={vi.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText(/embed/i)).toBeInTheDocument();
  });

  it('[FUT-5.23.2.4] displays chunk count for ready documents', () => {
    const doc = createReadyDocument(42);

    render(
      <DocumentProcessingTable
        documents={[doc]}
        onRowClick={vi.fn()}
        onSort={vi.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('[FUT-5.23.2.5] supports column sorting on header click', async () => {
    const onSort = vi.fn();

    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        onRowClick={vi.fn()}
        onSort={onSort}
      />,
      { wrapper }
    );

    await userEvent.click(screen.getByText(/upload date/i));

    expect(onSort).toHaveBeenCalledWith('created_at', expect.any(String));
  });

  it('[FUT-5.23.2.6] opens details modal on row click', async () => {
    const onRowClick = vi.fn();

    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        onRowClick={onRowClick}
        onSort={vi.fn()}
      />,
      { wrapper }
    );

    const rows = screen.getAllByRole('row');
    await userEvent.click(rows[1]); // First data row

    expect(onRowClick).toHaveBeenCalledWith(expect.any(String));
  });
});

describe('ProcessingFilterBar - Filter Controls', () => {
  const mockOnFiltersChange = vi.fn();

  beforeEach(() => {
    mockOnFiltersChange.mockClear();
  });

  it('[FUT-5.23.3.1] renders filter bar with all controls', () => {
    render(
      <ProcessingFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
      />,
      { wrapper }
    );

    expect(screen.getByPlaceholderText(/search by name/i)).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /type/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /status/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /step/i })).toBeInTheDocument();
    expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
  });

  it('[FUT-5.23.3.2] filters by name with 300ms debounce', async () => {
    vi.useFakeTimers();

    render(
      <ProcessingFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
      />,
      { wrapper }
    );

    const searchInput = screen.getByPlaceholderText(/search by name/i);
    await userEvent.type(searchInput, 'report');

    // Should not call immediately
    expect(mockOnFiltersChange).not.toHaveBeenCalled();

    // Fast-forward 300ms
    vi.advanceTimersByTime(300);

    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'report' })
    );

    vi.useRealTimers();
  });

  it('[FUT-5.23.3.3] filters by status dropdown', async () => {
    render(
      <ProcessingFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
      />,
      { wrapper }
    );

    const statusSelect = screen.getByRole('combobox', { name: /status/i });
    await userEvent.click(statusSelect);
    await userEvent.click(screen.getByRole('option', { name: /failed/i }));

    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'failed' })
    );
  });

  it('[FUT-5.23.3.4] filters by step dropdown', async () => {
    render(
      <ProcessingFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
      />,
      { wrapper }
    );

    const stepSelect = screen.getByRole('combobox', { name: /step/i });
    await userEvent.click(stepSelect);
    await userEvent.click(screen.getByRole('option', { name: /embed/i }));

    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ current_step: 'embed' })
    );
  });

  it('[FUT-5.23.3.5] syncs filters with URL query params', () => {
    const mockSearchParams = new URLSearchParams('?status=failed&current_step=parse');
    vi.mocked(require('next/navigation').useSearchParams).mockReturnValue(mockSearchParams);

    render(
      <ProcessingFilterBar
        filters={{ status: 'failed', current_step: 'parse' }}
        onFiltersChange={mockOnFiltersChange}
      />,
      { wrapper }
    );

    // Verify filters are pre-selected from URL params
    expect(screen.getByRole('combobox', { name: /status/i })).toHaveTextContent(/failed/i);
    expect(screen.getByRole('combobox', { name: /step/i })).toHaveTextContent(/parse/i);
  });
});

describe('ProcessingDetailsModal - Step Timeline', () => {
  const mockDocument = createMockProcessingDocument({
    id: 'doc-1',
    name: 'Test Document.pdf',
    status: 'processing',
    current_step: 'chunk',
    chunk_count: 0,
    steps: [
      { step: 'upload', status: 'completed', duration_ms: 1000, started_at: '2025-12-06T10:00:00Z', completed_at: '2025-12-06T10:00:01Z', error_message: null, metadata: {} },
      { step: 'parse', status: 'completed', duration_ms: 2000, started_at: '2025-12-06T10:00:01Z', completed_at: '2025-12-06T10:00:03Z', error_message: null, metadata: {} },
      { step: 'chunk', status: 'in_progress', duration_ms: null, started_at: '2025-12-06T10:00:03Z', completed_at: null, error_message: null, metadata: {} },
      { step: 'embed', status: 'pending', duration_ms: null, started_at: null, completed_at: null, error_message: null, metadata: {} },
      { step: 'index', status: 'pending', duration_ms: null, started_at: null, completed_at: null, error_message: null, metadata: {} },
    ],
  });

  it('[FUT-5.23.4.1] details modal shows step timeline', () => {
    render(
      <ProcessingDetailsModal
        document={mockDocument}
        isOpen={true}
        onClose={vi.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText(/upload/i)).toBeInTheDocument();
    expect(screen.getByText(/parse/i)).toBeInTheDocument();
    expect(screen.getByText(/chunk/i)).toBeInTheDocument();
    expect(screen.getByText(/embed/i)).toBeInTheDocument();
    expect(screen.getByText(/index/i)).toBeInTheDocument();

    // Verify step statuses
    expect(screen.getAllByTestId('step-status-completed')).toHaveLength(2);
    expect(screen.getByTestId('step-status-in_progress')).toBeInTheDocument();
    expect(screen.getAllByTestId('step-status-pending')).toHaveLength(2);
  });

  it('[FUT-5.23.4.2] details modal shows error message for failed step', () => {
    const failedDoc = createFailedParsingDocument();

    render(
      <ProcessingDetailsModal
        document={failedDoc}
        isOpen={true}
        onClose={vi.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText(/failed to parse pdf/i)).toBeInTheDocument();
    expect(screen.getByTestId('step-status-failed')).toBeInTheDocument();
  });

  it('[FUT-5.23.4.3] details modal shows duration metrics', () => {
    render(
      <ProcessingDetailsModal
        document={mockDocument}
        isOpen={true}
        onClose={vi.fn()}
      />,
      { wrapper }
    );

    // Verify duration display
    expect(screen.getByText(/1\.0s/i)).toBeInTheDocument(); // upload duration
    expect(screen.getByText(/2\.0s/i)).toBeInTheDocument(); // parse duration
  });

  it('[FUT-5.23.4.4] details modal shows chunk count', () => {
    const readyDoc = createReadyDocument(50);

    render(
      <ProcessingDetailsModal
        document={readyDoc}
        isOpen={true}
        onClose={vi.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText(/50 chunks/i)).toBeInTheDocument();
  });

  it('[FUT-5.23.4.5] details modal closes on escape key', async () => {
    const onClose = vi.fn();

    render(
      <ProcessingDetailsModal
        document={mockDocument}
        isOpen={true}
        onClose={onClose}
      />,
      { wrapper }
    );

    await userEvent.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalled();
  });
});

describe('ProcessingTab - Pagination', () => {
  it('[FUT-5.23.5.1] renders pagination controls', () => {
    const mockData = {
      documents: createMockProcessingList(50),
      total: 127,
      page: 1,
      page_size: 50,
      has_more: true,
    };

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: mockData,
      isLoading: false,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    expect(screen.getByTestId('page-size-select')).toBeInTheDocument();
  });

  it('[FUT-5.23.5.2] displays total document count', () => {
    const mockData = {
      documents: createMockProcessingList(50),
      total: 127,
      page: 1,
      page_size: 50,
    };

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: mockData,
      isLoading: false,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    expect(screen.getByText(/127 documents/i)).toBeInTheDocument();
  });

  it('[FUT-5.23.5.3] navigates between pages', async () => {
    const mockRefetch = vi.fn();
    const mockData = {
      documents: createMockProcessingList(50),
      total: 127,
      page: 1,
      page_size: 50,
    };

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: mockData,
      isLoading: false,
      refetch: mockRefetch,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    await userEvent.click(screen.getByRole('button', { name: /next/i }));

    // Verify page change was triggered
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('[FUT-5.23.5.4] changes page size', async () => {
    const mockData = {
      documents: createMockProcessingList(50),
      total: 127,
      page: 1,
      page_size: 50,
    };

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: mockData,
      isLoading: false,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    await userEvent.click(screen.getByTestId('page-size-select'));
    await userEvent.click(screen.getByRole('option', { name: '100' }));

    // Verify page size was updated in URL
    expect(screen.getByTestId('page-size-select')).toHaveTextContent('100');
  });
});

describe('ProcessingTab - Auto-Refresh', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('[FUT-5.23.6.1] auto-refreshes every 10 seconds', async () => {
    const mockRefetch = vi.fn();

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [], total: 0, page: 1, page_size: 50 },
      isLoading: false,
      refetch: mockRefetch,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    // Fast-forward 10 seconds
    vi.advanceTimersByTime(10000);

    expect(mockRefetch).toHaveBeenCalled();
  });

  it('[FUT-5.23.6.2] displays last updated timestamp', () => {
    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [], total: 0, page: 1, page_size: 50, last_updated: new Date().toISOString() },
      isLoading: false,
      dataUpdatedAt: Date.now(),
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    expect(screen.getByText(/last updated/i)).toBeInTheDocument();
  });

  it('[FUT-5.23.6.3] shows refresh now button', () => {
    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [], total: 0, page: 1, page_size: 50 },
      isLoading: false,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    expect(screen.getByRole('button', { name: /refresh now/i })).toBeInTheDocument();
  });

  it('[FUT-5.23.6.4] manual refresh updates data immediately', async () => {
    const mockRefetch = vi.fn();

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [], total: 0, page: 1, page_size: 50 },
      isLoading: false,
      refetch: mockRefetch,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    await userEvent.click(screen.getByRole('button', { name: /refresh now/i }));

    expect(mockRefetch).toHaveBeenCalled();
  });

  it('[FUT-5.23.6.5] pauses auto-refresh when modal is open', () => {
    const mockRefetch = vi.fn();
    const mockDocument = createMockProcessingDocument();

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [mockDocument], total: 1, page: 1, page_size: 50 },
      isLoading: false,
      refetch: mockRefetch,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    // Open modal
    fireEvent.click(screen.getAllByRole('row')[1]);

    // Reset mock and advance timer
    mockRefetch.mockClear();
    vi.advanceTimersByTime(10000);

    // Should NOT have refreshed while modal is open
    expect(mockRefetch).not.toHaveBeenCalled();
  });

  it('[FUT-5.23.6.6] resumes auto-refresh when modal is closed', async () => {
    const mockRefetch = vi.fn();
    const mockDocument = createMockProcessingDocument();

    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: { documents: [mockDocument], total: 1, page: 1, page_size: 50 },
      isLoading: false,
      refetch: mockRefetch,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    // Open and close modal
    fireEvent.click(screen.getAllByRole('row')[1]);
    await userEvent.keyboard('{Escape}');

    mockRefetch.mockClear();
    vi.advanceTimersByTime(10000);

    expect(mockRefetch).toHaveBeenCalled();
  });

  it('[FUT-5.23.6.7] shows loading indicator during refresh', () => {
    vi.mocked(require('@/hooks/useDocumentProcessing').useDocumentProcessing).mockReturnValue({
      data: null,
      isLoading: true,
      isFetching: true,
    });

    render(<ProcessingTab kbId="kb-1" userPermission="ADMIN" />, { wrapper });

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });
});
```

---

### E2E Tests

**File:** `frontend/e2e/tests/processing/document-processing-progress.spec.ts`

| Test ID | Test Name | AC | Priority | Status |
|---------|-----------|----|----|-----|
| E2E-5.23.1 | `admin_navigates_to_processing_tab` | AC-1 | P0 | ⬜ |
| E2E-5.23.2 | `document_list_displays_processing_status` | AC-2 | P0 | ⬜ |
| E2E-5.23.3 | `filters_update_document_list` | AC-3 | P1 | ⬜ |
| E2E-5.23.4 | `details_modal_shows_step_progress` | AC-4 | P1 | ⬜ |
| E2E-5.23.5 | `auto_refresh_updates_status` | AC-6 | P1 | ⬜ |

```typescript
// frontend/e2e/tests/processing/document-processing-progress.spec.ts
/**
 * Story 5-23 E2E Tests - RED Phase
 * Document Processing Progress Screen E2E Tests
 */
import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';
import { AdminPage } from '../../pages/admin.page';
import {
  createMockProcessingListResponse,
  createMockProcessingDocument,
  createReadyDocument,
  createFailedParsingDocument,
  createChunkingDocument,
  PROCESSING_ERRORS,
} from '../../fixtures/processing-progress.factory';

test.describe('Story 5-23: Document Processing Progress Screen', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test('[P0] E2E-5.23.1: Admin navigates to Processing tab', async ({ page }) => {
    // Arrange - Mock processing endpoint
    await page.route('**/api/v1/knowledge-bases/*/documents/processing*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createMockProcessingListResponse(1, 50, 10)),
      });
    });

    // Act
    await dashboardPage.goto();
    await dashboardPage.gotoWithKB('test-kb-id');

    // Assert - Processing tab should be visible for admin
    await expect(page.getByRole('tab', { name: /processing/i })).toBeVisible();

    // Click on Processing tab
    await page.getByRole('tab', { name: /processing/i }).click();

    // Verify processing view loads
    await expect(page.getByTestId('document-processing-table')).toBeVisible();
  });

  test('[P0] E2E-5.23.2: Document list displays processing status columns', async ({ page }) => {
    // Arrange - Create documents in various states
    const mockDocuments = [
      createReadyDocument(42),
      createChunkingDocument(),
      createFailedParsingDocument(),
    ];

    await page.route('**/api/v1/knowledge-bases/*/documents/processing*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: mockDocuments,
          total: 3,
          page: 1,
          page_size: 50,
          has_more: false,
          last_updated: new Date().toISOString(),
        }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');
    await page.getByRole('tab', { name: /processing/i }).click();

    // Assert - All columns visible
    await expect(page.getByText(/document name/i)).toBeVisible();
    await expect(page.getByText(/file type/i)).toBeVisible();
    await expect(page.getByText(/upload date/i)).toBeVisible();
    await expect(page.getByText(/status/i)).toBeVisible();
    await expect(page.getByText(/current step/i)).toBeVisible();
    await expect(page.getByText(/chunk count/i)).toBeVisible();

    // Assert - Document data displayed
    await expect(page.getByText('Fully Processed.pdf')).toBeVisible();
    await expect(page.getByText('Large Report.pdf')).toBeVisible();
    await expect(page.getByText('Corrupted Document.pdf')).toBeVisible();

    // Assert - Status badges
    await expect(page.getByTestId('status-badge-ready')).toBeVisible();
    await expect(page.getByTestId('status-badge-processing')).toBeVisible();
    await expect(page.getByTestId('status-badge-failed')).toBeVisible();

    // Assert - Chunk count for ready document
    await expect(page.getByText('42')).toBeVisible();
  });

  test('[P1] E2E-5.23.3: Filters update document list', async ({ page }) => {
    // Arrange
    let lastRequestUrl = '';

    await page.route('**/api/v1/knowledge-bases/*/documents/processing*', async (route, request) => {
      lastRequestUrl = request.url();
      const url = new URL(request.url());
      const status = url.searchParams.get('status');

      let documents = createMockProcessingListResponse(1, 50, 20).documents;

      // Apply server-side filter simulation
      if (status) {
        documents = documents.filter((d) => d.status === status);
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents,
          total: documents.length,
          page: 1,
          page_size: 50,
          has_more: false,
        }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');
    await page.getByRole('tab', { name: /processing/i }).click();

    // Apply status filter
    await page.getByRole('combobox', { name: /status/i }).click();
    await page.getByRole('option', { name: /failed/i }).click();

    // Assert - URL updated with filter
    await expect(page).toHaveURL(/status=failed/);

    // Assert - API called with filter
    expect(lastRequestUrl).toContain('status=failed');

    // Assert - Results filtered
    const rows = page.locator('[data-testid="document-row"]');
    await expect(rows).toHaveCount(await rows.count());
  });

  test('[P1] E2E-5.23.4: Details modal shows step progress', async ({ page }) => {
    // Arrange
    const chunkingDoc = createChunkingDocument();

    await page.route('**/api/v1/knowledge-bases/*/documents/processing*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [chunkingDoc],
          total: 1,
          page: 1,
          page_size: 50,
        }),
      });
    });

    await page.route(`**/api/v1/documents/${chunkingDoc.id}/processing-details`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...chunkingDoc,
          total_duration_ms: 5000,
        }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');
    await page.getByRole('tab', { name: /processing/i }).click();

    // Click on document row to open details
    await page.getByText('Large Report.pdf').click();

    // Assert - Modal opens with step timeline
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/processing details/i)).toBeVisible();

    // Assert - All steps visible in timeline
    await expect(page.getByText(/upload/i)).toBeVisible();
    await expect(page.getByText(/parse/i)).toBeVisible();
    await expect(page.getByText(/chunk/i)).toBeVisible();
    await expect(page.getByText(/embed/i)).toBeVisible();
    await expect(page.getByText(/index/i)).toBeVisible();

    // Assert - Current step highlighted
    await expect(page.getByTestId('step-chunk')).toHaveClass(/current/);
  });

  test('[P1] E2E-5.23.5: Auto-refresh updates document status', async ({ page }) => {
    // Arrange - Track refresh calls
    let refreshCount = 0;

    await page.route('**/api/v1/knowledge-bases/*/documents/processing*', async (route) => {
      refreshCount++;

      // First call: document is processing
      // Second call: document is ready
      const doc = refreshCount === 1
        ? createChunkingDocument()
        : createReadyDocument(50);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [doc],
          total: 1,
          page: 1,
          page_size: 50,
          last_updated: new Date().toISOString(),
        }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');
    await page.getByRole('tab', { name: /processing/i }).click();

    // Assert - Initial state shows processing
    await expect(page.getByTestId('status-badge-processing')).toBeVisible();

    // Wait for auto-refresh (10 seconds)
    await page.waitForTimeout(10500);

    // Assert - Status updated to ready after refresh
    await expect(page.getByTestId('status-badge-ready')).toBeVisible();
    expect(refreshCount).toBeGreaterThanOrEqual(2);

    // Assert - Last updated timestamp visible
    await expect(page.getByText(/last updated/i)).toBeVisible();
  });

  test('[P2] Reader user cannot see Processing tab', async ({ page }) => {
    // Arrange - Setup as reader user
    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'reader-user-id',
          email: 'reader@example.com',
          role: 'user',
        }),
      });
    });

    await page.route('**/api/v1/knowledge-bases/*/permission', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ permission: 'READ' }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');

    // Assert - Processing tab not visible for reader
    await expect(page.getByRole('tab', { name: /processing/i })).not.toBeVisible();
  });
});
```

---

## Phase 2: Implementation Checklist

### Backend Implementation

- [ ] **Migration:** Create Alembic migration for processing columns
- [ ] **Models:** Add processing_steps, current_step, step_errors to Document model
- [ ] **Schemas:** Create ProcessingStep, StepStatus enums and response schemas
- [ ] **Service:** Implement list_with_processing_status() method
- [ ] **Service:** Implement get_processing_details() method
- [ ] **Service:** Implement can_view_processing_status() permission check
- [ ] **API:** Add GET /knowledge-bases/{kb_id}/documents/processing endpoint
- [ ] **API:** Add GET /documents/{doc_id}/processing-details endpoint
- [ ] **Workers:** Update document_tasks.py with update_step_status() helper

### Frontend Implementation

- [ ] **Types:** Create processing.ts with TypeScript interfaces
- [ ] **Hooks:** Implement useDocumentProcessing with auto-refresh
- [ ] **Hooks:** Implement useDocumentProcessingDetails
- [ ] **Components:** Create ProcessingTab component
- [ ] **Components:** Create DocumentProcessingTable component
- [ ] **Components:** Create ProcessingFilterBar component
- [ ] **Components:** Create ProcessingDetailsModal component
- [ ] **Integration:** Add Processing tab to KB dashboard
- [ ] **Styling:** Add status badge colors and step timeline styling

---

## Phase 3: GREEN - Make Tests Pass

Track test execution status here as implementation proceeds.

| Category | Total | Passing | Failing | Skipped |
|----------|-------|---------|---------|---------|
| Backend Unit | 20 | 0 | 20 | 0 |
| Backend Integration | 6 | 0 | 6 | 0 |
| Frontend Unit | 30 | 0 | 30 | 0 |
| E2E | 5 | 0 | 5 | 0 |
| **Total** | **61** | **0** | **61** | **0** |

---

## Phase 4: REFACTOR

After all tests pass, review and refactor:

- [ ] Remove code duplication in filter logic
- [ ] Extract common step timeline component for reuse
- [ ] Optimize database queries with proper indexes
- [ ] Add query caching where appropriate
- [ ] Review and clean up test fixtures

---

## Traceability Matrix

| Requirement | Backend Unit | Integration | Frontend Unit | E2E |
|-------------|--------------|-------------|---------------|-----|
| AC-5.23.1: Permission-based visibility | UT-5.23.1.1-2 | IT-5.23.1.1-2 | FUT-5.23.1.1-3 | E2E-5.23.1 |
| AC-5.23.2: Document list columns | UT-5.23.2.1-4 | IT-5.23.2.1 | FUT-5.23.2.1-6 | E2E-5.23.2 |
| AC-5.23.3: Filtering | UT-5.23.3.1-6 | IT-5.23.3.1 | FUT-5.23.3.1-5 | E2E-5.23.3 |
| AC-5.23.4: Step details modal | UT-5.23.4.1-4 | IT-5.23.4.1 | FUT-5.23.4.1-5 | E2E-5.23.4 |
| AC-5.23.5: Pagination | UT-5.23.5.1-2 | IT-5.23.5.1 | FUT-5.23.5.1-4 | - |
| AC-5.23.6: Auto-refresh | UT-5.23.6.1-2 | - | FUT-5.23.6.1-7 | E2E-5.23.5 |

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-06 | TEA | Initial ATDD checklist creation - RED phase |
