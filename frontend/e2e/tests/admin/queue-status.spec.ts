/**
 * E2E Tests for Queue Status Dashboard
 * Story 5-4: Processing Queue Status
 *
 * Tests cover all 6 acceptance criteria:
 * - AC-5.4.1: Admin sees queue status for all active Celery queues
 * - AC-5.4.2: Each queue displays pending, active, and worker metrics
 * - AC-5.4.3: Task details include task_id, task_name, status, started_at, estimated_duration
 * - AC-5.4.4: Workers marked "offline" if no heartbeat received in 60s
 * - AC-5.4.5: Queue monitoring gracefully handles Celery inspect failures
 * - AC-5.4.6: Non-admin users receive 403 Forbidden
 */

import { test, expect } from '@playwright/test';
import { AdminPage, QueuePage } from '../../pages';
import {
  createAllQueues,
  createQueueWithNoWorkers,
  createQueueWithHighLoad,
  createQueueWithOfflineWorkers,
  createUnavailableQueue,
  createTaskList,
} from '../../fixtures/queue.factory';

test.describe('Queue Status Dashboard - E2E', () => {
  let adminPage: AdminPage;
  let queuePage: QueuePage;

  test.beforeEach(async ({ page }) => {
    adminPage = new AdminPage(page);
    queuePage = new QueuePage(page);

    // Login as admin
    await adminPage.loginAsAdmin();
  });

  test('[P0] Admin navigates to /admin/queue and sees all 3 queue cards - AC-5.4.1', async ({
    page,
  }) => {
    // GIVEN: Mock API returns 3 queues
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAllQueues()),
      });
    });

    // WHEN: Admin navigates to /admin/queue
    await queuePage.goto();

    // THEN: Page displays 3 queue cards
    await expect(queuePage.getQueueCard('document_processing')).toBeVisible();
    await expect(queuePage.getQueueCard('embedding_generation')).toBeVisible();
    await expect(queuePage.getQueueCard('export_generation')).toBeVisible();

    // AND: Each queue displays metrics
    const docProcessingCard = queuePage.getQueueCard('document_processing');
    await expect(docProcessingCard.locator('[data-testid="pending-tasks"]')).toBeVisible();
    await expect(docProcessingCard.locator('[data-testid="active-tasks"]')).toBeVisible();
    await expect(docProcessingCard.locator('[data-testid="workers-online"]')).toBeVisible();
  });

  test('[P1] Queue cards display warning badges for high load and no workers - AC-5.4.2', async ({
    page,
  }) => {
    // GIVEN: Mock queues with warning conditions
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          createQueueWithHighLoad('document_processing'),
          createQueueWithNoWorkers('embedding_generation'),
          createQueueWithOfflineWorkers('export_generation'),
        ]),
      });
    });

    // WHEN: Admin views queue status page
    await queuePage.goto();

    // THEN: Document processing queue shows high load badge (pending > 100)
    await expect(
      queuePage.getQueueCard('document_processing').getByText(/high load/i)
    ).toBeVisible();

    // AND: Embedding generation queue shows no workers warning
    await expect(
      queuePage.getQueueCard('embedding_generation').getByText(/no workers available/i)
    ).toBeVisible();

    // AND: Export generation queue shows offline workers warning
    await expect(
      queuePage.getQueueCard('export_generation').getByText(/\d+ worker.*offline/i)
    ).toBeVisible();
  });

  test('[P1] Admin clicks "View Active Tasks" and sees task details modal - AC-5.4.3', async ({
    page,
  }) => {
    // GIVEN: Mock queue status and task list
    const mockTasks = createTaskList(5, false); // active tasks

    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAllQueues()),
      });
    });

    await page.route('**/api/v1/admin/queue/document_processing/tasks', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTasks),
      });
    });

    await queuePage.goto();

    // WHEN: Admin clicks "View Active Tasks" for document_processing queue
    await queuePage.getViewActiveTasksButton('document_processing').click();

    // THEN: Task list modal is visible
    await expect(page.getByRole('dialog')).toBeVisible();

    // AND: Modal displays task table with all required columns
    const headers = queuePage.getTaskTableHeaders();
    await expect(headers).toContainText([
      'Task ID',
      'Task Name',
      'Status',
      'Started At',
      'Estimated Duration',
    ]);

    // AND: Task rows are displayed
    const taskRows = page.locator('[data-testid="task-row"]');
    await expect(taskRows).toHaveCount(5);

    // AND: First task has all required fields
    const firstTask = taskRows.first();
    await expect(firstTask.locator('[data-testid="task-id"]')).toContainText(/^task-1/);
    await expect(firstTask.locator('[data-testid="task-name"]')).toContainText('process_document');
    await expect(firstTask.locator('[data-testid="task-status"]')).toContainText('active');
    await expect(firstTask.locator('[data-testid="task-started-at"]')).not.toContainText(
      'Not started yet'
    );
    await expect(firstTask.locator('[data-testid="estimated-duration"]')).toContainText(
      /~\d+(\.\d+)?s/
    );
  });

  test('[P1] Admin clicks "View Pending Tasks" and sees pending task list - AC-5.4.3', async ({
    page,
  }) => {
    // GIVEN: Mock pending tasks
    const mockPendingTasks = createTaskList(3, true); // pending tasks

    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAllQueues()),
      });
    });

    await page.route(
      '**/api/v1/admin/queue/document_processing/tasks?type=pending',
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPendingTasks),
        });
      }
    );

    await queuePage.goto();

    // WHEN: Admin clicks "View Pending Tasks"
    await queuePage.getViewPendingTasksButton('document_processing').click();

    // THEN: Modal displays pending tasks
    await expect(page.getByRole('dialog')).toBeVisible();
    const taskRows = page.locator('[data-testid="task-row"]');
    await expect(taskRows).toHaveCount(3);

    // AND: Pending tasks show "Not started yet" for started_at
    const firstTask = taskRows.first();
    await expect(firstTask.locator('[data-testid="task-started-at"]')).toContainText(
      'Not started yet'
    );
    await expect(firstTask.locator('[data-testid="task-status"]')).toContainText('active');
  });

  test('[P1] Auto-refresh updates queue metrics every 10 seconds', async ({ page }) => {
    let requestCount = 0;

    // GIVEN: Mock API that changes metrics on each request
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      requestCount++;
      const queues = createAllQueues({
        documentProcessing: {
          pending_tasks: 10 + requestCount * 5,
          active_tasks: 2 + requestCount,
        },
      });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(queues),
      });
    });

    await queuePage.goto();

    // WHEN: Initial load completes
    const initialPendingCount = await queuePage.getPendingTasksCount('document_processing');
    expect(initialPendingCount).toBe(15); // 10 + 1*5

    // THEN: After 10 seconds, metrics update automatically
    await queuePage.waitForAutoRefresh();

    const updatedPendingCount = await queuePage.getPendingTasksCount('document_processing');
    expect(updatedPendingCount).toBe(20); // 10 + 2*5
    expect(updatedPendingCount).toBeGreaterThan(initialPendingCount);
  });

  test('[P0] Non-admin user navigates to /admin/queue and receives 403 redirect - AC-5.4.6', async ({
    page,
  }) => {
    // GIVEN: Logout admin and login as regular user
    await page.goto('/api/v1/auth/logout');
    await adminPage.loginAsRegularUser();

    // Mock 403 response for non-admin
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Admin access required' }),
      });
    });

    // WHEN: Regular user attempts to access /admin/queue
    await queuePage.goto();

    // THEN: User is redirected to dashboard with error message
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(
      page.getByText(/you do not have permission to access the admin panel/i)
    ).toBeVisible();
  });

  test('[P0] Queue status gracefully handles Celery broker unavailable - AC-5.4.5', async ({
    page,
  }) => {
    // GIVEN: Mock API returns unavailable queues (Celery broker offline)
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          createUnavailableQueue('document_processing'),
          createUnavailableQueue('embedding_generation'),
          createUnavailableQueue('export_generation'),
        ]),
      });
    });

    // WHEN: Admin views queue status page
    await queuePage.goto();

    // THEN: Page displays queues with "unavailable" status
    await expect(queuePage.getQueueCard('document_processing')).toBeVisible();
    const statusBadge = await queuePage.getQueueStatusBadge('document_processing');
    expect(statusBadge.toLowerCase()).toContain('unavailable');

    // AND: Error message is displayed
    await expect(queuePage.errorMessage).toBeVisible();
    await expect(queuePage.errorMessage).toContainText(
      /unable to connect to task queue|celery workers may be offline|redis is unavailable/i
    );

    // AND: Retry button is available
    await expect(queuePage.retryButton).toBeVisible();

    // WHEN: Admin clicks retry button
    let retryRequestMade = false;
    await page.route('**/api/v1/admin/queue/status', async (route) => {
      retryRequestMade = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAllQueues()),
      });
    });

    await queuePage.retryButton.click();

    // THEN: API request is retried and queues become available
    await page.waitForTimeout(500);
    expect(retryRequestMade).toBe(true);
    await expect(queuePage.errorMessage).not.toBeVisible();
  });
});
