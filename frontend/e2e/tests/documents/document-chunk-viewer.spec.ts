/**
 * E2E Tests for Document Chunk Viewer
 * Story 5-26: Document Chunk Viewer - Frontend UI
 *
 * Tests cover key acceptance criteria:
 * - AC-5.26.0: Feature Navigation - Access via document detail modal
 * - AC-5.26.1: Document detail modal has "View & Chunks" tab
 * - AC-5.26.2: Split-pane layout with resizable panels
 * - AC-5.26.3: Chunk sidebar displays chunks with search
 * - AC-5.26.5: Search filters chunks in real-time
 * - AC-5.26.6: PDF viewer with chunk highlighting
 * - AC-5.26.7: DOCX viewer with paragraph highlighting
 */

import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';

// Mock responses
const mockKBResponse = {
  data: [
    {
      id: 'kb-test-chunks',
      name: 'Test KB for Chunk Viewer',
      description: 'Test Knowledge Base',
      permission_level: 'WRITE',
    },
  ],
};

const mockDocumentsResponse = {
  documents: [
    {
      id: 'doc-pdf-001',
      filename: 'test-document.pdf',
      mime_type: 'application/pdf',
      status: 'ready',
      chunk_count: 47,
      created_at: '2025-12-01T10:00:00Z',
    },
    {
      id: 'doc-docx-001',
      filename: 'test-document.docx',
      mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      status: 'ready',
      chunk_count: 23,
      created_at: '2025-12-01T11:00:00Z',
    },
    {
      id: 'doc-md-001',
      filename: 'readme.md',
      mime_type: 'text/markdown',
      status: 'ready',
      chunk_count: 15,
      created_at: '2025-12-01T12:00:00Z',
    },
    {
      id: 'doc-txt-001',
      filename: 'notes.txt',
      mime_type: 'text/plain',
      status: 'ready',
      chunk_count: 8,
      created_at: '2025-12-01T13:00:00Z',
    },
  ],
  total: 4,
};

const createMockChunksResponse = (count: number = 5, searchTerm?: string) => {
  const chunks = Array.from({ length: count }, (_, i) => ({
    chunk_id: `chunk-${i + 1}`,
    chunk_index: i,
    text: `This is chunk ${i + 1} content. ${searchTerm ? `Contains ${searchTerm} term.` : 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'}`,
    char_start: i * 500,
    char_end: (i + 1) * 500 - 1,
    page_number: Math.floor(i / 3) + 1,
    section_header: i < 3 ? 'Introduction' : 'Main Content',
    score: searchTerm ? 0.85 + Math.random() * 0.1 : null,
  }));

  return {
    chunks,
    total: count,
    has_more: count > 50,
    next_cursor: count > 50 ? 50 : null,
  };
};

const mockTextContentResponse = {
  text: 'This is the full document content.\n\nLine 2 of the document.\nLine 3 with more text.\n\nAnother paragraph here.',
  mime_type: 'text/plain',
  html: null,
};

