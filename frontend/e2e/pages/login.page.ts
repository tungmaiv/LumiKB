import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class LoginPage extends BasePage {
  // Locators
  readonly emailInput = this.page.getByLabel(/email/i);
  readonly passwordInput = this.page.getByLabel(/password/i);
  readonly submitButton = this.page.getByRole('button', { name: /sign in/i });
  readonly registerLink = this.page.getByRole('link', {
    name: /create account/i,
  });
  readonly errorMessage = this.page.getByRole('alert');

  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await super.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string | RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToDashboard() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }

  async expectOnLoginPage() {
    await expect(this.emailInput).toBeVisible();
    await expect(this.passwordInput).toBeVisible();
  }
}
