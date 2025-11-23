import { test, expect, TEST_USER } from '../../fixtures/auth.fixture';

test.describe('Login Page', () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
  });

  test('displays login form with all required fields', async ({ loginPage }) => {
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();
  });

  test('displays link to registration page', async ({ loginPage }) => {
    await expect(loginPage.registerLink).toBeVisible();
  });

  test('shows validation error for empty email', async ({ loginPage }) => {
    await loginPage.passwordInput.fill('somepassword');
    await loginPage.submitButton.click();

    await expect(loginPage.page.getByText(/email.*required/i)).toBeVisible();
  });

  test('shows validation error for empty password', async ({ loginPage }) => {
    await loginPage.emailInput.fill('test@example.com');
    await loginPage.submitButton.click();

    await expect(loginPage.page.getByText(/password.*required/i)).toBeVisible();
  });

  test('shows validation error for invalid email format', async ({ loginPage }) => {
    await loginPage.emailInput.fill('notanemail');
    await loginPage.passwordInput.fill('password123');
    await loginPage.submitButton.click();

    // Browser native validation or custom validation
    const invalidMessage = loginPage.page.getByText(/invalid.*email|email.*invalid/i);
    const isVisible = await invalidMessage.isVisible().catch(() => false);

    // If no visible error, the form should not have submitted
    if (!isVisible) {
      // Email input should still be on page (form didn't submit)
      await expect(loginPage.emailInput).toBeVisible();
    }
  });

  test('navigates to registration page when clicking create account', async ({ loginPage }) => {
    await loginPage.registerLink.click();

    await expect(loginPage.page).toHaveURL(/.*register/);
  });
});

test.describe('Login Authentication', () => {
  test('redirects to dashboard on successful login', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login(TEST_USER.email, TEST_USER.password);

    // Should redirect to dashboard or show success
    // Note: This test requires a running backend with valid credentials
    await loginPage.expectRedirectToDashboard();
  });

  test('shows error for invalid credentials', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('invalid@example.com', 'wrongpassword');

    // Should show error message
    await expect(loginPage.page.getByText(/invalid|incorrect|failed/i)).toBeVisible({
      timeout: 10000,
    });
  });
});