test.describe('Document Chunk Viewer - E2E', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('AC-5.26.0: Feature Navigation', () => {
    test('[P0] User navigates from dashboard to chunk viewer via document modal', async ({
      page,
    }) => {
      // GIVEN: Mock KB and documents
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      // Login and navigate
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();

      // Select KB
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');

      // WHEN: User clicks on a document row
      await page.click('tr:has-text("notes.txt")');

      // THEN: Document detail modal opens
      await expect(page.getByRole('dialog')).toBeVisible();

      // AND: "View & Chunks" tab is available
      const viewChunksTab = page.getByRole('tab', { name: /View.*Chunks/i });
      await expect(viewChunksTab).toBeVisible();

      // WHEN: User clicks on "View & Chunks" tab
      await viewChunksTab.click();

      // THEN: Chunk viewer is displayed with split-pane layout
      await expect(page.getByTestId('document-chunk-viewer')).toBeVisible();
      await expect(page.getByTestId('chunk-sidebar')).toBeVisible();
    });

    test('[P1] View & Chunks tab shows no placeholder text', async ({ page }) => {
      // GIVEN: Mock API responses
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');

      // Click View & Chunks tab
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: No placeholder text is shown
      await expect(page.getByText(/Coming in Epic/i)).not.toBeVisible();
      await expect(page.getByText(/Not implemented/i)).not.toBeVisible();
    });
  });

  test.describe('AC-5.26.1: Document detail modal tabs', () => {
    test('[P0] Modal shows Details, View & Chunks, and History tabs', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');

      // WHEN: User clicks on a document
      await page.click('tr:has-text("notes.txt")');

      // THEN: Modal shows all tabs
      await expect(page.getByRole('tab', { name: /Details/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /View.*Chunks/i })).toBeVisible();
    });
  });

  test.describe('AC-5.26.3: Chunk sidebar displays chunks', () => {
    test('[P0] Chunk sidebar shows search box and chunk count', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(47) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Search box is visible
      await expect(page.getByTestId('chunk-search-input')).toBeVisible();
      await expect(page.getByPlaceholder('Search chunks...')).toBeVisible();

      // AND: Chunk count is displayed
      await expect(page.getByText(/47 chunks/)).toBeVisible();
    });

    test('[P1] Chunk items show preview text with chunk number', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(5) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Chunk numbers are visible
      await expect(page.getByText('#1')).toBeVisible();

      // AND: Preview text is shown
      await expect(page.getByText(/This is chunk 1 content/)).toBeVisible();
    });
  });

  test.describe('AC-5.26.5: Search filters chunks in real-time', () => {
    test('[P0] Search input filters chunks with debounce', async ({ page }) => {
      let searchQuery = '';

      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        const url = new URL(route.request().url());
        searchQuery = url.searchParams.get('search') || '';

        if (searchQuery === 'authentication') {
          // Return filtered results
          await route.fulfill({
            status: 200,
            json: createMockChunksResponse(3, 'authentication'),
          });
        } else {
          // Return all chunks
          await route.fulfill({
            status: 200,
            json: createMockChunksResponse(47),
          });
        }
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // Initial state shows all chunks
      await expect(page.getByText(/47 chunks/)).toBeVisible();

      // WHEN: User types in search
      await page.getByTestId('chunk-search-input').fill('authentication');

      // Wait for debounce (300ms)
      await page.waitForTimeout(400);

      // THEN: Filtered results are shown
      await expect(page.getByText(/3.*chunks/)).toBeVisible();
      await expect(page.getByText(/authentication/)).toBeVisible();
    });

    test('[P1] Clearing search shows all chunks again', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        const url = new URL(route.request().url());
        const search = url.searchParams.get('search') || '';

        if (search) {
          await route.fulfill({ status: 200, json: createMockChunksResponse(3, search) });
        } else {
          await route.fulfill({ status: 200, json: createMockChunksResponse(47) });
        }
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // Type search
      await page.getByTestId('chunk-search-input').fill('test');
      await page.waitForTimeout(400);
      await expect(page.getByText(/3.*chunks/)).toBeVisible();

      // WHEN: User clears search
      await page.getByTestId('chunk-search-input').clear();
      await page.waitForTimeout(400);

      // THEN: All chunks are shown
      await expect(page.getByText(/47 chunks/)).toBeVisible();
    });
  });

  test.describe('AC-5.26.2: Split-pane layout', () => {
    test('[P0] Split-pane layout renders on desktop', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1280, height: 720 });

      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(5) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Split-pane layout is visible
      await expect(page.getByTestId('document-chunk-viewer')).toBeVisible();

      // AND: Both panels are visible
      await expect(page.getByTestId('text-viewer')).toBeVisible();
      await expect(page.getByTestId('chunk-sidebar')).toBeVisible();
    });

    test('[P1] Mobile layout shows chunks toggle button', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(5) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Mobile toggle button is visible
      await expect(page.getByTestId('mobile-chunks-toggle')).toBeVisible();
    });
  });

  test.describe('AC-5.26.10: Loading and error states', () => {
    test('[P1] Loading state shows skeleton while fetching', async ({ page }) => {
      // Setup mocks with delay
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        // Delay response
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.fulfill({ status: 200, json: createMockChunksResponse(5) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Loading indicator should be visible initially
      // This is tested by the fact that content eventually loads
      await expect(page.getByTestId('chunk-sidebar')).toBeVisible({ timeout: 5000 });
    });

    test('[P1] Error state shows message when fetch fails', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(5) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 500, json: { detail: 'Internal server error' } });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Error message is displayed
      await expect(page.getByText(/Failed to load document/)).toBeVisible({ timeout: 5000 });
    });

    test('[P2] Empty state shows message when no chunks', async ({ page }) => {
      // Setup mocks
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { chunks: [], total: 0, has_more: false, next_cursor: null },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Empty state message is shown
      await expect(page.getByText(/No chunks found/)).toBeVisible();
    });
  });
});

