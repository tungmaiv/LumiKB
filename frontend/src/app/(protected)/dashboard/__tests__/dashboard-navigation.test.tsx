/**
 * Component Tests: Dashboard Navigation Cards (Story 5-0, AC2)
 * Status: Generated for Story 5-0
 * Generated: 2025-11-30
 *
 * Test Coverage:
 * - P1: Search navigation card renders and links correctly
 * - P1: Chat navigation card renders and links correctly
 * - P1: No "Coming in Epic" placeholders remain
 * - P2: Navigation cards have proper styling and hover states
 *
 * Knowledge Base References:
 * - test-quality.md: Component test isolation
 * - test-levels-framework.md: Component vs E2E test selection
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from '../page';

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock DashboardLayout
vi.mock('@/components/layout/dashboard-layout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  ),
}));

// Mock DocumentsPanel
vi.mock('@/components/documents', () => ({
  DocumentsPanel: () => <div data-testid="documents-panel">Documents Panel</div>,
}));

// Mock OnboardingWizard
vi.mock('@/components/onboarding/onboarding-wizard', () => ({
  OnboardingWizard: () => <div data-testid="onboarding-wizard">Onboarding</div>,
}));

// Mock useOnboarding hook
vi.mock('@/hooks/useOnboarding', () => ({
  useOnboarding: () => ({
    isOnboardingComplete: true,
    markOnboardingComplete: vi.fn(),
  }),
}));

// Mock auth store
vi.mock('@/lib/stores/auth-store', () => ({
  useUser: () => ({ email: 'test@example.com' }),
}));

// Variable to control KB state in tests
let mockActiveKb: {
  id: string;
  name: string;
  description: string;
  permission_level?: string;
} | null = null;
let mockKbs: Array<{ id: string; name: string }> = [];

// Mock kb store
vi.mock('@/lib/stores/kb-store', () => ({
  useActiveKb: () => mockActiveKb,
  useKbs: () => mockKbs,
}));

describe('Dashboard Navigation Cards (Story 5-0)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Set default state: active KB with some KBs
    mockActiveKb = { id: '1', name: 'Demo KB', description: 'Test KB', permission_level: 'READ' };
    mockKbs = [{ id: '1', name: 'Demo KB' }];
  });

  describe('[P1] Search Navigation Card', () => {
    it('should render Search card when KB is active', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Search')).toBeInTheDocument();
    });

    it('should display correct description text', () => {
      render(<DashboardPage />);

      expect(screen.getByText(/Find answers with citations/i)).toBeInTheDocument();
    });

    it('should have link to /search', () => {
      render(<DashboardPage />);

      const searchLink = screen.getByRole('link', { name: /Search/i });
      expect(searchLink).toHaveAttribute('href', '/search');
    });
  });

  describe('[P1] Chat Navigation Card', () => {
    it('should render Chat card when KB is active', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Chat')).toBeInTheDocument();
    });

    it('should display correct description text', () => {
      render(<DashboardPage />);

      expect(screen.getByText(/Ask AI questions/i)).toBeInTheDocument();
    });

    it('should have link to /chat', () => {
      render(<DashboardPage />);

      const chatLink = screen.getByRole('link', { name: /Chat/i });
      expect(chatLink).toHaveAttribute('href', '/chat');
    });
  });

  describe('[P1] No Epic Placeholders', () => {
    it('should NOT display "Coming in Epic 3" placeholder', () => {
      render(<DashboardPage />);

      const epic3Placeholder = screen.queryByText(/Coming in Epic 3/i);
      expect(epic3Placeholder).not.toBeInTheDocument();
    });

    it('should NOT display "Coming in Epic 4" placeholder', () => {
      render(<DashboardPage />);

      const epic4Placeholder = screen.queryByText(/Coming in Epic 4/i);
      expect(epic4Placeholder).not.toBeInTheDocument();
    });
  });

  describe('[P1] Active KB Display', () => {
    it('should display active KB name', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Demo KB')).toBeInTheDocument();
    });

    it('should display active KB description', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Test KB')).toBeInTheDocument();
    });

    it('should show DocumentsPanel when KB is active', () => {
      render(<DashboardPage />);

      expect(screen.getByTestId('documents-panel')).toBeInTheDocument();
    });
  });

  describe('[P2] No Active KB State', () => {
    beforeEach(() => {
      mockActiveKb = null;
      mockKbs = []; // No KBs
    });

    it('should show Getting Started when no KBs exist', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Getting Started')).toBeInTheDocument();
    });

    it('should show Search Knowledge Base card in no-KB state', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Search Knowledge Base')).toBeInTheDocument();
    });

    it('should show welcome message with user name', () => {
      render(<DashboardPage />);

      expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
    });
  });

  describe('[P2] KBs exist but none selected', () => {
    beforeEach(() => {
      mockActiveKb = null;
      mockKbs = [{ id: '1', name: 'Demo KB' }]; // KBs exist but none selected
    });

    it('should prompt to select a KB', () => {
      render(<DashboardPage />);

      expect(screen.getByText('Select a Knowledge Base')).toBeInTheDocument();
    });

    it('should not show navigation cards when no KB selected', () => {
      render(<DashboardPage />);

      // No Search/Chat cards in this state
      expect(screen.queryByText('Search')).not.toBeInTheDocument();
      expect(screen.queryByText('Chat')).not.toBeInTheDocument();
    });
  });
});
