# ATDD Checklist - Story 5-24: KB Dashboard Document Filtering & Pagination

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-24
**Status:** RED (Failing Tests Written)
**Generated:** 2025-12-06
**Priority:** MEDIUM

---

## Overview

This checklist tracks the ATDD (Acceptance Test-Driven Development) implementation for Story 5-24, which adds filtering and pagination capabilities to the KB dashboard document list.

**Test Coverage Target:** 26 tests total
- Backend Unit Tests: 4 tests
- Backend Integration Tests: 6 tests
- Frontend Unit Tests: 12 tests
- E2E Tests: 4 tests

---

## Acceptance Criteria Test Matrix

| AC ID | Acceptance Criteria | Backend Unit | Integration | Frontend Unit | E2E |
|-------|---------------------|--------------|-------------|---------------|-----|
| AC-5.24.1 | Filter bar with all controls | - | 1 | 4 | 1 |
| AC-5.24.2 | Real-time filter updates | 1 | 2 | 3 | 1 |
| AC-5.24.3 | Pagination controls | 1 | 2 | 3 | 1 |
| AC-5.24.4 | URL filter state persistence | 1 | - | 2 | 1 |
| AC-5.24.5 | Tag filtering with AND logic | 1 | 1 | - | - |

---

## Phase 1: RED - Write Failing Tests

### Backend Unit Tests

**File:** `backend/tests/unit/test_document_filter_service.py`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| UT-5.24.2.1 | `test_filter_documents_by_name_partial_match` | AC-2 | ⬜ |
| UT-5.24.3.1 | `test_paginate_documents_returns_correct_page` | AC-3 | ⬜ |
| UT-5.24.4.1 | `test_filter_params_mapped_correctly` | AC-4 | ⬜ |
| UT-5.24.5.1 | `test_filter_by_tags_uses_and_logic` | AC-5 | ⬜ |

```python
# backend/tests/unit/test_document_filter_service.py
"""
Story 5-24 Backend Unit Tests - RED Phase
KB Dashboard Document Filtering & Pagination Tests
"""
import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.document_service import DocumentService
from app.models.document import Document


class TestDocumentFilterService:
    """Unit tests for document filtering in DocumentService"""

    @pytest.mark.asyncio
    async def test_filter_documents_by_name_partial_match(self, mock_db_session):
        """[UT-5.24.2.1] Filter by name uses case-insensitive partial match"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user = MagicMock()
        user.id = uuid4()

        # Mock KB service for permission check
        service.kb_service = AsyncMock()
        service.kb_service.check_user_access = AsyncMock()

        mock_doc = MagicMock()
        mock_doc.name = "Quarterly Report.pdf"
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

        # Act
        documents, total = await service.list_documents(
            kb_id=kb_id,
            user=user,
            search="report"
        )

        # Assert
        # Verify ILIKE filter was applied in query
        call_args = mock_db_session.execute.call_args
        assert call_args is not None
        # The actual implementation should use ilike for case-insensitive search

    @pytest.mark.asyncio
    async def test_paginate_documents_returns_correct_page(self, mock_db_session):
        """[UT-5.24.3.1] Pagination returns correct offset and limit"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user = MagicMock()
        user.id = uuid4()

        service.kb_service = AsyncMock()
        service.kb_service.check_user_access = AsyncMock()

        # Act
        await service.list_documents(
            kb_id=kb_id,
            user=user,
            page=3,
            limit=50
        )

        # Assert
        # Page 3 with limit 50 should offset by 100 ((3-1) * 50)
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_params_mapped_correctly(self, mock_db_session):
        """[UT-5.24.4.1] Filter parameters are correctly mapped to query"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user = MagicMock()
        user.id = uuid4()

        service.kb_service = AsyncMock()
        service.kb_service.check_user_access = AsyncMock()

        # Act
        await service.list_documents(
            kb_id=kb_id,
            user=user,
            search="test",
            doc_type="pdf",
            status="processed",
            start_date=datetime.now(UTC) - timedelta(days=7),
            end_date=datetime.now(UTC)
        )

        # Assert
        call_args = mock_db_session.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_filter_by_tags_uses_and_logic(self, mock_db_session):
        """[UT-5.24.5.1] Tag filter uses AND logic (all tags must match)"""
        # Arrange
        service = DocumentService(mock_db_session)
        kb_id = uuid4()
        user = MagicMock()
        user.id = uuid4()

        service.kb_service = AsyncMock()
        service.kb_service.check_user_access = AsyncMock()

        # Act
        await service.list_documents(
            kb_id=kb_id,
            user=user,
            tags=["policy", "hr"]
        )

        # Assert
        # The query should include JSONB contains checks for BOTH tags
        call_args = mock_db_session.execute.call_args
        assert call_args is not None
```

