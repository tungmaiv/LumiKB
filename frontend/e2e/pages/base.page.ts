import { Page, Locator } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Common navigation
  async goto(path: string = '/') {
    await this.page.goto(path);
  }

  // Common locators
  getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  // Common actions
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  // Toast/notification helpers (using Sonner)
  async getToastMessage(): Promise<string | null> {
    const toast = this.page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      return toast.textContent();
    }
    return null;
  }

  async waitForToast(message: string | RegExp) {
    const toast = this.page.locator('[data-sonner-toast]').first();
    await toast.waitFor({ state: 'visible' });
    if (typeof message === 'string') {
      await this.page.getByText(message).waitFor({ state: 'visible' });
    }
  }
}
