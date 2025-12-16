/**
 * MobileNav Component Tests (Story 5-17, Story 7-11)
 *
 * Test Coverage:
 * - Core navigation links (dashboard, search, chat)
 * - RBAC-based menu visibility (Operations, Admin)
 * - Active route highlighting
 * - Callback props (onSidebarOpen, onCitationsOpen)
 * - Accessibility (roles, aria-labels, aria-expanded)
 *
 * Story 7.11: Updated to use permission levels instead of is_superuser
 * AC-7.11.1: Administrators see both Operations and Admin menus
 * AC-7.11.2: Operators see only Operations menu
 * AC-7.11.3: Basic Users see neither menu
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MobileNav } from '../mobile-nav';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  usePathname: vi.fn(),
}));

// Mock auth store - now using permission level hooks
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

/**
 * Helper to set up permission level mocks
 */
function setupPermissions(level: 'user' | 'operator' | 'administrator') {
  switch (level) {
    case 'administrator':
      mockUseIsOperator.mockReturnValue(true); // Administrators are also operators
      mockUseIsAdministrator.mockReturnValue(true);
      break;
    case 'operator':
      mockUseIsOperator.mockReturnValue(true);
      mockUseIsAdministrator.mockReturnValue(false);
      break;
    case 'user':
    default:
      mockUseIsOperator.mockReturnValue(false);
      mockUseIsAdministrator.mockReturnValue(false);
      break;
  }
}

