import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import { KbSidebar } from '../../layout/kb-sidebar';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/search',
}));

// Mock react-query hooks that the component uses
vi.mock('@/hooks/useRecentKBs', () => ({
  useRecentKBs: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/hooks/useKBRecommendations', () => ({
  useKBRecommendations: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
}));

// Create a wrapper with QueryClientProvider for any nested hooks
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Mock data
const mockKbs: KnowledgeBase[] = [
  {
    id: '1',
    name: 'Test KB 1',
    description: 'Description 1',
    status: 'active',
    document_count: 5,
    permission_level: 'ADMIN',
    tags: ['test', 'admin'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    archived_at: null,
  },
  {
    id: '2',
    name: 'Test KB 2',
    description: 'Description 2',
    status: 'active',
    document_count: 0,
    permission_level: 'READ',
    tags: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    archived_at: null,
  },
];

// Mock store state
const mockFetchKbs = vi.fn();
const mockSetActiveKb = vi.fn();
const mockCreateKb = vi.fn();

let mockStoreState = {
  kbs: [] as KnowledgeBase[],
  activeKb: null as KnowledgeBase | null,
  isLoading: false,
  error: null as string | null,
  fetchKbs: mockFetchKbs,
  setActiveKb: mockSetActiveKb,
  createKb: mockCreateKb,
  clearError: vi.fn(),
};

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: (selector?: (state: typeof mockStoreState) => unknown) => {
    if (selector) {
      return selector(mockStoreState);
    }
    return mockStoreState;
  },
}));

vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: (selector?: (state: { user: { id: string } | null }) => unknown) => {
    const state = { user: { id: 'user-1' } };
    if (selector) {
      return selector(state);
    }
    return state;
  },
}));

describe('KbSidebar', () => {
  const Wrapper = createWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
    mockStoreState = {
      kbs: [],
      activeKb: null,
      isLoading: false,
      error: null,
      fetchKbs: mockFetchKbs,
      setActiveKb: mockSetActiveKb,
      createKb: mockCreateKb,
      clearError: vi.fn(),
    };
  });

  it('renders Knowledge Bases header', () => {
    render(<KbSidebar />, { wrapper: Wrapper });
    expect(screen.getByText('Knowledge Bases')).toBeInTheDocument();
  });

  it('calls fetchKbs on mount', () => {
    render(<KbSidebar />, { wrapper: Wrapper });
    expect(mockFetchKbs).toHaveBeenCalled();
  });

  it('shows loading skeleton when isLoading is true', () => {
    mockStoreState.isLoading = true;
    render(<KbSidebar />, { wrapper: Wrapper });

    // Skeleton has multiple divs with specific classes
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows error message when error exists', () => {
    mockStoreState.error = 'Failed to load';
    render(<KbSidebar />, { wrapper: Wrapper });

    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('shows empty state when no KBs exist', () => {
    mockStoreState.kbs = [];
    render(<KbSidebar />, { wrapper: Wrapper });

    expect(screen.getByText('No Knowledge Bases available')).toBeInTheDocument();
  });

  it('shows Create KB CTA in empty state for authenticated users', () => {
    mockStoreState.kbs = [];
    render(<KbSidebar />, { wrapper: Wrapper });

    expect(screen.getByText('Create your first Knowledge Base')).toBeInTheDocument();
  });

  it('renders list of KBs when data exists', () => {
    mockStoreState.kbs = mockKbs;
    render(<KbSidebar />, { wrapper: Wrapper });

    expect(screen.getByText('Test KB 1')).toBeInTheDocument();
    expect(screen.getByText('Test KB 2')).toBeInTheDocument();
  });

  it('shows correct document counts', () => {
    mockStoreState.kbs = mockKbs;
    render(<KbSidebar />, { wrapper: Wrapper });

    expect(screen.getByText('5 docs')).toBeInTheDocument();
    expect(screen.getByText('0 docs')).toBeInTheDocument();
  });

  it('calls setActiveKb when KB item is clicked', async () => {
    const user = userEvent.setup();
    mockStoreState.kbs = mockKbs;
    render(<KbSidebar />, { wrapper: Wrapper });

    await user.click(screen.getByText('Test KB 1'));
    expect(mockSetActiveKb).toHaveBeenCalledWith(mockKbs[0]);
  });

  it('highlights active KB', () => {
    mockStoreState.kbs = mockKbs;
    mockStoreState.activeKb = mockKbs[0];
    render(<KbSidebar />, { wrapper: Wrapper });

    const buttons = screen.getAllByRole('button');
    // First KB button should have active styling (skip Create button)
    const kbButtons = buttons.filter((btn) => btn.textContent?.includes('Test KB'));
    expect(kbButtons[0]).toHaveClass('bg-accent');
  });

  it('renders Create KB button for authenticated users', () => {
    render(<KbSidebar />, { wrapper: Wrapper });
    expect(screen.getByLabelText('Create Knowledge Base')).toBeInTheDocument();
  });

  it('opens create modal when Create KB button is clicked', async () => {
    const user = userEvent.setup();
    render(<KbSidebar />, { wrapper: Wrapper });

    await user.click(screen.getByLabelText('Create Knowledge Base'));

    await waitFor(() => {
      expect(screen.getByText('Create Knowledge Base')).toBeInTheDocument();
    });
  });
});