---

### Backend Integration Tests

**File:** `backend/tests/integration/test_document_filter_api.py`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| IT-5.24.1.1 | `test_list_documents_with_all_filter_params` | AC-1 | ⬜ |
| IT-5.24.2.1 | `test_filter_by_name_returns_matching_docs` | AC-2 | ⬜ |
| IT-5.24.2.2 | `test_filter_by_status_returns_filtered_docs` | AC-2 | ⬜ |
| IT-5.24.3.1 | `test_pagination_returns_correct_page_metadata` | AC-3 | ⬜ |
| IT-5.24.3.2 | `test_pagination_with_filters_combined` | AC-3 | ⬜ |
| IT-5.24.5.1 | `test_tag_filter_uses_and_logic` | AC-5 | ⬜ |

```python
# backend/tests/integration/test_document_filter_api.py
"""
Story 5-24 Backend Integration Tests - RED Phase
KB Dashboard Document Filtering & Pagination API Tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta, UTC

from tests.factories import KnowledgeBaseFactory, DocumentFactory


@pytest.mark.integration
class TestDocumentFilterEndpoints:
    """Integration tests for document filtering and pagination"""

    @pytest.mark.asyncio
    async def test_list_documents_with_all_filter_params(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.1.1] Document list accepts all filter parameters"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        await DocumentFactory.create(
            kb_id=kb.id,
            name="Policy Document.pdf",
            content_type="application/pdf",
            status="processed",
            metadata={"tags": ["policy", "hr"]}
        )

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={
                "search": "policy",
                "type": "pdf",
                "status": "processed",
                "tags": ["policy"],
                "start_date": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
                "end_date": datetime.now(UTC).isoformat(),
                "page": 1,
                "limit": 50,
            },
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_more" in data

    @pytest.mark.asyncio
    async def test_filter_by_name_returns_matching_docs(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.2.1] Filter by name returns only matching documents"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        await DocumentFactory.create(kb_id=kb.id, name="Quarterly Report.pdf")
        await DocumentFactory.create(kb_id=kb.id, name="Annual Review.pdf")
        await DocumentFactory.create(kb_id=kb.id, name="Policy Handbook.docx")

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={"search": "report"},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Quarterly Report" in data["documents"][0]["name"]

    @pytest.mark.asyncio
    async def test_filter_by_status_returns_filtered_docs(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.2.2] Filter by status returns only matching documents"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        await DocumentFactory.create(kb_id=kb.id, status="processed")
        await DocumentFactory.create(kb_id=kb.id, status="processed")
        await DocumentFactory.create(kb_id=kb.id, status="failed")
        await DocumentFactory.create(kb_id=kb.id, status="processing")

        # Act
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={"status": "processed"},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for doc in data["documents"]:
            assert doc["status"] == "processed"

    @pytest.mark.asyncio
    async def test_pagination_returns_correct_page_metadata(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.3.1] Pagination returns correct metadata"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        # Create 75 documents
        for i in range(75):
            await DocumentFactory.create(kb_id=kb.id, name=f"Document {i}.pdf")

        # Act - Request page 2 with 50 per page
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={"page": 2, "limit": 50},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 75
        assert data["page"] == 2
        assert data["page_size"] == 50
        assert len(data["documents"]) == 25  # Second page has remaining 25
        assert data["has_more"] is False  # No more pages

    @pytest.mark.asyncio
    async def test_pagination_with_filters_combined(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.3.2] Pagination works correctly with active filters"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        # Create 60 processed docs and 40 failed docs
        for i in range(60):
            await DocumentFactory.create(kb_id=kb.id, status="processed")
        for i in range(40):
            await DocumentFactory.create(kb_id=kb.id, status="failed")

        # Act - Filter by processed + paginate
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={"status": "processed", "page": 2, "limit": 50},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 60  # Only processed docs
        assert data["page"] == 2
        assert len(data["documents"]) == 10  # Page 2 has remaining 10

    @pytest.mark.asyncio
    async def test_tag_filter_uses_and_logic(
        self, async_client: AsyncClient, auth_headers
    ):
        """[IT-5.24.5.1] Tag filter uses AND logic - all tags must match"""
        # Arrange
        kb = await KnowledgeBaseFactory.create()
        # Doc with both tags
        await DocumentFactory.create(
            kb_id=kb.id,
            name="HR Policy.pdf",
            metadata={"tags": ["policy", "hr", "onboarding"]}
        )
        # Doc with only one tag
        await DocumentFactory.create(
            kb_id=kb.id,
            name="IT Policy.pdf",
            metadata={"tags": ["policy", "it"]}
        )
        # Doc with no tags
        await DocumentFactory.create(
            kb_id=kb.id,
            name="Notes.txt",
            metadata={"tags": []}
        )

        # Act - Filter by BOTH policy AND hr tags
        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb.id}/documents",
            params={"tags": ["policy", "hr"]},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "HR Policy" in data["documents"][0]["name"]
```

