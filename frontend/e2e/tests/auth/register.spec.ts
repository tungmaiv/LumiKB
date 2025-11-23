import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Registration Page', () => {
  test.beforeEach(async ({ registerPage }) => {
    await registerPage.goto();
  });

  test('displays registration form with all required fields', async ({ registerPage }) => {
    await expect(registerPage.nameInput).toBeVisible();
    await expect(registerPage.emailInput).toBeVisible();
    await expect(registerPage.passwordInput).toBeVisible();
    await expect(registerPage.confirmPasswordInput).toBeVisible();
    await expect(registerPage.submitButton).toBeVisible();
  });

  test('displays link to login page', async ({ registerPage }) => {
    await expect(registerPage.loginLink).toBeVisible();
  });

  test('shows validation error for empty name', async ({ registerPage }) => {
    await registerPage.emailInput.fill('test@example.com');
    await registerPage.passwordInput.fill('password123');
    await registerPage.confirmPasswordInput.fill('password123');
    await registerPage.submitButton.click();

    await expect(registerPage.page.getByText(/name.*required/i)).toBeVisible();
  });

  test('shows validation error for password mismatch', async ({ registerPage }) => {
    await registerPage.register(
      'Test User',
      'test@example.com',
      'password123',
      'differentpassword'
    );

    await expect(registerPage.page.getByText(/password.*match|passwords.*match/i)).toBeVisible();
  });

  test('shows validation error for short password', async ({ registerPage }) => {
    await registerPage.register('Test User', 'test@example.com', '123', '123');

    await expect(registerPage.page.getByText(/password.*characters|too short/i)).toBeVisible();
  });

  test('navigates to login page when clicking sign in link', async ({ registerPage }) => {
    await registerPage.loginLink.click();

    await expect(registerPage.page).toHaveURL(/.*login/);
  });
});

test.describe('Registration Flow', () => {
  test('successful registration redirects to login or dashboard', async ({ registerPage }) => {
    // Generate unique email to avoid conflicts
    const uniqueEmail = `test-${Date.now()}@example.com`;

    await registerPage.goto();
    await registerPage.register(
      'New Test User',
      uniqueEmail,
      'SecurePassword123!',
      'SecurePassword123!'
    );

    // Should redirect to login page or dashboard after successful registration
    await expect(registerPage.page).toHaveURL(/.*\/(login|dashboard)/);
  });

  test('shows error for existing email', async ({ registerPage }) => {
    await registerPage.goto();
    // Use a known existing email
    await registerPage.register(
      'Duplicate User',
      'test@example.com', // Assuming this exists
      'password123',
      'password123'
    );

    // Should show error about existing email
    await expect(
      registerPage.page.getByText(/already.*exists|email.*taken|registered/i)
    ).toBeVisible({ timeout: 10000 });
  });
});
