import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { KbSidebar } from '../kb-sidebar';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';
import type { RecentKB } from '@/hooks/useRecentKBs';
import type { KBRecommendation } from '@/hooks/useKBRecommendations';

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
  {
    kb_id: 'kb-2',
    kb_name: 'Test KB 2',
    description: 'Description 2',
    last_accessed: '2025-12-03T09:00:00Z',
    document_count: 10,
  },
];

const mockRecommendations: KBRecommendation[] = [
  {
    kb_id: 'kb-rec-1',
    kb_name: 'Recommended KB 1',
    description: 'Popular KB',
    score: 0.95,
    reason: 'Based on your recent activity',
    last_accessed: null,
    is_cold_start: true,
  },
  {
    kb_id: 'kb-rec-2',
    kb_name: 'Recommended KB 2',
    description: 'Trending KB',
    score: 0.85,
    reason: 'Popular in your organization',
    last_accessed: null,
    is_cold_start: true,
  },
];

// Mock store state
const mockSetActiveKb = vi.fn();
const mockFetchKbs = vi.fn();

let mockKBStoreState = {
  kbs: mockKbs,
  activeKb: null as KnowledgeBase | null,
  isLoading: false,
  error: null as string | null,
  fetchKbs: mockFetchKbs,
  setActiveKb: mockSetActiveKb,
  createKb: vi.fn(),
  clearError: vi.fn(),
};

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: (selector?: (state: typeof mockKBStoreState) => unknown) => {
    if (selector) return selector(mockKBStoreState);
    return mockKBStoreState;
  },
}));

vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: (selector?: (state: { user: { id: string } | null }) => unknown) => {
    const state = { user: { id: 'user-1' } };
    if (selector) return selector(state);
    return state;
  },
}));

// Mock hooks with controllable state
let mockRecentKBsHook = {
  data: mockRecentKBs as RecentKB[] | undefined,
  isLoading: false,
  isError: false,
  error: null as Error | null,
};

let mockRecommendationsHook = {
  data: [] as KBRecommendation[] | undefined,
  isLoading: false,
  isError: false,
  error: null as Error | null,
};

vi.mock('@/hooks/useRecentKBs', () => ({
  useRecentKBs: () => mockRecentKBsHook,
}));

vi.mock('@/hooks/useKBRecommendations', () => ({
  useKBRecommendations: () => mockRecommendationsHook,
}));

