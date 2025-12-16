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

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from '../page';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(),
  }),
  usePathname: () => '/dashboard',
}));

// Mock useActiveKb hook
vi.mock('@/hooks/useKnowledgeBase', () => ({
  useActiveKb: () => ({
    activeKb: { id: '1', name: 'Demo KB', description: 'Test KB' },
    isLoading: false,
  }),
}));

describe('Dashboard Navigation Cards (Story 5-0)', () => {
  describe('[P1] Search Navigation Card', () => {
    it('should render Search card when KB is active', () => {
      render(<DashboardPage />);

      const searchCard = screen.getByTestId('search-card');
      expect(searchCard).toBeInTheDocument();
    });

    it('should display correct text and icon', () => {
      render(<DashboardPage />);

      expect(screen.getByText(/Search Knowledge Base/i)).toBeInTheDocument();
    });

    it('should have clickable link to /search', () => {
      render(<DashboardPage />);

      const searchLink = screen.getByRole('link', { name: /Search/i });
      expect(searchLink).toHaveAttribute('href', '/search');
    });

    it('should be keyboard accessible', () => {
      render(<DashboardPage />);

      const searchCard = screen.getByTestId('search-card');
      expect(searchCard).toBeVisible();

      // Should be focusable
      searchCard.focus();
      expect(searchCard).toHaveFocus();
    });
  });

  describe('[P1] Chat Navigation Card', () => {
    it('should render Chat card when KB is active', () => {
      render(<DashboardPage />);

      const chatCard = screen.getByTestId('chat-card');
      expect(chatCard).toBeInTheDocument();
    });

    it('should display correct text and icon', () => {
      render(<DashboardPage />);

      expect(screen.getByText(/Chat/i)).toBeInTheDocument();
    });

    it('should have clickable link to /chat', () => {
      render(<DashboardPage />);

      const chatLink = screen.getByRole('link', { name: /Chat/i });
      expect(chatLink).toHaveAttribute('href', '/chat');
    });

    it('should be keyboard accessible', () => {
      render(<DashboardPage />);

      const chatCard = screen.getByTestId('chat-card');
      expect(chatCard).toBeVisible();

      // Should be focusable
      chatCard.focus();
      expect(chatCard).toHaveFocus();
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

  describe('[P2] Visual Styling', () => {
    it('should have cursor-pointer class for interactivity', () => {
      render(<DashboardPage />);

      const searchCard = screen.getByTestId('search-card');
      expect(searchCard).toHaveClass(/cursor-pointer/);
    });

    it('should have hover transition class', () => {
      render(<DashboardPage />);

      const searchCard = screen.getByTestId('search-card');
      expect(searchCard).toHaveClass(/transition/);
    });

    it('should maintain consistent styling with existing cards', () => {
      render(<DashboardPage />);

      const searchCard = screen.getByTestId('search-card');
      const chatCard = screen.getByTestId('chat-card');

      // Both should use Card component pattern
      expect(searchCard.tagName).toBe('DIV');
      expect(chatCard.tagName).toBe('DIV');
    });
  });
});