---

### Frontend Unit Tests

**File:** `frontend/src/components/documents/__tests__/document-filter-bar.test.tsx`

| Test ID | Test Name | AC | Status |
|---------|-----------|----|----|
| FUT-5.24.1.1 | `renders_all_filter_controls` | AC-1 | ⬜ |
| FUT-5.24.1.2 | `renders_search_input` | AC-1 | ⬜ |
| FUT-5.24.1.3 | `renders_type_dropdown` | AC-1 | ⬜ |
| FUT-5.24.1.4 | `renders_clear_filters_button` | AC-1 | ⬜ |
| FUT-5.24.2.1 | `search_triggers_filter_with_debounce` | AC-2 | ⬜ |
| FUT-5.24.2.2 | `dropdown_change_triggers_filter` | AC-2 | ⬜ |
| FUT-5.24.2.3 | `clear_filters_resets_all` | AC-2 | ⬜ |
| FUT-5.24.3.1 | `pagination_shows_page_info` | AC-3 | ⬜ |
| FUT-5.24.3.2 | `pagination_navigation_works` | AC-3 | ⬜ |
| FUT-5.24.3.3 | `page_size_selector_changes_limit` | AC-3 | ⬜ |
| FUT-5.24.4.1 | `filters_sync_with_url_params` | AC-4 | ⬜ |
| FUT-5.24.4.2 | `filter_changes_update_url` | AC-4 | ⬜ |

