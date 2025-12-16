/**
 * MainNav Component Tests
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * Tests navigation menu based on permission levels:
 * - AC-7.11.1: Administrators see both Operations and Admin dropdowns
 * - AC-7.11.2: Operators see only Operations dropdown
 * - AC-7.11.3: Basic Users see neither dropdown (only core links)
 * - AC-7.11.4: Operations dropdown contains audit, queue, kb-stats
 * - AC-7.11.5: Admin dropdown contains users, groups, kb-permissions, config, models
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MainNav } from '../main-nav';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

// Mock auth store hooks
vi.mock('@/lib/stores/auth-store', () => ({
  useIsOperator: vi.fn(),
  useIsAdministrator: vi.fn(),
}));

// Import mocks for configuration
import { usePathname } from 'next/navigation';
import { useIsOperator, useIsAdministrator } from '@/lib/stores/auth-store';

const mockUsePathname = usePathname as ReturnType<typeof vi.fn>;
const mockUseIsOperator = useIsOperator as ReturnType<typeof vi.fn>;
const mockUseIsAdministrator = useIsAdministrator as ReturnType<typeof vi.fn>;

describe('MainNav', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue('/dashboard');
    // Default: regular user (neither operator nor admin)
    mockUseIsOperator.mockReturnValue(false);
    mockUseIsAdministrator.mockReturnValue(false);
  });

  describe('Core Navigation Links', () => {
    it('[P0] renders all core navigation links for authenticated user', () => {
      render(<MainNav />);

      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /search/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /chat/i })).toBeInTheDocument();
    });

    it('[P0] core links have correct href attributes', () => {
      render(<MainNav />);

      expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/dashboard');
      expect(screen.getByRole('link', { name: /search/i })).toHaveAttribute('href', '/search');
      expect(screen.getByRole('link', { name: /chat/i })).toHaveAttribute('href', '/chat');
    });
  });

  describe('RBAC - Basic User (AC-7.11.3)', () => {
    it('[P0] hides Operations dropdown for basic user', () => {
      mockUseIsOperator.mockReturnValue(false);
      mockUseIsAdministrator.mockReturnValue(false);

      render(<MainNav />);

      expect(screen.queryByRole('button', { name: /operations menu/i })).not.toBeInTheDocument();
    });

    it('[P0] hides Admin dropdown for basic user', () => {
      mockUseIsOperator.mockReturnValue(false);
      mockUseIsAdministrator.mockReturnValue(false);

      render(<MainNav />);

      expect(screen.queryByRole('button', { name: /admin menu/i })).not.toBeInTheDocument();
    });
  });

  describe('RBAC - Operator (AC-7.11.2, AC-7.11.4)', () => {
    beforeEach(() => {
      mockUseIsOperator.mockReturnValue(true);
      mockUseIsAdministrator.mockReturnValue(false);
    });

    it('[P0] shows Operations dropdown for operator', () => {
      render(<MainNav />);

      expect(screen.getByRole('button', { name: /operations menu/i })).toBeInTheDocument();
    });

    it('[P0] hides Admin dropdown for operator', () => {
      render(<MainNav />);

      expect(screen.queryByRole('button', { name: /admin menu/i })).not.toBeInTheDocument();
    });

    it('[P0] Operations dropdown contains correct links (AC-7.11.4)', async () => {
      const user = userEvent.setup();
      render(<MainNav />);

      // Open Operations dropdown
      const operationsButton = screen.getByRole('button', { name: /operations menu/i });
      await user.click(operationsButton);

      // Verify all operations links are present with correct hrefs
      await waitFor(() => {
        expect(screen.getByRole('menuitem', { name: /operations dashboard/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /audit logs/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /processing queue/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /kb statistics/i })).toBeInTheDocument();
      });
    });

    it('[P1] Operations links have correct href attributes', async () => {
      const user = userEvent.setup();
      render(<MainNav />);

      const operationsButton = screen.getByRole('button', { name: /operations menu/i });
      await user.click(operationsButton);

      await waitFor(() => {
        const menu = screen.getByRole('menu');
        // DropdownMenuItem wraps links as menuitems, not links
        const menuItems = within(menu).getAllByRole('menuitem');

        // Find the actual anchor elements inside menu items
        const links = menuItems.map(item => item.closest('a') || item.querySelector('a') || item);

        expect(links[0]).toHaveAttribute('href', '/operations');
        expect(links[1]).toHaveAttribute('href', '/operations/audit');
        expect(links[2]).toHaveAttribute('href', '/operations/queue');
        expect(links[3]).toHaveAttribute('href', '/operations/kb-stats');
      });
    });
  });

  describe('RBAC - Administrator (AC-7.11.1, AC-7.11.5)', () => {
    beforeEach(() => {
      // Admin is also an operator (cumulative permissions)
      mockUseIsOperator.mockReturnValue(true);
      mockUseIsAdministrator.mockReturnValue(true);
    });

    it('[P0] shows both Operations and Admin dropdowns for administrator (AC-7.11.1)', () => {
      render(<MainNav />);

      expect(screen.getByRole('button', { name: /operations menu/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /admin menu/i })).toBeInTheDocument();
    });

    it('[P0] Admin dropdown contains correct links (AC-7.11.5)', async () => {
      const user = userEvent.setup();
      render(<MainNav />);

      // Open Admin dropdown
      const adminButton = screen.getByRole('button', { name: /admin menu/i });
      await user.click(adminButton);

      // Verify all admin links are present
      await waitFor(() => {
        expect(screen.getByRole('menuitem', { name: /admin dashboard/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /users/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /groups/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /kb permissions/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /system config/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /model registry/i })).toBeInTheDocument();
      });
    });

    it('[P1] Admin links have correct href attributes', async () => {
      const user = userEvent.setup();
      render(<MainNav />);

      const adminButton = screen.getByRole('button', { name: /admin menu/i });
      await user.click(adminButton);

      await waitFor(() => {
        const menu = screen.getByRole('menu');
        // DropdownMenuItem wraps links as menuitems, not links
        const menuItems = within(menu).getAllByRole('menuitem');

        // Find the actual anchor elements inside menu items
        const links = menuItems.map(item => item.closest('a') || item.querySelector('a') || item);

        expect(links[0]).toHaveAttribute('href', '/admin');
        expect(links[1]).toHaveAttribute('href', '/admin/users');
        expect(links[2]).toHaveAttribute('href', '/admin/groups');
        expect(links[3]).toHaveAttribute('href', '/admin/kb-permissions');
        expect(links[4]).toHaveAttribute('href', '/admin/config');
        expect(links[5]).toHaveAttribute('href', '/admin/models');
      });
    });
  });

  describe('Active Route Highlighting', () => {
    it('[P1] highlights dashboard link when on /dashboard', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      render(<MainNav />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('[P1] highlights search link when on /search', () => {
      mockUsePathname.mockReturnValue('/search');

      render(<MainNav />);

      const searchLink = screen.getByRole('link', { name: /search/i });
      expect(searchLink).toHaveAttribute('aria-current', 'page');
    });

    it('[P1] highlights chat link when on /chat', () => {
      mockUsePathname.mockReturnValue('/chat');

      render(<MainNav />);

      const chatLink = screen.getByRole('link', { name: /chat/i });
      expect(chatLink).toHaveAttribute('aria-current', 'page');
    });

    it('[P1] highlights Operations button when on /operations route', () => {
      mockUsePathname.mockReturnValue('/operations/audit');
      mockUseIsOperator.mockReturnValue(true);

      render(<MainNav />);

      const operationsButton = screen.getByRole('button', { name: /operations menu/i });
      // Button should have accent styling when on operations route
      expect(operationsButton).toHaveClass('bg-accent');
    });

    it('[P1] highlights Admin button when on /admin route', () => {
      mockUsePathname.mockReturnValue('/admin/users');
      mockUseIsOperator.mockReturnValue(true);
      mockUseIsAdministrator.mockReturnValue(true);

      render(<MainNav />);

      const adminButton = screen.getByRole('button', { name: /admin menu/i });
      // Button should have accent styling when on admin route
      expect(adminButton).toHaveClass('bg-accent');
    });

    it('[P1] does not highlight non-active links', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      render(<MainNav />);

      const searchLink = screen.getByRole('link', { name: /search/i });
      const chatLink = screen.getByRole('link', { name: /chat/i });
      expect(searchLink).not.toHaveAttribute('aria-current');
      expect(chatLink).not.toHaveAttribute('aria-current');
    });
  });

  describe('Accessibility', () => {
    it('[P1] has proper navigation role and aria-label', () => {
      render(<MainNav />);

      const nav = screen.getByRole('navigation', { name: /main navigation/i });
      expect(nav).toBeInTheDocument();
    });

    it('[P1] uses semantic list structure for core links', () => {
      render(<MainNav />);

      const lists = screen.getAllByRole('list');
      expect(lists.length).toBeGreaterThanOrEqual(1);
    });

    it('[P2] dropdown buttons have aria-label attributes', () => {
      mockUseIsOperator.mockReturnValue(true);
      mockUseIsAdministrator.mockReturnValue(true);

      render(<MainNav />);

      expect(screen.getByRole('button', { name: /operations menu/i })).toHaveAttribute('aria-label');
      expect(screen.getByRole('button', { name: /admin menu/i })).toHaveAttribute('aria-label');
    });
  });

  describe('Custom className', () => {
    it('[P2] accepts and applies custom className', () => {
      const { container } = render(<MainNav className="custom-class" />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('custom-class');
    });
  });
});
