/**
 * AdminGuard Component Tests
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * Tests route-level access control for Administrator-level (3) pages:
 * - AC-7.11.17-18: Non-admin users cannot access /admin routes
 * - AC-7.11.1: Only Administrators can access admin routes
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AdminGuard } from '../admin-guard';

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
  useIsAdministrator: vi.fn(),
}));

import { useAuthStore, useIsAdministrator } from '@/lib/stores/auth-store';

const mockUseAuthStore = useAuthStore as unknown as ReturnType<typeof vi.fn>;
const mockUseIsAdministrator = useIsAdministrator as unknown as ReturnType<typeof vi.fn>;

describe('AdminGuard', () => {
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
      mockUseIsAdministrator.mockReturnValue(false);

      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText(/verifying access/i)).toBeInTheDocument();
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
    });

    it('[P1] does not redirect while loading', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: true,
        isAuthenticated: false,
      });
      mockUseIsAdministrator.mockReturnValue(false);

      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('Access Denied - Basic User (AC-7.11.17)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsAdministrator.mockReturnValue(false);
    });

    it('[P0] redirects basic user to dashboard', async () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('[P0] shows access denied message for basic user', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
      expect(screen.getByText(/administrator access.*level 3.*required/i)).toBeInTheDocument();
    });

    it('[P0] does not render admin content for basic user', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
    });

    it('[P1] displays shield alert icon', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      // ShieldAlert icon should be present (check for destructive color)
      const icon = document.querySelector('.text-destructive');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Access Denied - Operator (AC-7.11.18)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      // Operator is NOT an admin
      mockUseIsAdministrator.mockReturnValue(false);
    });

    it('[P0] redirects operator to dashboard', async () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('[P0] shows access denied message for operator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
    });

    it('[P0] does not render admin content for operator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
    });
  });

  describe('Access Granted - Administrator (AC-7.11.1)', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsAdministrator.mockReturnValue(true);
    });

    it('[P0] renders admin content for administrator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText('Admin Content')).toBeInTheDocument();
    });

    it('[P0] does not redirect administrator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(mockReplace).not.toHaveBeenCalled();
    });

    it('[P1] does not show access denied message for administrator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument();
    });

    it('[P1] does not show loading spinner for administrator', () => {
      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.queryByText(/verifying access/i)).not.toBeInTheDocument();
    });
  });

  describe('Unauthenticated User', () => {
    it('[P0] does not redirect when not authenticated (AuthGuard handles this)', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: false,
      });
      mockUseIsAdministrator.mockReturnValue(false);

      render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      // AdminGuard should not redirect - AuthGuard handles login redirect
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('Complex Children', () => {
    it('[P1] renders complex nested children for administrator', () => {
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsAdministrator.mockReturnValue(true);

      render(
        <AdminGuard>
          <div>
            <h1>Admin Dashboard</h1>
            <div>
              <h2>User Management</h2>
              <p>Total Users: 100</p>
            </div>
            <div>
              <h2>System Configuration</h2>
              <p>Active Settings: 25</p>
            </div>
          </div>
        </AdminGuard>
      );

      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('Total Users: 100')).toBeInTheDocument();
      expect(screen.getByText('System Configuration')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('[P2] handles rapid auth state changes gracefully', async () => {
      // Start loading
      mockUseAuthStore.mockReturnValue({
        isLoading: true,
        isAuthenticated: false,
      });
      mockUseIsAdministrator.mockReturnValue(false);

      const { rerender } = render(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText(/verifying access/i)).toBeInTheDocument();

      // Finish loading as admin
      mockUseAuthStore.mockReturnValue({
        isLoading: false,
        isAuthenticated: true,
      });
      mockUseIsAdministrator.mockReturnValue(true);

      rerender(
        <AdminGuard>
          <div>Admin Content</div>
        </AdminGuard>
      );

      expect(screen.getByText('Admin Content')).toBeInTheDocument();
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });
});