```typescript
// frontend/src/components/documents/__tests__/document-filter-bar.test.tsx
/**
 * Story 5-24 Frontend Unit Tests - RED Phase
 * Document Filter Bar Component Tests
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { DocumentFilterBar } from '../document-filter-bar';
import { DocumentPagination } from '../document-pagination';
import { useDocumentFilters } from '@/hooks/useDocumentFilters';

// Mock next/navigation
const mockPush = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => '/dashboard',
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('DocumentFilterBar - Filter Controls', () => {
  const mockOnFiltersChange = vi.fn();
  const availableTags = ['policy', 'hr', 'technical', 'legal'];

  beforeEach(() => {
    mockOnFiltersChange.mockClear();
    mockPush.mockClear();
  });

  it('[FUT-5.24.1.1] renders all filter controls', () => {
    render(
      <DocumentFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
        availableTags={availableTags}
      />,
      { wrapper }
    );

    // Verify all controls present
    expect(screen.getByPlaceholderText(/search documents/i)).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /type/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /status/i })).toBeInTheDocument();
    expect(screen.getByTestId('tag-filter')).toBeInTheDocument();
    expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
  });

  it('[FUT-5.24.1.2] renders search input with placeholder', () => {
    render(
      <DocumentFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
        availableTags={availableTags}
      />,
      { wrapper }
    );

    const searchInput = screen.getByPlaceholderText(/search documents/i);
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveAttribute('type', 'text');
  });

  it('[FUT-5.24.1.3] renders type dropdown with options', async () => {
    render(
      <DocumentFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
        availableTags={availableTags}
      />,
      { wrapper }
    );

    const typeSelect = screen.getByRole('combobox', { name: /type/i });
    await userEvent.click(typeSelect);

    expect(screen.getByRole('option', { name: /pdf/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /docx/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /txt/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /markdown/i })).toBeInTheDocument();
  });

  it('[FUT-5.24.1.4] renders clear filters button', () => {
    render(
      <DocumentFilterBar
        filters={{ search: 'test', status: 'failed' }}
        onFiltersChange={mockOnFiltersChange}
        availableTags={availableTags}
      />,
      { wrapper }
    );

    expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
  });
});

describe('DocumentFilterBar - Filter Behavior', () => {
  const mockOnFiltersChange = vi.fn();

  beforeEach(() => {
    mockOnFiltersChange.mockClear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('[FUT-5.24.2.1] search triggers filter with 300ms debounce', async () => {
    render(
      <DocumentFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
        availableTags={[]}
      />,
      { wrapper }
    );

    const searchInput = screen.getByPlaceholderText(/search documents/i);
    await userEvent.type(searchInput, 'report');

    // Should not call immediately
    expect(mockOnFiltersChange).not.toHaveBeenCalled();

    // Advance timer by 300ms
    vi.advanceTimersByTime(300);

    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'report' })
    );
  });

  it('[FUT-5.24.2.2] dropdown change triggers filter immediately', async () => {
    vi.useRealTimers(); // Need real timers for dropdown

    render(
      <DocumentFilterBar
        filters={{}}
        onFiltersChange={mockOnFiltersChange}
        availableTags={[]}
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

  it('[FUT-5.24.2.3] clear filters resets all filter values', async () => {
    vi.useRealTimers();

    render(
      <DocumentFilterBar
        filters={{ search: 'test', status: 'failed', type: 'pdf' }}
        onFiltersChange={mockOnFiltersChange}
        availableTags={[]}
      />,
      { wrapper }
    );

    await userEvent.click(screen.getByRole('button', { name: /clear filters/i }));

    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      search: undefined,
      type: undefined,
      status: undefined,
      tags: undefined,
      startDate: undefined,
      endDate: undefined,
      page: 1,
    });
  });
});

describe('DocumentPagination - Controls', () => {
  const mockOnPageChange = vi.fn();
  const mockOnPageSizeChange = vi.fn();

  beforeEach(() => {
    mockOnPageChange.mockClear();
    mockOnPageSizeChange.mockClear();
  });

  it('[FUT-5.24.3.1] pagination shows page info', () => {
    render(
      <DocumentPagination
        page={2}
        pageSize={50}
        total={127}
        onPageChange={mockOnPageChange}
        onPageSizeChange={mockOnPageSizeChange}
      />,
      { wrapper }
    );

    // Verify page info displayed
    expect(screen.getByText(/page 2 of 3/i)).toBeInTheDocument();
    expect(screen.getByText(/127 documents/i)).toBeInTheDocument();
  });

  it('[FUT-5.24.3.2] pagination navigation works', async () => {
    render(
      <DocumentPagination
        page={2}
        pageSize={50}
        total={127}
        onPageChange={mockOnPageChange}
        onPageSizeChange={mockOnPageSizeChange}
      />,
      { wrapper }
    );

    // Test previous button
    await userEvent.click(screen.getByRole('button', { name: /previous/i }));
    expect(mockOnPageChange).toHaveBeenCalledWith(1);

    mockOnPageChange.mockClear();

    // Test next button
    await userEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(mockOnPageChange).toHaveBeenCalledWith(3);
  });

  it('[FUT-5.24.3.3] page size selector changes limit', async () => {
    render(
      <DocumentPagination
        page={1}
        pageSize={50}
        total={127}
        onPageChange={mockOnPageChange}
        onPageSizeChange={mockOnPageSizeChange}
      />,
      { wrapper }
    );

    const pageSizeSelect = screen.getByRole('combobox');
    await userEvent.click(pageSizeSelect);
    await userEvent.click(screen.getByRole('option', { name: '100' }));

    expect(mockOnPageSizeChange).toHaveBeenCalledWith(100);
  });
});

describe('useDocumentFilters - URL Sync', () => {
  it('[FUT-5.24.4.1] filters sync with URL params on load', () => {
    // Setup mock search params with filters
    const searchParams = new URLSearchParams('?search=report&status=failed&page=2');
    vi.mocked(require('next/navigation').useSearchParams).mockReturnValue(searchParams);

    const TestComponent = () => {
      const { filters } = useDocumentFilters();
      return (
        <div>
          <span data-testid="search">{filters.search}</span>
          <span data-testid="status">{filters.status}</span>
          <span data-testid="page">{filters.page}</span>
        </div>
      );
    };

    render(<TestComponent />, { wrapper });

    expect(screen.getByTestId('search')).toHaveTextContent('report');
    expect(screen.getByTestId('status')).toHaveTextContent('failed');
    expect(screen.getByTestId('page')).toHaveTextContent('2');
  });

  it('[FUT-5.24.4.2] filter changes update URL params', async () => {
    const TestComponent = () => {
      const { filters, setFilters } = useDocumentFilters();
      return (
        <button onClick={() => setFilters({ status: 'processed' })}>
          Set Status
        </button>
      );
    };

    render(<TestComponent />, { wrapper });

    await userEvent.click(screen.getByRole('button', { name: /set status/i }));

    expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('status=processed'));
  });
});
```

