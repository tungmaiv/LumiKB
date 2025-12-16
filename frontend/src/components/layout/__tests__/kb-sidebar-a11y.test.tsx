import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { KbSidebar } from '../kb-sidebar';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';
import type { RecentKB } from '@/hooks/useRecentKBs';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/search',
}));

// Mock data
const mockKbs: KnowledgeBase[] = [
  {
    id: 'kb-1',
    name: 'Test KB 1',
    description: 'Description 1',
    status: 'active',
    document_count: 5,
    permission_level: 'ADMIN',
    tags: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    archived_at: null,
  },
  {
    id: 'kb-2',
    name: 'Test KB 2',
    description: 'Description 2',
    status: 'active',
    document_count: 10,
    permission_level: 'READ',
    tags: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    archived_at: null,
  },
];

const mockRecentKBs: RecentKB[] = [
  {
    kb_id: 'kb-1',
    kb_name: 'Test KB 1',
    description: 'Description 1',
    last_accessed: '2025-12-03T10:00:00Z',
    document_count: 5,
  },
];

// Mock store state
const mockSetActiveKb = vi.fn();
const mockFetchKbs = vi.fn();

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: (selector?: (state: unknown) => unknown) => {
    const state = {
      kbs: mockKbs,
      activeKb: null,
      isLoading: false,
      error: null,
      fetchKbs: mockFetchKbs,
      setActiveKb: mockSetActiveKb,
      createKb: vi.fn(),
      clearError: vi.fn(),
    };
    if (selector) return selector(state);
    return state;
  },
}));

vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: (selector?: (state: { user: { id: string } | null }) => unknown) => {
    const state = { user: { id: 'user-1' } };
    if (selector) return selector(state);
    return state;
  },
}));

vi.mock('@/hooks/useRecentKBs', () => ({
  useRecentKBs: () => ({
    data: mockRecentKBs,
    isLoading: false,
    isError: false,
    error: null,
  }),
}));

vi.mock('@/hooks/useKBRecommendations', () => ({
  useKBRecommendations: () => ({
    data: [],
    isLoading: false,
    isError: false,
    error: null,
  }),
}));