describe('KbSidebar - Recent KBs Section', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockClear();
    mockSetActiveKb.mockClear();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Reset mock states
    mockRecentKBsHook = {
      data: mockRecentKBs,
      isLoading: false,
      isError: false,
      error: null,
    };

    mockRecommendationsHook = {
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    };

    mockKBStoreState = {
      kbs: mockKbs,
      activeKb: null,
      isLoading: false,
      error: null,
      fetchKbs: mockFetchKbs,
      setActiveKb: mockSetActiveKb,
      createKb: vi.fn(),
      clearError: vi.fn(),
    };
  });

  const renderWithProviders = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <KbSidebar />
      </QueryClientProvider>
    );
  };

  describe('Recent KBs Display (AC-5.9.1)', () => {
    it('renders Recent section header when KBs exist', () => {
      renderWithProviders();

      expect(screen.getByText('Recent')).toBeInTheDocument();
    });

    it('displays recent KBs in the sidebar', () => {
      renderWithProviders();

      // Both recent KBs should be displayed
      expect(screen.getByLabelText('Open Test KB 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Open Test KB 2')).toBeInTheDocument();
    });

    it('shows document count for each recent KB', () => {
      renderWithProviders();

      // Document counts appear in both Recent section and main list,
      // so we check that they exist (at least one instance)
      expect(screen.getAllByText('5 docs').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('10 docs').length).toBeGreaterThanOrEqual(1);
    });

    it('limits display to maximum 5 recent KBs', () => {
      // Create 7 recent KBs
      const manyRecentKBs: RecentKB[] = Array.from({ length: 7 }, (_, i) => ({
        kb_id: `kb-${i}`,
        kb_name: `KB Number ${i}`,
        description: `Description ${i}`,
        last_accessed: `2025-12-03T${10 - i}:00:00Z`,
        document_count: i * 5,
      }));

      mockRecentKBsHook.data = manyRecentKBs;

      // Also add corresponding KBs to the store
      mockKBStoreState.kbs = Array.from({ length: 7 }, (_, i) => ({
        id: `kb-${i}`,
        name: `KB Number ${i}`,
        description: `Description ${i}`,
        status: 'active' as const,
        document_count: i * 5,
        permission_level: 'READ' as const,
        tags: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        archived_at: null,
      }));

      renderWithProviders();

      // Should only show 5 recent KBs (slice(0, 5) in component)
      expect(screen.getByLabelText('Open KB Number 0')).toBeInTheDocument();
      expect(screen.getByLabelText('Open KB Number 4')).toBeInTheDocument();
      expect(screen.queryByLabelText('Open KB Number 5')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Open KB Number 6')).not.toBeInTheDocument();
    });

    it('hides Recent section when no recent KBs', () => {
      mockRecentKBsHook.data = [];

      renderWithProviders();

      expect(screen.queryByText('Recent')).not.toBeInTheDocument();
    });

    it('applies truncate class to KB names', () => {
      renderWithProviders();

      const kbButtons = screen.getAllByLabelText(/^Open Test KB/);
      kbButtons.forEach((button) => {
        const nameSpan = button.querySelector('span.truncate');
        expect(nameSpan).toBeInTheDocument();
      });
    });
  });

  describe('Recent KB Navigation (AC-5.9.4)', () => {
    it('calls setActiveKb when recent KB is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await user.click(screen.getByLabelText('Open Test KB 1'));

      expect(mockSetActiveKb).toHaveBeenCalledWith(mockKbs[0]);
    });

    it('navigates to search page with kb query param', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await user.click(screen.getByLabelText('Open Test KB 1'));

      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-1');
    });

    it('handles click on KB not in store gracefully', async () => {
      const user = userEvent.setup();

      // Add a recent KB that's not in the store
      mockRecentKBsHook.data = [
        {
          kb_id: 'kb-not-in-store',
          kb_name: 'Missing KB',
          description: 'Not in store',
          last_accessed: '2025-12-03T10:00:00Z',
          document_count: 0,
        },
      ];

      renderWithProviders();

      await user.click(screen.getByLabelText('Open Missing KB'));

      // Should still navigate even if KB not in store
      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-not-in-store');
      // setActiveKb should not be called since KB not found
      expect(mockSetActiveKb).not.toHaveBeenCalled();
    });

    it('sets correct active KB when multiple KBs exist', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      // Click on second KB
      await user.click(screen.getByLabelText('Open Test KB 2'));

      expect(mockSetActiveKb).toHaveBeenCalledWith(mockKbs[1]);
      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-2');
    });
  });

  describe('Loading States (AC-5.9.7)', () => {
    it('shows skeleton during loading', () => {
      mockRecentKBsHook.isLoading = true;
      mockRecentKBsHook.data = undefined;

      renderWithProviders();

      // Should show Recent section header even during loading
      expect(screen.getByText('Recent')).toBeInTheDocument();

      // Should show skeleton elements (animate-pulse class)
      const skeletons = document.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('hides skeleton when data loads', () => {
      mockRecentKBsHook.isLoading = false;
      mockRecentKBsHook.data = mockRecentKBs;

      renderWithProviders();

      // Should show actual KB names
      expect(screen.getByLabelText('Open Test KB 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Open Test KB 2')).toBeInTheDocument();
    });

    it('shows Recent section header during loading', () => {
      mockRecentKBsHook.isLoading = true;

      renderWithProviders();

      expect(screen.getByText('Recent')).toBeInTheDocument();
    });
  });

  describe('Recommendations Section (AC-5.9.6)', () => {
    it('shows Recommendations section when user has no history', () => {
      mockRecentKBsHook.data = [];
      mockRecentKBsHook.isLoading = false;
      mockRecommendationsHook.data = mockRecommendations;

      renderWithProviders();

      expect(screen.getByText('Suggested for you')).toBeInTheDocument();
    });

    it('hides Recommendations when user has recent KBs', () => {
      mockRecentKBsHook.data = mockRecentKBs;
      mockRecommendationsHook.data = mockRecommendations;

      renderWithProviders();

      expect(screen.queryByText('Suggested for you')).not.toBeInTheDocument();
    });

    it('displays recommendation reasons in tooltip/title', () => {
      mockRecentKBsHook.data = [];
      mockRecommendationsHook.data = mockRecommendations;

      renderWithProviders();

      const recButton = screen.getByLabelText(
        'Open Recommended KB 1 - Based on your recent activity'
      );
      expect(recButton).toHaveAttribute('title', 'Based on your recent activity');
    });

    it('navigates when recommendation is clicked', async () => {
      const user = userEvent.setup();
      mockRecentKBsHook.data = [];
      mockRecommendationsHook.data = mockRecommendations;

      // Add recommended KB to store
      mockKBStoreState.kbs = [
        ...mockKbs,
        {
          id: 'kb-rec-1',
          name: 'Recommended KB 1',
          description: 'Popular KB',
          status: 'active',
          document_count: 20,
          permission_level: 'READ' as const,
          tags: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          archived_at: null,
        },
      ];

      renderWithProviders();

      await user.click(
        screen.getByLabelText('Open Recommended KB 1 - Based on your recent activity')
      );

      expect(mockPush).toHaveBeenCalledWith('/search?kb=kb-rec-1');
    });

    it('limits recommendations to 3', () => {
      mockRecentKBsHook.data = [];
      mockRecommendationsHook.data = [
        ...mockRecommendations,
        {
          kb_id: 'kb-rec-3',
          kb_name: 'Recommended KB 3',
          description: 'Third recommendation',
          score: 0.75,
          reason: 'Another reason',
          last_accessed: null,
          is_cold_start: true,
        },
        {
          kb_id: 'kb-rec-4',
          kb_name: 'Recommended KB 4',
          description: 'Fourth recommendation',
          score: 0.65,
          reason: 'Yet another reason',
          last_accessed: null,
          is_cold_start: true,
        },
      ];

      renderWithProviders();

      // Should only show 3 recommendations (slice(0, 3) in component)
      expect(
        screen.getByLabelText('Open Recommended KB 1 - Based on your recent activity')
      ).toBeInTheDocument();
      expect(
        screen.getByLabelText('Open Recommended KB 2 - Popular in your organization')
      ).toBeInTheDocument();
      expect(
        screen.getByLabelText('Open Recommended KB 3 - Another reason')
      ).toBeInTheDocument();
      expect(
        screen.queryByLabelText('Open Recommended KB 4 - Yet another reason')
      ).not.toBeInTheDocument();
    });
  });

  describe('Empty State (AC-5.9.3)', () => {
    it('shows empty state when no KBs available', () => {
      mockKBStoreState.kbs = [];
      mockRecentKBsHook.data = [];
      mockRecommendationsHook.data = [];

      renderWithProviders();

      expect(screen.getByText('No Knowledge Bases available')).toBeInTheDocument();
    });

    it('shows Create CTA in empty state for authenticated users', () => {
      mockKBStoreState.kbs = [];
      mockRecentKBsHook.data = [];

      renderWithProviders();

      expect(screen.getByText('Create your first Knowledge Base')).toBeInTheDocument();
    });
  });

  describe('All Knowledge Bases Section', () => {
    it('shows "All Knowledge Bases" header when recent KBs exist', () => {
      mockRecentKBsHook.data = mockRecentKBs;

      renderWithProviders();

      expect(screen.getByText('All Knowledge Bases')).toBeInTheDocument();
    });

    it('shows "All Knowledge Bases" header when recommendations shown', () => {
      mockRecentKBsHook.data = [];
      mockRecommendationsHook.data = mockRecommendations;

      renderWithProviders();

      expect(screen.getByText('All Knowledge Bases')).toBeInTheDocument();
    });

    it('renders all KBs in the main list', () => {
      renderWithProviders();

      // KBs should appear in the main list via KbSelectorItem
      expect(screen.getAllByText('Test KB 1').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Test KB 2').length).toBeGreaterThanOrEqual(1);
    });
  });
});