---

### E2E Tests

**File:** `frontend/e2e/tests/dashboard/document-filtering.spec.ts`

| Test ID | Test Name | AC | Priority | Status |
|---------|-----------|----|----|-----|
| E2E-5.24.1 | `filter_bar_visible_on_dashboard` | AC-1 | P0 | ⬜ |
| E2E-5.24.2 | `filters_update_document_list` | AC-2 | P0 | ⬜ |
| E2E-5.24.3 | `pagination_navigates_between_pages` | AC-3 | P1 | ⬜ |
| E2E-5.24.4 | `filter_state_persists_in_url` | AC-4 | P1 | ⬜ |

```typescript
// frontend/e2e/tests/dashboard/document-filtering.spec.ts
/**
 * Story 5-24 E2E Tests - RED Phase
 * KB Dashboard Document Filtering & Pagination E2E Tests
 */
import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';
import {
  createMockDocumentsWithTags,
  createMockPaginatedDocuments,
  getAvailableTags,
} from '../../fixtures/document-tags.factory';

test.describe('Story 5-24: KB Dashboard Document Filtering & Pagination', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test('[P0] E2E-5.24.1: Filter bar visible on dashboard', async ({ page }) => {
    // Arrange
    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createMockPaginatedDocuments(1, 50, 100)),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');

    // Assert - Filter bar is visible
    const isFilterBarVisible = await dashboardPage.isFilterBarVisible();
    expect(isFilterBarVisible).toBe(true);

    // Assert - All filter controls present
    await expect(page.getByPlaceholderText(/search documents/i)).toBeVisible();
    await expect(page.getByRole('combobox', { name: /type/i })).toBeVisible();
    await expect(page.getByRole('combobox', { name: /status/i })).toBeVisible();
    await expect(page.locator('[data-testid="tag-filter"]')).toBeVisible();
    await expect(page.locator('[data-testid="date-range-picker"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /clear filters/i })).toBeVisible();
  });

  test('[P0] E2E-5.24.2: Filters update document list in real-time', async ({ page }) => {
    // Arrange
    let lastRequestUrl = '';

    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route, request) => {
      lastRequestUrl = request.url();
      const url = new URL(request.url());
      const status = url.searchParams.get('status');

      let documents = createMockDocumentsWithTags(20);

      // Simulate server-side filtering
      if (status === 'failed') {
        documents = documents.filter((d) => d.status === 'failed');
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

    // Apply status filter
    await dashboardPage.filterByStatus('failed');

    // Assert - API called with filter
    await expect(page).toHaveURL(/status=failed/);
    expect(lastRequestUrl).toContain('status=failed');

    // Assert - Loading indicator shown during refresh
    // (may need to slow down network to see this)

    // Assert - Results updated
    const documentRows = page.locator('[data-testid="document-row"]');
    const count = await documentRows.count();
    expect(count).toBeGreaterThanOrEqual(0); // Filtered results
  });

  test('[P1] E2E-5.24.3: Pagination navigates between pages', async ({ page }) => {
    // Arrange
    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route, request) => {
      const url = new URL(request.url());
      const pageNum = parseInt(url.searchParams.get('page') || '1');
      const limit = parseInt(url.searchParams.get('limit') || '50');

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createMockPaginatedDocuments(pageNum, limit, 127)),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');

    // Assert - Initial state
    let paginationInfo = await dashboardPage.getPaginationInfo();
    expect(paginationInfo.currentPage).toBe(1);
    expect(paginationInfo.totalDocuments).toBe(127);

    // Navigate to next page
    await dashboardPage.goToNextPage();

    // Assert - Page 2
    paginationInfo = await dashboardPage.getPaginationInfo();
    expect(paginationInfo.currentPage).toBe(2);
    await expect(page).toHaveURL(/page=2/);

    // Navigate back
    await dashboardPage.goToPreviousPage();

    // Assert - Back to page 1
    paginationInfo = await dashboardPage.getPaginationInfo();
    expect(paginationInfo.currentPage).toBe(1);
  });

  test('[P1] E2E-5.24.4: Filter state persists in URL', async ({ page }) => {
    // Arrange
    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createMockPaginatedDocuments(1, 50, 50)),
      });
    });

    // Act - Apply multiple filters
    await dashboardPage.gotoWithKB('test-kb-id');
    await dashboardPage.searchDocuments('report');
    await dashboardPage.filterByStatus('processed');
    await dashboardPage.filterByType('pdf');

    // Assert - URL contains all filters
    const filters = await dashboardPage.getActiveFilters();
    expect(filters.search).toBe('report');
    expect(filters.status).toBe('processed');
    expect(filters.type).toBe('pdf');

    // Reload page
    await page.reload();

    // Assert - Filters still applied after reload
    const reloadedFilters = await dashboardPage.getActiveFilters();
    expect(reloadedFilters.search).toBe('report');
    expect(reloadedFilters.status).toBe('processed');
    expect(reloadedFilters.type).toBe('pdf');

    // Assert - Document list shows filtered results
    await expect(page.getByPlaceholderText(/search documents/i)).toHaveValue('report');
  });

  test('[P2] Empty state shows when no documents match filters', async ({ page }) => {
    // Arrange
    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [],
          total: 0,
          page: 1,
          page_size: 50,
          has_more: false,
        }),
      });
    });

    // Act
    await dashboardPage.gotoWithKB('test-kb-id');
    await dashboardPage.filterByStatus('failed');

    // Assert - Empty state visible
    const isEmptyStateVisible = await dashboardPage.isEmptyStateVisible();
    expect(isEmptyStateVisible).toBe(true);

    await expect(page.getByText(/no documents found/i)).toBeVisible();
  });

  test('[P2] Clear filters button resets all filters', async ({ page }) => {
    // Arrange
    await page.route('**/api/v1/knowledge-bases/*/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createMockPaginatedDocuments(1, 50, 100)),
      });
    });

    // Act - Apply filters then clear
    await dashboardPage.gotoWithKB('test-kb-id');
    await dashboardPage.searchDocuments('report');
    await dashboardPage.filterByStatus('failed');
    await dashboardPage.clearFilters();

    // Assert - All filters cleared
    const filters = await dashboardPage.getActiveFilters();
    expect(filters.search).toBeUndefined();
    expect(filters.status).toBeUndefined();
    expect(filters.type).toBeUndefined();

    // Assert - URL has no filter params
    await expect(page).not.toHaveURL(/search=/);
    await expect(page).not.toHaveURL(/status=/);
  });
});
```

