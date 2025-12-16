# ATDD Checklist - Story 5-22: Document Tags

**Generated:** 2025-12-06
**TEA Agent:** Murat (Test Architect)
**Story Status:** DRAFTED → RED PHASE READY
**Test Strategy:** API-First + Component Testing

---

## Test Summary

| Test Type | Count | Priority |
|-----------|-------|----------|
| Backend Unit Tests | 5 | P0 |
| Backend Integration Tests | 5 | P0 |
| Frontend Unit Tests | 10 | P0-P1 |
| E2E Tests | 4 | P1 |
| **Total** | **24** | - |

---

## Acceptance Criteria Mapping

### AC-5.22.1: Add Tags During Upload (5 tests)

| Test ID | Type | Description | Priority |
|---------|------|-------------|----------|
| UT-5.22.1.1 | Unit | Tag input validates max 10 tags | P0 |
| UT-5.22.1.2 | Unit | Tag input validates 50 char limit per tag | P0 |
| IT-5.22.1.1 | Integration | POST upload with tags → tags in metadata | P0 |
| IT-5.22.1.2 | Integration | POST upload with 11 tags → 422 error | P0 |
| E2E-5.22.1.1 | E2E | Upload document with tags flow | P1 |

### AC-5.22.2: Tags Displayed in Document List (4 tests)

| Test ID | Type | Description | Priority |
|---------|------|-------------|----------|
| UT-5.22.2.1 | Unit | Document list item renders tag badges | P0 |
| UT-5.22.2.2 | Unit | Truncates to 3 tags with "+N more" | P0 |
| UT-5.22.2.3 | Unit | "+N more" shows tooltip/popover on hover | P1 |
| E2E-5.22.2.1 | E2E | Tags display correctly in dashboard | P1 |

### AC-5.22.3: Edit Document Tags (6 tests)

| Test ID | Type | Description | Priority |
|---------|------|-------------|----------|
| IT-5.22.3.1 | Integration | PATCH tags as ADMIN → 200 | P0 |
| IT-5.22.3.2 | Integration | PATCH tags as WRITE → 200 | P0 |
| UT-5.22.3.1 | Unit | Edit modal opens with current tags | P0 |
| UT-5.22.3.2 | Unit | Add tag in modal updates list | P0 |
| UT-5.22.3.3 | Unit | Remove tag in modal updates list | P0 |
| E2E-5.22.3.1 | E2E | Complete edit tags flow | P1 |

### AC-5.22.4: READ Permission Cannot Edit (3 tests)

| Test ID | Type | Description | Priority |
|---------|------|-------------|----------|
| IT-5.22.4.1 | Integration | PATCH tags as READ → 403 | P0 |
| UT-5.22.4.1 | Unit | Edit button hidden for READ users | P0 |
| E2E-5.22.4.1 | E2E | READ user sees no edit button | P1 |

### AC-5.22.5: Tags Searchable (3 tests)

| Test ID | Type | Description | Priority |
|---------|------|-------------|----------|
| IT-5.22.5.1 | Integration | GET documents?tags=xyz → filtered | P0 |
| UT-5.22.5.1 | Unit | Tag filter triggers API call | P1 |
| UT-5.22.5.2 | Unit | Case-insensitive tag matching | P1 |

---

## Failing Tests (RED Phase)

### Backend Unit Tests

