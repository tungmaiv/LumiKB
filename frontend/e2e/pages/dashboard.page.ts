import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class DashboardPage extends BasePage {
  // Locators
  readonly welcomeMessage = this.page.getByRole('heading', {
    name: /welcome|dashboard/i,
  });
  readonly searchInput = this.page.getByPlaceholder(/search/i);
  readonly uploadButton = this.page.getByRole('button', { name: /upload/i });
  readonly userMenu = this.page.getByTestId('user-menu');
  readonly sidebar = this.page.getByTestId('sidebar');

  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await super.goto('/dashboard');
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    await this.openUserMenu();
    await this.page.getByRole('menuitem', { name: /logout|sign out/i }).click();
  }

  async expectDashboardVisible() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }

  async navigateTo(section: 'documents' | 'settings' | 'profile') {
    const linkName = {
      documents: /documents/i,
      settings: /settings/i,
      profile: /profile/i,
    };
    await this.page.getByRole('link', { name: linkName[section] }).click();
  }
}