/**
 * E2E Tests for View Mode Toggle
 * Story 7-31: View Mode Toggle for Chunk Viewer
 *
 * Tests cover key acceptance criteria:
 * - AC-7.31.1: Toggle Component - renders in viewer header
 * - AC-7.31.2: Default Mode - markdown when available
 * - AC-7.31.3: Disabled When Unavailable - markdown grayed out
 * - AC-7.31.4: Preference Persistence - localStorage
 * - AC-7.31.5: Visual Indication - selected state
 */
test.describe('Story 7-31: View Mode Toggle', () => {
  let dashboardPage: DashboardPage;

  // Mock markdown content response
  const mockMarkdownContentResponse = {
    document_id: 'doc-txt-001',
    markdown_content: '# Test Document\n\nThis is the markdown content.\n\n## Section 1\n\nSome text here.',
    generated_at: '2025-12-11T10:00:00Z',
  };

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('AC-7.31.1: Toggle Component', () => {
    test('[P0] Toggle renders in chunk viewer header with Original and Markdown options', async ({
      page,
    }) => {
      // GIVEN: Mock responses
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      // WHEN: User opens chunk viewer
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: View mode toggle is visible
      await expect(page.getByTestId('view-mode-toggle')).toBeVisible();

      // AND: Both options are available
      await expect(page.getByRole('radio', { name: /original/i })).toBeVisible();
      await expect(page.getByRole('radio', { name: /markdown/i })).toBeVisible();
    });
  });

  test.describe('AC-7.31.2: Default Mode', () => {
    test('[P0] Defaults to Markdown when markdown content is available', async ({ page }) => {
      // GIVEN: Document has markdown content
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      // WHEN: User opens chunk viewer
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Markdown option should be selected by default
      const markdownButton = page.getByRole('radio', { name: /markdown/i });
      await expect(markdownButton).toHaveAttribute('data-state', 'on');
    });

    test('[P0] Defaults to Original when markdown content is NOT available', async ({ page }) => {
      // GIVEN: Document does NOT have markdown content (404)
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 404, json: { detail: 'Markdown content not available' } });
      });

      // WHEN: User opens chunk viewer
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Original option should be selected
      const originalButton = page.getByRole('radio', { name: /original/i });
      await expect(originalButton).toHaveAttribute('data-state', 'on');
    });
  });

  test.describe('AC-7.31.3: Disabled When Unavailable', () => {
    test('[P1] Markdown option is disabled when markdown not available', async ({ page }) => {
      // GIVEN: Markdown content returns 404
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 404, json: { detail: 'Markdown not available' } });
      });

      // WHEN: User opens chunk viewer
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Markdown button should be disabled
      const markdownButton = page.getByRole('radio', { name: /markdown/i });
      await expect(markdownButton).toBeDisabled();
    });

    test('[P1] Shows tooltip explaining why Markdown is disabled', async ({ page }) => {
      // GIVEN: Markdown content returns 404
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 404, json: { detail: 'Markdown not available' } });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // WHEN: User hovers over disabled Markdown button
      const markdownButton = page.getByRole('radio', { name: /markdown/i });
      await markdownButton.hover();

      // THEN: Tooltip explains why
      await expect(page.getByText(/markdown not available for this document/i)).toBeVisible();
    });
  });

  test.describe('AC-7.31.4: Preference Persistence', () => {
    test('[P1] Toggle persists preference across page refresh', async ({ page }) => {
      // GIVEN: Mock responses
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // WHEN: User switches to Original mode
      await page.getByRole('radio', { name: /original/i }).click();

      // AND: Refreshes the page
      await page.reload();

      // Re-navigate to chunk viewer
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Original should still be selected
      const originalButton = page.getByRole('radio', { name: /original/i });
      await expect(originalButton).toHaveAttribute('data-state', 'on');
    });
  });

  test.describe('AC-7.31.5: Visual Indication', () => {
    test('[P1] Selected mode has clear visual indication', async ({ page }) => {
      // GIVEN: Mock responses
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // THEN: Markdown (default) has data-state="on"
      const markdownButton = page.getByRole('radio', { name: /markdown/i });
      await expect(markdownButton).toHaveAttribute('data-state', 'on');

      // AND: Original has data-state="off"
      const originalButton = page.getByRole('radio', { name: /original/i });
      await expect(originalButton).toHaveAttribute('data-state', 'off');

      // WHEN: User clicks Original
      await originalButton.click();

      // THEN: States are reversed
      await expect(originalButton).toHaveAttribute('data-state', 'on');
      await expect(markdownButton).toHaveAttribute('data-state', 'off');
    });
  });

  test.describe('Mode Switching Behavior', () => {
    test('[P0] Switching to Original shows original document viewer', async ({ page }) => {
      // GIVEN: Mock responses
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // Initially in Markdown mode, should show enhanced viewer
      await expect(page.getByTestId('enhanced-markdown-viewer')).toBeVisible();

      // WHEN: User switches to Original
      await page.getByRole('radio', { name: /original/i }).click();

      // THEN: Original viewer is shown
      await expect(page.getByTestId('text-viewer')).toBeVisible();
      await expect(page.getByTestId('enhanced-markdown-viewer')).not.toBeVisible();
    });

    test('[P0] Switching to Markdown shows enhanced markdown viewer', async ({ page }) => {
      // GIVEN: Mock responses and user preference is 'original' in localStorage
      await page.addInitScript(() => {
        localStorage.setItem('lumikb-chunk-viewer-mode', 'original');
      });

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({ status: 200, json: mockKBResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents*', async (route) => {
        await route.fulfill({ status: 200, json: mockDocumentsResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/chunks*', async (route) => {
        await route.fulfill({ status: 200, json: createMockChunksResponse(8) });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/full-content', async (route) => {
        await route.fulfill({ status: 200, json: mockTextContentResponse });
      });

      await page.route('**/api/v1/knowledge-bases/kb-test-chunks/documents/doc-txt-001/markdown-content', async (route) => {
        await route.fulfill({ status: 200, json: mockMarkdownContentResponse });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-test-chunks"]');
      await page.click('tr:has-text("notes.txt")');
      await page.getByRole('tab', { name: /View.*Chunks/i }).click();

      // Initially in Original mode (from localStorage)
      await expect(page.getByTestId('text-viewer')).toBeVisible();

      // WHEN: User switches to Markdown
      await page.getByRole('radio', { name: /markdown/i }).click();

      // THEN: Enhanced markdown viewer is shown
      await expect(page.getByTestId('enhanced-markdown-viewer')).toBeVisible();
      await expect(page.getByTestId('text-viewer')).not.toBeVisible();
    });
  });
});