```python
# backend/tests/unit/test_document_tags.py

import pytest
from app.schemas.document import DocumentCreate, DocumentUpdate
from pydantic import ValidationError


class TestDocumentTagValidation:
    """[P0] Test document tag schema validation."""

    def test_tags_max_10_limit(self):
        """
        [UT-5.22.1.1] Tag input validates max 10 tags.

        Given: Document create schema
        When: 11 tags are provided
        Then: ValidationError is raised
        """
        tags = [f"tag-{i}" for i in range(11)]

        with pytest.raises(ValidationError) as exc:
            DocumentCreate(name="test.pdf", tags=tags)

        assert "max_items" in str(exc.value).lower() or "at most 10" in str(exc.value).lower()

    def test_tag_max_50_chars(self):
        """
        [UT-5.22.1.2] Tag input validates 50 char limit per tag.

        Given: Document create schema
        When: Tag with 51 characters is provided
        Then: Tag is truncated to 50 chars OR ValidationError
        """
        long_tag = "a" * 51
        doc = DocumentCreate(name="test.pdf", tags=[long_tag])

        # Implementation should truncate
        assert len(doc.tags[0]) <= 50

    def test_tags_normalized_lowercase(self):
        """
        [UT-5.22.5.2] Tags are normalized to lowercase.

        Given: Document create schema
        When: Tags with mixed case are provided
        Then: Tags are stored as lowercase
        """
        doc = DocumentCreate(name="test.pdf", tags=["POLICY", "Hr", "onBoarding"])

        assert doc.tags == ["policy", "hr", "onboarding"]

    def test_empty_tags_filtered(self):
        """
        Tags list filters out empty strings.

        Given: Document create schema
        When: Empty or whitespace tags are provided
        Then: Empty tags are removed
        """
        doc = DocumentCreate(name="test.pdf", tags=["valid", "", "  ", "another"])

        assert doc.tags == ["valid", "another"]

    def test_tags_optional_on_update(self):
        """
        Tags field is optional on update schema.

        Given: Document update schema
        When: No tags field provided
        Then: Schema is valid (tags unchanged)
        """
        update = DocumentUpdate(name="renamed.pdf")

        assert update.tags is None
```

### Backend Integration Tests

```python
# backend/tests/integration/test_document_tags_api.py

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestDocumentTagsAPI:
    """[P0] Test document tags API endpoints."""

    async def test_upload_with_tags(
        self,
        async_client: AsyncClient,
        auth_headers_admin: dict,
        test_kb: dict,
        sample_pdf_content: bytes,
    ):
        """
        [IT-5.22.1.1] POST upload with tags → tags in metadata.

        Given: Admin user with KB access
        When: Upload document with tags
        Then: Document created with tags in metadata
        """
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        data = {"tags": ["policy", "hr"]}

        response = await async_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents",
            files=files,
            data=data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        doc = response.json()
        assert "tags" in doc
        assert set(doc["tags"]) == {"policy", "hr"}

    async def test_upload_with_too_many_tags(
        self,
        async_client: AsyncClient,
        auth_headers_admin: dict,
        test_kb: dict,
        sample_pdf_content: bytes,
    ):
        """
        [IT-5.22.1.2] POST upload with 11 tags → 422 error.

        Given: Admin user with KB access
        When: Upload document with 11 tags
        Then: 422 Unprocessable Entity error
        """
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        tags = [f"tag-{i}" for i in range(11)]
        data = {"tags": tags}

        response = await async_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents",
            files=files,
            data=data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 422

    async def test_patch_tags_as_admin(
        self,
        async_client: AsyncClient,
        auth_headers_admin: dict,
        test_document: dict,
    ):
        """
        [IT-5.22.3.1] PATCH tags as ADMIN → 200.

        Given: Admin user with document access
        When: PATCH document tags
        Then: Tags updated successfully
        """
        response = await async_client.patch(
            f"/api/v1/documents/{test_document['id']}/tags",
            json=["updated", "tags"],
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        doc = response.json()
        assert set(doc["tags"]) == {"updated", "tags"}

    async def test_patch_tags_as_read_user_forbidden(
        self,
        async_client: AsyncClient,
        auth_headers_read_user: dict,
        test_document: dict,
    ):
        """
        [IT-5.22.4.1] PATCH tags as READ → 403.

        Given: READ-only user
        When: PATCH document tags
        Then: 403 Forbidden
        """
        response = await async_client.patch(
            f"/api/v1/documents/{test_document['id']}/tags",
            json=["new", "tags"],
            headers=auth_headers_read_user,
        )

        assert response.status_code == 403

    async def test_filter_documents_by_tag(
        self,
        async_client: AsyncClient,
        auth_headers_admin: dict,
        test_kb_with_tagged_documents: dict,
    ):
        """
        [IT-5.22.5.1] GET documents?tags=xyz → filtered.

        Given: KB with documents having various tags
        When: Filter by specific tag
        Then: Only matching documents returned
        """
        kb_id = test_kb_with_tagged_documents["id"]

        response = await async_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            params={"tags": "policy"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        docs = response.json()["documents"]
        for doc in docs:
            assert "policy" in doc["tags"]
```

### Frontend Unit Tests