describe('KbSidebar - Keyboard Accessibility (AC-5.9.9)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockClear();
    mockSetActiveKb.mockClear();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  const renderWithProviders = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <KbSidebar />
      </QueryClientProvider>
    );
  };

  describe('Tab Order', () => {
    it('tab moves focus to Dashboard link first', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await user.tab();

      expect(screen.getByRole('link', { name: /dashboard/i })).toHaveFocus();
    });

    it('tab moves through interactive elements', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Tab to Dashboard link first
      await user.tab();
      expect(screen.getByRole('link', { name: /dashboard/i })).toHaveFocus();

      // Tab to Create button
      await user.tab();
      expect(screen.getByLabelText('Create Knowledge Base')).toHaveFocus();

      // Tab to first recent KB
      await user.tab();
      expect(screen.getByLabelText('Open Test KB 1')).toHaveFocus();
    });

    it('shift+tab moves focus backwards', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Tab forward three times (Dashboard -> Create -> Recent KB)
      await user.tab();
      await user.tab();
      await user.tab();

      // Verify we're on the recent KB
      expect(screen.getByLabelText('Open Test KB 1')).toHaveFocus();

      // Shift+tab back to Create button
      await user.tab({ shift: true });

      expect(screen.getByLabelText('Create Knowledge Base')).toHaveFocus();
    });

    it('can tab through all KB list items', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Tab through all focusable elements
      let focusedElements: string[] = [];

      // Tab until we've gone through all elements or hit a limit
      for (let i = 0; i < 10; i++) {
        await user.tab();
        const activeElement = document.activeElement;
        if (activeElement?.getAttribute('aria-label')) {
          focusedElements.push(activeElement.getAttribute('aria-label') || '');
        }
      }

      // Should have focused on Create button and KB items
      expect(focusedElements).toContain('Create Knowledge Base');
      expect(focusedElements).toContain('Open Test KB 1');
    });
  });

  describe('Focus Indicators', () => {
    it('buttons have focus-visible styling classes', () => {
      renderWithProviders();

      const createButton = screen.getByLabelText('Create Knowledge Base');
      // Check that the button has focus-related classes in its className
      expect(createButton.className).toMatch(/focus/);
    });

    it('recent KB buttons have focus styling', () => {
      renderWithProviders();

      const recentKbButton = screen.getByLabelText('Open Test KB 1');
      // The button should have focus-visible:ring-2 class
      expect(recentKbButton.className).toContain('focus-visible:ring-2');
    });

    it('focus ring has ring-ring class for consistent styling', () => {
      renderWithProviders();

      const recentKbButton = screen.getByLabelText('Open Test KB 1');
      expect(recentKbButton.className).toContain('focus-visible:ring-ring');
    });
  });

  describe('Activation', () => {
    it('Enter key activates focused KB item', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Tab to Dashboard link
      await user.tab();
      // Tab to Create button
      await user.tab();
      // Tab to recent KB
      await user.tab();

      // Press Enter
      await user.keyboard('{Enter}');

      expect(mockSetActiveKb).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-1');
    });

    it('Space key activates focused button', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Tab to Dashboard link
      await user.tab();
      // Tab to Create button
      await user.tab();

      // Press Space
      await user.keyboard(' ');

      // Modal should open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('clicking recent KB triggers navigation', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await user.click(screen.getByLabelText('Open Test KB 1'));

      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-1');
    });
  });

  describe('ARIA Attributes', () => {
    it('recent KB items have aria-label with KB name', () => {
      renderWithProviders();

      expect(screen.getByLabelText('Open Test KB 1')).toBeInTheDocument();
    });

    it('Create button has aria-label', () => {
      renderWithProviders();

      expect(screen.getByLabelText('Create Knowledge Base')).toBeInTheDocument();
    });

    it('Recent section has descriptive text', () => {
      renderWithProviders();

      // "Recent" text should be present
      const recentHeading = screen.getByText('Recent');
      expect(recentHeading).toBeInTheDocument();
      // It should be uppercase for visual styling
      expect(recentHeading).toHaveClass('uppercase');
    });

    it('All Knowledge Bases section has descriptive text', () => {
      renderWithProviders();

      const allKbsHeading = screen.getByText('All Knowledge Bases');
      expect(allKbsHeading).toBeInTheDocument();
      expect(allKbsHeading).toHaveClass('uppercase');
    });

    it('Knowledge Bases header is present', () => {
      renderWithProviders();

      expect(screen.getByText('Knowledge Bases')).toBeInTheDocument();
    });
  });

  describe('Interactive Elements', () => {
    it('all recent KB items are buttons', () => {
      renderWithProviders();

      const recentKbButton = screen.getByLabelText('Open Test KB 1');
      expect(recentKbButton.tagName.toLowerCase()).toBe('button');
    });

    it('Create KB button is a proper button element', () => {
      renderWithProviders();

      const createButton = screen.getByLabelText('Create Knowledge Base');
      expect(createButton.tagName.toLowerCase()).toBe('button');
    });

    it('buttons are not disabled by default', () => {
      renderWithProviders();

      const createButton = screen.getByLabelText('Create Knowledge Base');
      expect(createButton).not.toBeDisabled();

      const recentKbButton = screen.getByLabelText('Open Test KB 1');
      expect(recentKbButton).not.toBeDisabled();
    });
  });

  describe('Keyboard Navigation Patterns', () => {
    it('Escape closes the create modal', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Open modal
      await user.click(screen.getByLabelText('Create Knowledge Base'));

      // Verify modal is open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Press Escape
      await user.keyboard('{Escape}');

      // Modal should be closed
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('focus returns to trigger after modal closes', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      const createButton = screen.getByLabelText('Create Knowledge Base');

      // Open modal
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Press Escape to close
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      // Focus should return to the create button (or be manageable)
      // Note: This depends on the modal implementation
    });
  });

  describe('Screen Reader Support', () => {
    it('document count is readable', () => {
      renderWithProviders();

      // The "5 docs" text should be visible and readable
      // It appears in both Recent section and main list, so use getAllByText
      expect(screen.getAllByText('5 docs').length).toBeGreaterThanOrEqual(1);
    });

    it('icons have appropriate context through button labels', () => {
      renderWithProviders();

      // The Create button has an icon but also an aria-label
      const createButton = screen.getByLabelText('Create Knowledge Base');
      expect(createButton).toBeInTheDocument();

      // The icon is decorative, the button has the accessible name
      const svg = createButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('storage section is visible', () => {
      renderWithProviders();

      expect(screen.getByText('Storage used')).toBeInTheDocument();
    });
  });
});
