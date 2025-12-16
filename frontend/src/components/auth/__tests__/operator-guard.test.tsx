/**
 * OperatorGuard Component Tests
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * Tests route-level access control for Operator-level (2+) pages:
 * - AC-7.11.16: Non-operator users cannot access /operations routes
 * - AC-7.11.2: Operators can access operations routes
 * - AC-7.11.1: Administrators can access operations routes (cumulative)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { OperatorGuard } from '../operator-guard';

// Mock next/navigation
const mockReplace = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: vi.fn(),
    back: vi.fn(),
  }),
}));

// Mock auth store
vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: vi.fn(),
  useIsOperator: vi.fn(),
}));

import { useAuthStore, useIsOperator } from '@/lib/stores/auth-store';

const mockUseAuthStore = useAuthStore as unknown as ReturnType<typeof vi.fn>;
const mockUseIsOperator = useIsOperator as unknown as ReturnType<typeof vi.fn>;

describe('OperatorGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReplace.mockClear();
  });

  describe('Loading State', () => {
    it('[P0] shows loading spinner while auth is checking', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: true,
        isAuthenticated: false,
      });
      mockUseIsOperator.mockReturnValue(false);

      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.getByText(/verifying access/i)).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('[P1] does not redirect while loading', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: true,
        isAuthenticated: false,
      });
      mockUseIsOperator.mockReturnValue(false);

      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('Access Denied - Basic User (AC-7.11.16)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsOperator.mockReturnValue(false);
    });

    it('[P0] redirects basic user to dashboard', async () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('[P0] shows access denied message for basic user', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
      expect(screen.getByText(/operator access.*level 2\+.*required/i)).toBeInTheDocument();
    });

    it('[P0] does not render protected content for basic user', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('[P1] displays shield alert icon', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      // ShieldAlert icon should be present (check for destructive color)
      const icon = document.querySelector('.text-destructive');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Access Granted - Operator (AC-7.11.2)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsOperator.mockReturnValue(true);
    });

    it('[P0] renders protected content for operator', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('[P0] does not redirect operator', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(mockReplace).not.toHaveBeenCalled();
    });

    it('[P1] does not show access denied message for operator', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument();
    });
  });

  describe('Access Granted - Administrator (AC-7.11.1 cumulative)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      // Administrator is also an operator (cumulative permissions)
      mockUseIsOperator.mockReturnValue(true);
    });

    it('[P0] renders protected content for administrator', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('[P0] does not redirect administrator', () => {
      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('Unauthenticated User', () => {
    it('[P0] does not redirect when not authenticated (AuthGuard handles this)', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: false,
      });
      mockUseIsOperator.mockReturnValue(false);

      render(
        <OperatorGuard>
          <div>Protected Content</div>
        </OperatorGuard>
      );

      // OperatorGuard should not redirect - AuthGuard handles login redirect
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('Complex Children', () => {
    it('[P1] renders complex nested children for operator', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsOperator.mockReturnValue(true);

      render(
        <OperatorGuard>
          <div>
            <h1>Operations Dashboard</h1>
            <div>
              <p>Queue Status</p>
              <p>Active Tasks: 5</p>
            </div>
          </div>
        </OperatorGuard>
      );

      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Queue Status')).toBeInTheDocument();
      expect(screen.getByText('Active Tasks: 5')).toBeInTheDocument();
    });
  });
});