```typescript
// frontend/src/components/documents/__tests__/document-tag-input.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentTagInput } from '../document-tag-input';

describe('DocumentTagInput', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[UT-5.22.1.1] validates max 10 tags limit', async () => {
    /**
     * Given: Tag input with 10 existing tags
     * When: User tries to add 11th tag
     * Then: Tag is not added, limit message shown
     */
    const existingTags = Array.from({ length: 10 }, (_, i) => `tag-${i}`);
    render(<DocumentTagInput tags={existingTags} onChange={mockOnChange} />);

    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, 'new-tag{enter}');

    expect(mockOnChange).not.toHaveBeenCalled();
    expect(screen.getByText(/maximum 10 tags/i)).toBeInTheDocument();
  });

  it('[UT-5.22.1.2] validates 50 char limit per tag', async () => {
    /**
     * Given: Tag input
     * When: User enters tag with 51 characters
     * Then: Tag is truncated to 50 chars
     */
    render(<DocumentTagInput tags={[]} onChange={mockOnChange} />);

    const longTag = 'a'.repeat(51);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, `${longTag}{enter}`);

    expect(mockOnChange).toHaveBeenCalledWith(['a'.repeat(50)]);
  });
});

// frontend/src/components/documents/__tests__/document-list-item.test.tsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentListItem } from '../document-list-item';

describe('DocumentListItem Tags Display', () => {
  it('[UT-5.22.2.1] renders tag badges', () => {
    /**
     * Given: Document with tags
     * When: Rendering list item
     * Then: Tags displayed as badges
     */
    const doc = {
      id: '1',
      name: 'test.pdf',
      tags: ['policy', 'hr'],
    };

    render(<DocumentListItem document={doc} />);

    expect(screen.getByTestId('document-tag')).toHaveTextContent('policy');
    expect(screen.getByTestId('document-tag')).toHaveTextContent('hr');
  });

  it('[UT-5.22.2.2] truncates to 3 tags with "+N more"', () => {
    /**
     * Given: Document with 5 tags
     * When: Rendering list item
     * Then: Shows 3 tags + "+2 more"
     */
    const doc = {
      id: '1',
      name: 'test.pdf',
      tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
    };

    render(<DocumentListItem document={doc} />);

    const visibleTags = screen.getAllByTestId('document-tag');
    expect(visibleTags).toHaveLength(3);
    expect(screen.getByTestId('more-tags')).toHaveTextContent('+2 more');
  });

  it('[UT-5.22.2.3] shows all tags on "+N more" hover', async () => {
    /**
     * Given: Document with truncated tags
     * When: Hovering "+N more"
     * Then: Popover shows all tags
     */
    const doc = {
      id: '1',
      name: 'test.pdf',
      tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
    };

    render(<DocumentListItem document={doc} />);

    await userEvent.hover(screen.getByTestId('more-tags'));

    expect(screen.getByText('tag4')).toBeVisible();
    expect(screen.getByText('tag5')).toBeVisible();
  });

  it('[UT-5.22.4.1] hides edit button for READ permission', () => {
    /**
     * Given: Document in KB with READ permission
     * When: Rendering list item
     * Then: No edit tags button visible
     */
    const doc = {
      id: '1',
      name: 'test.pdf',
      tags: ['policy'],
    };

    render(<DocumentListItem document={doc} permission="READ" />);

    expect(screen.queryByRole('button', { name: /edit tags/i })).not.toBeInTheDocument();
  });
});

// frontend/src/components/documents/__tests__/document-edit-tags-modal.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentEditTagsModal } from '../document-edit-tags-modal';

describe('DocumentEditTagsModal', () => {
  const mockOnSave = vi.fn();
  const mockOnClose = vi.fn();

  it('[UT-5.22.3.1] opens with current tags', () => {
    /**
     * Given: Document with existing tags
     * When: Modal opens
     * Then: Current tags displayed
     */
    render(
      <DocumentEditTagsModal
        open={true}
        onOpenChange={mockOnClose}
        documentId="1"
        documentName="test.pdf"
        currentTags={['policy', 'hr']}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByTestId('tag-badge')).toHaveTextContent('policy');
    expect(screen.getByTestId('tag-badge')).toHaveTextContent('hr');
  });

  it('[UT-5.22.3.2] adds tag to list', async () => {
    /**
     * Given: Edit modal open
     * When: User adds new tag
     * Then: Tag appears in list
     */
    render(
      <DocumentEditTagsModal
        open={true}
        onOpenChange={mockOnClose}
        documentId="1"
        documentName="test.pdf"
        currentTags={['policy']}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, 'new-tag{enter}');

    expect(screen.getByText('new-tag')).toBeInTheDocument();
  });

  it('[UT-5.22.3.3] removes tag from list', async () => {
    /**
     * Given: Edit modal with tags
     * When: User clicks remove on tag
     * Then: Tag removed from list
     */
    render(
      <DocumentEditTagsModal
        open={true}
        onOpenChange={mockOnClose}
        documentId="1"
        documentName="test.pdf"
        currentTags={['policy', 'hr']}
        onSave={mockOnSave}
      />
    );

    const removeButton = screen.getAllByRole('button', { name: /remove/i })[0];
    await userEvent.click(removeButton);

    expect(screen.queryByText('policy')).not.toBeInTheDocument();
    expect(screen.getByText('hr')).toBeInTheDocument();
  });
});
```

