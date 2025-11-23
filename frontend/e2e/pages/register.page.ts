import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class RegisterPage extends BasePage {
  // Locators
  readonly nameInput = this.page.getByLabel(/name/i);
  readonly emailInput = this.page.getByLabel(/email/i);
  readonly passwordInput = this.page.getByLabel(/^password$/i);
  readonly confirmPasswordInput = this.page.getByLabel(/confirm password/i);
  readonly submitButton = this.page.getByRole('button', {
    name: /create account/i,
  });
  readonly loginLink = this.page.getByRole('link', { name: /sign in/i });
  readonly errorMessage = this.page.getByRole('alert');

  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await super.goto('/register');
  }

  async register(name: string, email: string, password: string, confirmPassword?: string) {
    await this.nameInput.fill(name);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.confirmPasswordInput.fill(confirmPassword || password);
    await this.submitButton.click();
  }

  async expectError(message: string | RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToLogin() {
    await expect(this.page).toHaveURL(/.*login/);
  }
}