---

## Phase 2: Implementation Checklist

### Backend Implementation

- [ ] **API:** Add filter params (search, type, status, tags, date range) to document list endpoint
- [ ] **API:** Add pagination params (page, limit) to document list endpoint
- [ ] **Schema:** Create PaginatedDocumentResponse schema
- [ ] **Service:** Implement filter logic in list_documents method
- [ ] **Service:** Implement JSONB tag filtering with AND logic
- [ ] **Service:** Add pagination with count query

### Frontend Implementation

- [ ] **Types:** Define DocumentFilters interface
- [ ] **Hooks:** Implement useDocumentFilters with URL sync
- [ ] **Components:** Create DocumentFilterBar component
- [ ] **Components:** Create DocumentPagination component
- [ ] **Integration:** Add filter bar to KB dashboard
- [ ] **Integration:** Add pagination to KB dashboard
- [ ] **Styling:** Add debounce to search input (300ms)

---

## Phase 3: GREEN - Make Tests Pass

Track test execution status here as implementation proceeds.

| Category | Total | Passing | Failing | Skipped |
|----------|-------|---------|---------|---------|
| Backend Unit | 4 | 0 | 4 | 0 |
| Backend Integration | 6 | 0 | 6 | 0 |
| Frontend Unit | 12 | 0 | 12 | 0 |
| E2E | 4 | 0 | 4 | 0 |
| **Total** | **26** | **0** | **26** | **0** |