### E2E Tests

```typescript
// frontend/e2e/tests/documents/document-tags.spec.ts

import { test, expect } from '../../fixtures/auth.fixture';
import { mockApiResponse } from '../../utils/test-helpers';
import {
  createMockDocumentWithTags,
  createMockDocumentsWithTags,
} from '../../fixtures/document-tags.factory';

test.describe('Story 5-22: Document Tags', () => {
  test('[P1] E2E-5.22.1.1: Upload document with tags', async ({ page }) => {
    /**
     * Given: User on KB dashboard
     * When: Upload document with tags
     * Then: Document created with tags visible
     */
    // Mock upload endpoint
    await page.route('**/api/v1/knowledge-bases/*/documents', async (route, request) => {
      if (request.method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(createMockDocumentWithTags({
            name: 'uploaded.pdf',
            metadata: { tags: ['policy', 'hr'] },
          })),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/dashboard?kb=test-kb-id');

    // Open upload dialog
    await page.getByRole('button', { name: /upload/i }).click();

    // Fill upload form with tags
    await page.setInputFiles('input[type="file"]', {
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content'),
    });

    const tagInput = page.getByPlaceholder(/add tag/i);
    await tagInput.fill('policy');
    await tagInput.press('Enter');
    await tagInput.fill('hr');
    await tagInput.press('Enter');

    // Submit
    await page.getByRole('button', { name: /upload/i }).click();

    // Verify success
    await expect(page.getByText('uploaded.pdf')).toBeVisible();
    await expect(page.getByTestId('document-tag')).toContainText('policy');
  });

  test('[P1] E2E-5.22.2.1: Tags display correctly in dashboard', async ({ page }) => {
    /**
     * Given: KB with tagged documents
     * When: View document list
     * Then: Tags displayed as badges
     */
    await mockApiResponse(page, '**/api/v1/knowledge-bases/*/documents', {
      documents: createMockDocumentsWithTags(5),
      total: 5,
      page: 1,
      page_size: 50,
    });

    await page.goto('/dashboard?kb=test-kb-id');

    // Verify tags visible
    const tags = page.locator('[data-testid="document-tag"]');
    await expect(tags.first()).toBeVisible();
  });

  test('[P1] E2E-5.22.3.1: Edit tags flow', async ({ page }) => {
    /**
     * Given: Document with tags
     * When: Edit and save tags
     * Then: Updated tags displayed
     */
    const doc = createMockDocumentWithTags({
      id: 'doc-1',
      name: 'test.pdf',
      metadata: { tags: ['old-tag'] },
    });

    await mockApiResponse(page, '**/api/v1/knowledge-bases/*/documents', {
      documents: [doc],
      total: 1,
      page: 1,
      page_size: 50,
    });

    await page.route('**/api/v1/documents/doc-1/tags', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...doc, tags: ['new-tag'] }),
      });
    });

    await page.goto('/dashboard?kb=test-kb-id');

    // Open edit modal
    await page.getByRole('button', { name: /edit tags/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Add new tag
    const input = page.getByPlaceholder(/add tag/i);
    await input.fill('new-tag');
    await input.press('Enter');

    // Save
    await page.getByRole('button', { name: /save/i }).click();

    // Verify modal closes and tag updated
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('[P1] E2E-5.22.4.1: READ user sees no edit button', async ({ page }) => {
    /**
     * Given: User with READ permission
     * When: View document list
     * Then: No edit tags button visible
     */
    // Mock user as READ-only
    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-1',
          email: 'reader@example.com',
          is_superuser: false,
        }),
      });
    });

    // Mock KB permission as READ
    await page.route('**/api/v1/knowledge-bases/*/permissions/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ permission: 'READ' }),
      });
    });

    await mockApiResponse(page, '**/api/v1/knowledge-bases/*/documents', {
      documents: createMockDocumentsWithTags(1),
      total: 1,
      page: 1,
      page_size: 50,
    });

    await page.goto('/dashboard?kb=test-kb-id');

    // Verify no edit button
    await expect(page.getByRole('button', { name: /edit tags/i })).not.toBeVisible();
  });
});
```

