import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RegisterForm } from '../register-form';

// Mock the auth store
const mockRegister = vi.fn();
const mockClearError = vi.fn();

vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: () => ({
    register: mockRegister,
    isLoading: false,
    error: null,
    clearError: mockClearError,
  }),
}));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all required fields', () => {
    render(<RegisterForm />);

    expect(screen.getByLabelText(/^email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password(?!.*confirm)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  it('renders create account button', () => {
    render(<RegisterForm />);

    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('renders sign in link', () => {
    render(<RegisterForm />);

    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows password requirements helper text', () => {
    render(<RegisterForm />);

    expect(screen.getByText(/must be at least 8 characters/i)).toBeInTheDocument();
  });

  it('shows validation error for short password', async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const emailInput = screen.getByLabelText(/^email/i);
    const passwordInput = screen.getByLabelText(/^password(?!.*confirm)/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'short');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });
  });

  it('shows validation error when passwords do not match', async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const emailInput = screen.getByLabelText(/^email/i);
    const passwordInput = screen.getByLabelText(/^password(?!.*confirm)/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'differentpassword');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('calls register API on valid submission', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValueOnce(undefined);

    render(<RegisterForm />);

    const emailInput = screen.getByLabelText(/^email/i);
    const passwordInput = screen.getByLabelText(/^password(?!.*confirm)/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('redirects to login on successful registration', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValueOnce(undefined);

    render(<RegisterForm />);

    const emailInput = screen.getByLabelText(/^email/i);
    const passwordInput = screen.getByLabelText(/^password(?!.*confirm)/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });
});