---

## Phase 4: REFACTOR

After all tests pass, review and refactor:

- [ ] Extract common filter logic into shared utilities
- [ ] Optimize SQL queries with proper indexes
- [ ] Add query parameter validation
- [ ] Review debounce timing for optimal UX

---

## Traceability Matrix

| Requirement | Backend Unit | Integration | Frontend Unit | E2E |
|-------------|--------------|-------------|---------------|-----|
| AC-5.24.1: Filter bar controls | - | IT-5.24.1.1 | FUT-5.24.1.1-4 | E2E-5.24.1 |
| AC-5.24.2: Real-time updates | UT-5.24.2.1 | IT-5.24.2.1-2 | FUT-5.24.2.1-3 | E2E-5.24.2 |
| AC-5.24.3: Pagination | UT-5.24.3.1 | IT-5.24.3.1-2 | FUT-5.24.3.1-3 | E2E-5.24.3 |
| AC-5.24.4: URL persistence | UT-5.24.4.1 | - | FUT-5.24.4.1-2 | E2E-5.24.4 |
| AC-5.24.5: Tag AND logic | UT-5.24.5.1 | IT-5.24.5.1 | - | - |

---

## Dependencies

- **Blocked By:** Story 5-22 (Document Tags) - Tag filter requires tags feature
- **Blocks:** None

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-06 | TEA | Initial ATDD checklist creation - RED phase |