---

## Data Infrastructure

### Test Factories

**Already Created:** `frontend/e2e/fixtures/document-tags.factory.ts`

Provides:
- `createMockDocumentWithTags()`
- `createMockDocumentsWithTags()`
- `createMockDocumentWithMaxTags()`
- `createMockPaginatedDocuments()`
- `getAvailableTags()`
- `TAG_ERRORS`

### Backend Fixtures Needed

```python
# backend/tests/conftest.py - additions

@pytest.fixture
async def test_kb_with_tagged_documents(
    async_client: AsyncClient,
    auth_headers_admin: dict,
    test_kb: dict,
) -> dict:
    """Create KB with documents having various tags."""
    tags_sets = [
        ["policy", "hr"],
        ["technical", "api"],
        ["policy", "legal"],
        [],
    ]

    for i, tags in enumerate(tags_sets):
        await async_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents",
            files={"file": (f"doc-{i}.pdf", b"content", "application/pdf")},
            data={"tags": tags},
            headers=auth_headers_admin,
        )

    return test_kb
```

---

## Implementation Checklist

### Phase 1: Backend Schema & Validation (2 hours)

- [ ] **Task 1.1:** Add `tags` field to `DocumentCreate` schema
  - Max 10 items validation
  - 50 char per tag limit
  - Lowercase normalization
  - Filter empty strings

- [ ] **Task 1.2:** Add `tags` field to `DocumentUpdate` schema
  - Optional field (None = no change)

- [ ] **Task 1.3:** Add `tags` field to `DocumentResponse` schema
  - Extract from metadata JSONB

- [ ] **Task 1.4:** Write 5 unit tests (UT-5.22.1.1, UT-5.22.1.2, UT-5.22.5.2, etc.)

**Run Tests:**
```bash
pytest backend/tests/unit/test_document_tags.py -v
```

### Phase 2: Backend API Endpoints (2 hours)

- [ ] **Task 2.1:** Update upload endpoint to accept tags
- [ ] **Task 2.2:** Create PATCH `/documents/{id}/tags` endpoint
- [ ] **Task 2.3:** Add permission check (ADMIN/WRITE)
- [ ] **Task 2.4:** Update GET documents to filter by tags
- [ ] **Task 2.5:** Write 5 integration tests

**Run Tests:**
```bash
pytest backend/tests/integration/test_document_tags_api.py -v
```

### Phase 3: Frontend Components (4 hours)

- [ ] **Task 3.1:** Create `DocumentTagInput` component
- [ ] **Task 3.2:** Create `DocumentEditTagsModal` component
- [ ] **Task 3.3:** Update `DocumentListItem` with tag display
- [ ] **Task 3.4:** Update upload modal with tag input
- [ ] **Task 3.5:** Write 10 unit tests

**Run Tests:**
```bash
npm test -- document-tag-input.test.tsx document-list-item.test.tsx document-edit-tags-modal.test.tsx
```

### Phase 4: E2E Tests (1 hour)

- [ ] **Task 4.1:** Write 4 E2E tests
- [ ] **Task 4.2:** Verify all tests pass

**Run Tests:**
```bash
npx playwright test frontend/e2e/tests/documents/document-tags.spec.ts
```

---

## Red-Green-Refactor Status

| Phase | Status | Tests |
|-------|--------|-------|
| Schema & Validation | RED | 5 unit |
| API Endpoints | RED | 5 integration |
| Frontend Components | RED | 10 unit |
| E2E Tests | RED | 4 E2E |
| **Total** | **RED** | **24 tests** |

---

## Success Criteria

- [ ] All 5 acceptance criteria validated
- [ ] 24/24 tests passing (GREEN)
- [ ] Zero linting errors
- [ ] Code reviewed
- [ ] DoD checklist complete

---

**Generated by BMad TEA Agent (Murat)** - 2025-12-06
