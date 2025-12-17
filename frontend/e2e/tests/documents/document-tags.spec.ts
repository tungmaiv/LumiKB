/**
 * E2E Tests for Document Tags
 * Story 5-22: Document Tags
 *
 * Tests cover all 5 acceptance criteria:
 * - AC-5.22.1: Upload document with tags (ADMIN/WRITE users only)
 * - AC-5.22.2: Tags displayed in document list
 * - AC-5.22.3: Edit tags via modal (ADMIN/WRITE users only)
 * - AC-5.22.4: READ-only users cannot see edit option
 * - AC-5.22.5: Search/filter documents by tags
 */

import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';
import {
  createMockDocumentWithTags,
  createMockDocumentsWithTags,
  createMockDocumentWithMaxTags,
  createTagUpdateResponse,
  getAvailableTags,
  TAG_ERRORS,
} from '../../fixtures/document-tags.factory';

test.describe('Document Tags - E2E', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('AC-5.22.1: Upload document with tags', () => {
    test('[P0] User can add tags during document upload', async ({ page }) => {
      // GIVEN: Mock KB with WRITE permission
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [
              {
                id: 'kb-1',
                name: 'Test KB',
                description: 'Test Knowledge Base',
                permission_level: 'WRITE',
              },
            ],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents', async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            json: { documents: createMockDocumentsWithTags(5), total: 5 },
          });
        } else if (route.request().method() === 'POST') {
          // Mock successful upload with tags
          const formData = route.request().postData();
          await route.fulfill({
            status: 201,
            json: createMockDocumentWithTags({
              id: 'doc-new',
              name: 'uploaded-file.pdf',
              metadata: { tags: ['finance', 'quarterly'] },
            }),
          });
        }
      });

      // Login and navigate to dashboard
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();

      // Select the KB
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User opens upload modal
      await page.click('button:has-text("Upload")');
      await expect(page.getByRole('dialog')).toBeVisible();

      // AND: Enters tags in the tag input
      const tagInput = page.locator('[data-testid="document-tag-input"] input');
      await tagInput.fill('finance');
      await tagInput.press('Enter');
      await tagInput.fill('quarterly');
      await tagInput.press('Enter');

      // THEN: Tags appear as chips
      await expect(page.getByText('finance')).toBeVisible();
      await expect(page.getByText('quarterly')).toBeVisible();
    });

    test('[P1] Tags are normalized to lowercase during upload', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Upload")');

      // WHEN: User enters uppercase tag
      const tagInput = page.locator('[data-testid="document-tag-input"] input');
      await tagInput.fill('UPPERCASE');
      await tagInput.press('Enter');

      // THEN: Tag is displayed in lowercase
      await expect(page.getByText('uppercase')).toBeVisible();
      await expect(page.getByText('UPPERCASE')).not.toBeVisible();
    });

    test('[P1] Duplicate tags are prevented during upload', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Upload")');

      const tagInput = page.locator('[data-testid="document-tag-input"] input');

      // Add first tag
      await tagInput.fill('finance');
      await tagInput.press('Enter');

      // WHEN: User tries to add duplicate tag
      await tagInput.fill('finance');
      await tagInput.press('Enter');

      // THEN: Only one instance of the tag exists
      const tagChips = page.locator('[data-testid="tag-chip"]').filter({ hasText: 'finance' });
      await expect(tagChips).toHaveCount(1);
    });

    test('[P1] Maximum 10 tags enforced during upload', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Upload")');

      const tagInput = page.locator('[data-testid="document-tag-input"] input');

      // Add 10 tags
      for (let i = 1; i <= 10; i++) {
        await tagInput.fill(`tag${i}`);
        await tagInput.press('Enter');
      }

      // WHEN: User tries to add 11th tag
      // THEN: Input should be disabled or show max message
      await expect(tagInput).toBeDisabled();
      await expect(page.getByPlaceholder('Maximum tags reached')).toBeVisible();
    });
  });

  test.describe('AC-5.22.2: Tags displayed in document list', () => {
    test('[P0] Tags are visible in document list', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Financial Report Q4.pdf',
                metadata: { tags: ['finance', 'quarterly', 'report'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Tags are visible in the document row
      await expect(page.getByText('finance')).toBeVisible();
      await expect(page.getByText('quarterly')).toBeVisible();
      await expect(page.getByText('report')).toBeVisible();
    });

    test('[P1] Tags overflow shows +N more indicator', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Document with many tags.pdf',
                metadata: {
                  tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6'],
                },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Some tags are visible and overflow indicator shows
      await expect(page.getByText('tag1')).toBeVisible();
      await expect(page.getByText(/\+\d+ more/)).toBeVisible();
    });

    test('[P2] Documents with no tags show empty state', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Document without tags.pdf',
                metadata: { tags: [] },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: No tags are displayed (empty or dash indicator)
      const documentRow = page.locator('[data-testid="document-row"]').first();
      await expect(documentRow).toBeVisible();
      // Tags column should be empty or show placeholder
      const tagsCell = documentRow.locator('[data-testid="document-tags"]');
      const tagCount = await tagsCell.locator('[data-testid="tag-chip"]').count();
      expect(tagCount).toBe(0);
    });
  });

  test.describe('AC-5.22.3: Edit tags via modal', () => {
    test('[P0] WRITE user can open edit tags modal', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Editable Document.pdf',
                metadata: { tags: ['original'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User clicks on document row actions menu
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');

      // AND: Clicks "Edit Tags" option
      await page.click('text=Edit Tags');

      // THEN: Edit tags modal opens
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText('Edit Document Tags')).toBeVisible();
      await expect(page.getByText('original')).toBeVisible();
    });

    test('[P0] User can add new tags in edit modal', async ({ page }) => {
      let updatedTags: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Editable Document.pdf',
                metadata: { tags: ['existing'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents/doc-1/tags', async (route) => {
        const body = JSON.parse(route.request().postData() || '{}');
        updatedTags = body.tags;
        await route.fulfill({
          status: 200,
          json: createTagUpdateResponse('doc-1', 'Editable Document.pdf', body.tags),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Open edit modal
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');
      await page.click('text=Edit Tags');

      // WHEN: User adds new tags
      const tagInput = page.locator('[data-testid="edit-tags-modal"] input');
      await tagInput.fill('newtag');
      await tagInput.press('Enter');

      // AND: Clicks save
      await page.click('button:has-text("Save")');

      // THEN: API received updated tags
      await page.waitForTimeout(500);
      expect(updatedTags).toContain('existing');
      expect(updatedTags).toContain('newtag');
    });

    test('[P0] User can remove tags in edit modal', async ({ page }) => {
      let updatedTags: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Editable Document.pdf',
                metadata: { tags: ['tag1', 'tag2', 'toremove'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents/doc-1/tags', async (route) => {
        const body = JSON.parse(route.request().postData() || '{}');
        updatedTags = body.tags;
        await route.fulfill({
          status: 200,
          json: createTagUpdateResponse('doc-1', 'Editable Document.pdf', body.tags),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Open edit modal
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');
      await page.click('text=Edit Tags');

      // WHEN: User removes a tag
      await page.click('button[aria-label="Remove toremove"]');

      // AND: Clicks save
      await page.click('button:has-text("Save")');

      // THEN: API received updated tags without removed one
      await page.waitForTimeout(500);
      expect(updatedTags).toContain('tag1');
      expect(updatedTags).toContain('tag2');
      expect(updatedTags).not.toContain('toremove');
    });

    test('[P1] Cancel discards changes', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Editable Document.pdf',
                metadata: { tags: ['original'] },
              }),
            ],
            total: 1,
          },
        });
      });

      let apiCalled = false;
      await page.route('**/api/v1/knowledge-bases/kb-1/documents/doc-1/tags', async (route) => {
        apiCalled = true;
        await route.fulfill({ status: 200, json: {} });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Open edit modal
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');
      await page.click('text=Edit Tags');

      // Add new tag
      const tagInput = page.locator('[data-testid="edit-tags-modal"] input');
      await tagInput.fill('newtag');
      await tagInput.press('Enter');

      // WHEN: User clicks Cancel
      await page.click('button:has-text("Cancel")');

      // THEN: Modal closes without API call
      await expect(page.getByRole('dialog')).not.toBeVisible();
      expect(apiCalled).toBe(false);
    });
  });

  test.describe('AC-5.22.4: READ-only users cannot see edit option', () => {
    test('[P0] Edit Tags option is hidden for READ-only users', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Read Only Document.pdf',
                metadata: { tags: ['readonly'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Document actions menu does not exist or Edit Tags is hidden
      const actionsButton = page.locator('[data-testid="document-actions"]');

      if (await actionsButton.isVisible()) {
        await actionsButton.click();
        await expect(page.getByText('Edit Tags')).not.toBeVisible();
      }
    });

    test('[P1] ADMIN users can see edit option', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'ADMIN' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Admin Document.pdf',
                metadata: { tags: ['admin'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User clicks document actions
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');

      // THEN: Edit Tags option is visible
      await expect(page.getByText('Edit Tags')).toBeVisible();
    });
  });

  test.describe('AC-5.22.5: Search/filter documents by tags', () => {
    test('[P0] User can filter documents by selecting tags', async ({ page }) => {
      let lastTagsFilter: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastTagsFilter = url.searchParams.getAll('tags');

        // Return filtered results based on tags
        const allDocs = createMockDocumentsWithTags(10);
        const filteredDocs =
          lastTagsFilter.length > 0
            ? allDocs.filter((doc) => lastTagsFilter.some((tag) => doc.metadata.tags.includes(tag)))
            : allDocs;

        await route.fulfill({
          status: 200,
          json: { documents: filteredDocs, total: filteredDocs.length },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects tag filter
      await dashboardPage.filterByTags(['finance']);

      // THEN: API was called with tags filter
      await page.waitForTimeout(500);
      expect(lastTagsFilter).toContain('finance');
    });

    test('[P1] Tag filter updates URL', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects tags
      await dashboardPage.filterByTags(['legal', 'compliance']);

      // THEN: URL contains tag filters
      await page.waitForTimeout(500);
      const url = page.url();
      expect(url).toMatch(/tags=legal|tags.*compliance/);
    });

    test('[P1] Multiple tags filter with AND logic', async ({ page }) => {
      let lastTagsFilter: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastTagsFilter = url.searchParams.getAll('tags');

        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(3), total: 3 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects multiple tags
      await dashboardPage.filterByTags(['finance', 'quarterly']);

      // THEN: API receives both tags
      await page.waitForTimeout(500);
      expect(lastTagsFilter).toContain('finance');
      expect(lastTagsFilter).toContain('quarterly');
    });

    test('[P2] Clear filters removes tag filter', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Apply tag filter
      await dashboardPage.filterByTags(['finance']);
      await page.waitForTimeout(500);

      // WHEN: User clears filters
      await dashboardPage.clearFilters();

      // THEN: URL no longer contains tag filter
      await page.waitForTimeout(500);
      const url = page.url();
      expect(url).not.toMatch(/tags=/);
    });
  });

  test.describe('Validation and Error Handling', () => {
    test('[P1] Tag length validation (max 50 characters)', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Upload")');

      // WHEN: User enters a very long tag
      const tagInput = page.locator('[data-testid="document-tag-input"] input');
      const longTag = 'a'.repeat(60);
      await tagInput.fill(longTag);
      await tagInput.press('Enter');

      // THEN: Tag is truncated to 50 characters
      const truncatedTag = 'a'.repeat(50);
      await expect(page.getByText(truncatedTag)).toBeVisible();
    });

    test('[P2] Backend validation error is displayed', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            documents: [
              createMockDocumentWithTags({
                id: 'doc-1',
                name: 'Document.pdf',
                metadata: { tags: ['existing'] },
              }),
            ],
            total: 1,
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents/doc-1/tags', async (route) => {
        await route.fulfill({
          status: 400,
          json: TAG_ERRORS.TOO_MANY_TAGS,
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Open edit modal
      await page.click('[data-testid="document-row"] [data-testid="document-actions"]');
      await page.click('text=Edit Tags');

      // Add many tags
      const tagInput = page.locator('[data-testid="edit-tags-modal"] input');
      for (let i = 1; i <= 10; i++) {
        await tagInput.fill(`tag${i}`);
        await tagInput.press('Enter');
      }

      // WHEN: Save triggers validation error
      await page.click('button:has-text("Save")');

      // THEN: Error message is displayed
      await expect(page.getByText(/Maximum 10 tags allowed/i)).toBeVisible();
    });
  });
});