describe('MobileNav', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue('/dashboard');
    setupPermissions('user'); // Default to basic user
  });

  describe('Core Navigation Links (AC-5.17.5)', () => {
    it('renders core navigation links for authenticated user', () => {
      render(<MobileNav />);

      // The mobile nav uses "Home" label for dashboard
      expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /search/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /chat/i })).toBeInTheDocument();
    });

    it('core links have correct href attributes', () => {
      render(<MobileNav />);

      expect(screen.getByRole('link', { name: /home/i })).toHaveAttribute('href', '/dashboard');
      expect(screen.getByRole('link', { name: /search/i })).toHaveAttribute('href', '/search');
      expect(screen.getByRole('link', { name: /chat/i })).toHaveAttribute('href', '/chat');
    });

    it('shows KBs button to open sidebar', () => {
      render(<MobileNav />);

      expect(screen.getByRole('button', { name: /open knowledge bases/i })).toBeInTheDocument();
    });

    it('shows Citations button for basic users (no permission menus)', () => {
      setupPermissions('user');

      render(<MobileNav />);

      expect(screen.getByRole('button', { name: /open citations/i })).toBeInTheDocument();
    });

    it('hides Citations button for operators/admins (permission menus take space)', () => {
      setupPermissions('operator');

      render(<MobileNav />);

      expect(screen.queryByRole('button', { name: /open citations/i })).not.toBeInTheDocument();
    });
  });

  describe('RBAC - Basic User (AC-7.11.3)', () => {
    beforeEach(() => {
      setupPermissions('user');
    });

    it('hides Operations menu for basic user', () => {
      render(<MobileNav />);

      expect(screen.queryByRole('button', { name: /operations menu/i })).not.toBeInTheDocument();
    });

    it('hides Admin menu for basic user', () => {
      render(<MobileNav />);

      expect(screen.queryByRole('button', { name: /admin menu/i })).not.toBeInTheDocument();
    });
  });

  describe('RBAC - Operator (AC-7.11.2)', () => {
    beforeEach(() => {
      setupPermissions('operator');
    });

    it('shows Operations toggle button for operators', () => {
      render(<MobileNav />);

      expect(screen.getByRole('button', { name: /open operations menu/i })).toBeInTheDocument();
    });

    it('hides Admin menu for operators', () => {
      render(<MobileNav />);

      expect(screen.queryByRole('button', { name: /admin menu/i })).not.toBeInTheDocument();
    });

    it('expands Operations section when toggle button clicked', async () => {
      const user = userEvent.setup();

      render(<MobileNav />);

      // Initially operations links should not be visible
      expect(screen.queryByRole('link', { name: /^overview$/i })).not.toBeInTheDocument();

      // Click toggle button
      await user.click(screen.getByRole('button', { name: /open operations menu/i }));

      // Operations links should now be visible
      await waitFor(() => {
        expect(screen.getByRole('link', { name: /^overview$/i })).toBeInTheDocument();
      });
      expect(screen.getByRole('link', { name: /^audit$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /^queue$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /kb stats/i })).toBeInTheDocument();
    });
  });

  describe('RBAC - Administrator (AC-7.11.1)', () => {
    beforeEach(() => {
      setupPermissions('administrator');
    });

    it('shows both Operations and Admin toggle buttons for administrators', () => {
      render(<MobileNav />);

      expect(screen.getByRole('button', { name: /open operations menu/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /open admin menu/i })).toBeInTheDocument();
    });

    it('expands Admin section when toggle button clicked', async () => {
      const user = userEvent.setup();

      render(<MobileNav />);

      // Initially admin links should not be visible
      expect(screen.queryByRole('link', { name: /^users$/i })).not.toBeInTheDocument();

      // Click admin toggle button
      await user.click(screen.getByRole('button', { name: /open admin menu/i }));

      // Admin links should now be visible
      await waitFor(() => {
        expect(screen.getByRole('link', { name: /^overview$/i })).toBeInTheDocument();
      });
      expect(screen.getByRole('link', { name: /^users$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /^groups$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /kb perms/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /^config$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /^models$/i })).toBeInTheDocument();
    });

    it('collapses Admin section when toggle button clicked again', async () => {
      const user = userEvent.setup();

      render(<MobileNav />);

      // Open admin section
      await user.click(screen.getByRole('button', { name: /open admin menu/i }));
      await waitFor(() => {
        expect(screen.getByRole('link', { name: /^users$/i })).toBeInTheDocument();
      });

      // Close admin section (button label changes to "close admin menu")
      await user.click(screen.getByRole('button', { name: /close admin menu/i }));
      await waitFor(() => {
        expect(screen.queryByRole('link', { name: /^users$/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Active Route Highlighting', () => {
    it('highlights home link when on /dashboard', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      render(<MobileNav />);

      const homeLink = screen.getByRole('link', { name: /home/i });
      expect(homeLink).toHaveAttribute('aria-current', 'page');
    });

    it('highlights search link when active', () => {
      mockUsePathname.mockReturnValue('/search');

      render(<MobileNav />);

      const searchLink = screen.getByRole('link', { name: /search/i });
      expect(searchLink).toHaveAttribute('aria-current', 'page');
    });

    it('highlights chat link when active', () => {
      mockUsePathname.mockReturnValue('/chat');

      render(<MobileNav />);

      const chatLink = screen.getByRole('link', { name: /chat/i });
      expect(chatLink).toHaveAttribute('aria-current', 'page');
    });
  });

  describe('Accessibility (AC-5.17.6)', () => {
    it('has navigation role and aria-label', () => {
      render(<MobileNav />);

      const nav = screen.getByRole('navigation', { name: /mobile navigation/i });
      expect(nav).toBeInTheDocument();
    });

    it('all links have aria-label attributes', () => {
      render(<MobileNav />);

      const allLinks = screen.getAllByRole('link');
      allLinks.forEach((link) => {
        expect(link).toHaveAttribute('aria-label');
      });
    });

    it('Operations toggle button has aria-expanded attribute', async () => {
      setupPermissions('operator');
      const user = userEvent.setup();

      render(<MobileNav />);

      const toggleButton = screen.getByRole('button', { name: /open operations menu/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

      await user.click(toggleButton);
      // After click, aria-expanded becomes true
      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close operations menu/i });
        expect(closeButton).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('Admin toggle button has aria-expanded attribute', async () => {
      setupPermissions('administrator');
      const user = userEvent.setup();

      render(<MobileNav />);

      const toggleButton = screen.getByRole('button', { name: /open admin menu/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

      await user.click(toggleButton);
      // After click, button label changes and aria-expanded becomes true
      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close admin menu/i });
        expect(closeButton).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('Operations section has aria-label when expanded', async () => {
      setupPermissions('operator');
      const user = userEvent.setup();

      render(<MobileNav />);

      await user.click(screen.getByRole('button', { name: /open operations menu/i }));

      await waitFor(() => {
        const opsRegion = screen.getByRole('region', { name: /operations navigation/i });
        expect(opsRegion).toBeInTheDocument();
      });
    });

    it('Admin section has aria-label when expanded', async () => {
      setupPermissions('administrator');
      const user = userEvent.setup();

      render(<MobileNav />);

      await user.click(screen.getByRole('button', { name: /open admin menu/i }));

      await waitFor(() => {
        const adminRegion = screen.getByRole('region', { name: /admin navigation/i });
        expect(adminRegion).toBeInTheDocument();
      });
    });
  });

  describe('Callback Props', () => {
    it('calls onSidebarOpen when KBs button clicked', async () => {
      const handleSidebarOpen = vi.fn();
      const user = userEvent.setup();

      render(<MobileNav onSidebarOpen={handleSidebarOpen} />);

      await user.click(screen.getByRole('button', { name: /open knowledge bases/i }));
      expect(handleSidebarOpen).toHaveBeenCalledTimes(1);
    });

    it('calls onCitationsOpen when Citations button clicked', async () => {
      setupPermissions('user'); // Citations only shown for basic users
      const handleCitationsOpen = vi.fn();
      const user = userEvent.setup();

      render(<MobileNav onCitationsOpen={handleCitationsOpen} />);

      await user.click(screen.getByRole('button', { name: /open citations/i }));
      expect(handleCitationsOpen).toHaveBeenCalledTimes(1);
    });
  });
});
