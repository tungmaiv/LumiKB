/**
 * Component Tests: Admin Dashboard Page (Story 5-1, AC1-AC6)
 *
 * Test Coverage:
 * - Loading state (skeleton display)
 * - Error state (error message display)
 * - Success state (all stat cards rendered)
 * - Hook integration (useAdminStats)
 * - Data formatting (formatBytes utility)
 * - Responsive grid layout
 * - Section organization
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import AdminDashboardPage from '../page';

// Mock useAdminStats hook
vi.mock('@/hooks/useAdminStats');

import { useAdminStats } from '@/hooks/useAdminStats';

const mockUseAdminStats = vi.mocked(useAdminStats);

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  Wrapper.displayName = 'QueryClientWrapper';
  return Wrapper;
};

const mockAdminStats = {
  users: {
    total: 150,
    active: 120,
    inactive: 30,
  },
  knowledge_bases: {
    total: 45,
    by_status: {
      active: 40,
      archived: 5,
    },
  },
  documents: {
    total: 1250,
    by_status: {
      READY: 1100,
      PENDING: 75,
      PROCESSING: 50,
      FAILED: 25,
    },
  },
  storage: {
    total_bytes: 1073741824, // 1GB
    avg_doc_size_bytes: 1048576, // 1MB
  },
  activity: {
    searches: {
      last_24h: 42,
      last_7d: 285,
      last_30d: 1150,
    },
    generations: {
      last_24h: 15,
      last_7d: 98,
      last_30d: 420,
    },
  },
  trends: {
    searches: Array.from({ length: 30 }, (_, i) => 90 + i),
    generations: Array.from({ length: 30 }, (_, i) => 45 + i),
  },
};

describe('AdminDashboardPage Component (Story 5-1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] Loading State', () => {
    it('should display loading skeletons while fetching data', () => {
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isSuccess: false,
        isError: false,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should show title
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();

      // Should show 8 skeleton placeholders
      const skeletons = document.querySelectorAll('.h-32');
      expect(skeletons.length).toBeGreaterThanOrEqual(8);
    });

    it('should not show stat cards while loading', () => {
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isSuccess: false,
        isError: false,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Stat cards should not be visible
      expect(screen.queryByText('Total Users')).not.toBeInTheDocument();
      expect(screen.queryByText('Knowledge Bases')).not.toBeInTheDocument();
    });
  });

  describe('[P0] Error State', () => {
    it('should display error message when hook returns error', () => {
      const errorMessage = 'Failed to fetch admin statistics';
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error(errorMessage),
        isSuccess: false,
        isError: true,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should show error message
      expect(screen.getByText(errorMessage)).toBeInTheDocument();

      // Should not show stat cards
      expect(screen.queryByText('Total Users')).not.toBeInTheDocument();
    });

    it('should display generic error message when error is not Error instance', () => {
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: 'String error',
        isSuccess: false,
        isError: true,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should show generic error
      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument();
    });

    it('should apply error styling to error container', () => {
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Test error'),
        isSuccess: false,
        isError: true,
        refetch: vi.fn(),
      } as never);

      const { container } = render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should have destructive border styling
      const errorContainer = container.querySelector('.border-destructive');
      expect(errorContainer).toBeInTheDocument();
    });
  });

  describe('[P0] Success State - User Statistics', () => {
    beforeEach(() => {
      mockUseAdminStats.mockReturnValue({
        data: mockAdminStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);
    });

    it('should render page title and subtitle', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('System-wide statistics and metrics')).toBeInTheDocument();
    });

    it('should render "Users" section with all stat cards', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Section header
      expect(screen.getByText('Users')).toBeInTheDocument();

      // Total Users card
      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('All registered users')).toBeInTheDocument();

      // Active Users card
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('120')).toBeInTheDocument();
      expect(screen.getByText('Active in last 30 days')).toBeInTheDocument();

      // Inactive Users card
      expect(screen.getByText('Inactive Users')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('No activity in 30+ days')).toBeInTheDocument();
    });
  });

  describe('[P0] Success State - Content Statistics', () => {
    beforeEach(() => {
      mockUseAdminStats.mockReturnValue({
        data: mockAdminStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);
    });

    it('should render "Content" section with all stat cards', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Section header
      expect(screen.getByText('Content')).toBeInTheDocument();

      // Knowledge Bases card
      expect(screen.getByText('Knowledge Bases')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('Active: 40')).toBeInTheDocument();

      // Total Documents card
      expect(screen.getByText('Total Documents')).toBeInTheDocument();
      expect(screen.getByText('1250')).toBeInTheDocument();
      expect(screen.getByText('Ready: 1100')).toBeInTheDocument();

      // Failed Documents card
      expect(screen.getByText('Failed Documents')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('Pending: 75')).toBeInTheDocument();
    });

    it('should format storage bytes correctly', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Storage Used card
      expect(screen.getByText('Storage Used')).toBeInTheDocument();
      expect(screen.getByText('1 GB')).toBeInTheDocument(); // 1073741824 bytes = 1GB
      expect(screen.getByText('Avg: 1 MB')).toBeInTheDocument(); // 1048576 bytes = 1MB
    });
  });

  describe('[P0] Success State - Activity Statistics', () => {
    beforeEach(() => {
      mockUseAdminStats.mockReturnValue({
        data: mockAdminStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);
    });

    it('should render "Activity" section with search statistics', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Section header
      expect(screen.getByText('Activity')).toBeInTheDocument();

      // Searches (24h)
      expect(screen.getByText('Searches (24h)')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('7d: 285 | 30d: 1150')).toBeInTheDocument();

      // Searches (7d)
      expect(screen.getByText('Searches (7d)')).toBeInTheDocument();
      expect(screen.getByText('285')).toBeInTheDocument();

      // Searches (30d)
      expect(screen.getByText('Searches (30d)')).toBeInTheDocument();
      expect(screen.getByText('1150')).toBeInTheDocument();
    });

    it('should render "Generations" section with generation statistics', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Section header
      expect(screen.getByText('Generations')).toBeInTheDocument();

      // Generations (24h)
      expect(screen.getByText('Generations (24h)')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('7d: 98 | 30d: 420')).toBeInTheDocument();

      // Generations (7d)
      expect(screen.getByText('Generations (7d)')).toBeInTheDocument();
      expect(screen.getByText('98')).toBeInTheDocument();

      // Generations (30d)
      expect(screen.getByText('Generations (30d)')).toBeInTheDocument();
      expect(screen.getByText('420')).toBeInTheDocument();
    });
  });

  describe('[P1] Data Formatting', () => {
    it('should format bytes correctly for various sizes', () => {
      const testCases = [
        { bytes: 0, expected: '0 Bytes' },
        { bytes: 1024, expected: '1 KB' },
        { bytes: 1048576, expected: '1 MB' },
        { bytes: 1073741824, expected: '1 GB' },
        { bytes: 524288, expected: '512 KB' },
      ];

      testCases.forEach(({ bytes, expected }) => {
        const statsWithBytes = {
          ...mockAdminStats,
          storage: {
            total_bytes: bytes,
            avg_doc_size_bytes: 0,
          },
        };

        mockUseAdminStats.mockReturnValue({
          data: statsWithBytes,
          isLoading: false,
          error: null,
          isSuccess: true,
          isError: false,
          refetch: vi.fn(),
        } as never);

        const { unmount } = render(<AdminDashboardPage />, { wrapper: createWrapper() });

        expect(screen.getByText(expected)).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('[P2] Edge Cases', () => {
    it('should handle missing by_status data gracefully', () => {
      const statsWithMissingStatus = {
        ...mockAdminStats,
        knowledge_bases: {
          total: 50,
          by_status: {},
        },
        documents: {
          total: 1000,
          by_status: {},
        },
      };

      mockUseAdminStats.mockReturnValue({
        data: statsWithMissingStatus,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should show 0 for missing status counts
      expect(screen.getByText('Active: 0')).toBeInTheDocument();
      expect(screen.getByText('Ready: 0')).toBeInTheDocument();
      expect(screen.getByText('Pending: 0')).toBeInTheDocument();
    });

    it('should render nothing when stats is undefined (edge case)', () => {
      mockUseAdminStats.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should render empty container inside DashboardLayout (no stat cards)
      expect(screen.queryByText('Total Users')).not.toBeInTheDocument();
      expect(screen.queryByText('Knowledge Bases')).not.toBeInTheDocument();
    });

    it('should handle zero values correctly', () => {
      const zeroStats = {
        users: { total: 0, active: 0, inactive: 0 },
        knowledge_bases: { total: 0, by_status: {} },
        documents: { total: 0, by_status: {} },
        storage: { total_bytes: 0, avg_doc_size_bytes: 0 },
        activity: {
          searches: { last_24h: 0, last_7d: 0, last_30d: 0 },
          generations: { last_24h: 0, last_7d: 0, last_30d: 0 },
        },
        trends: { searches: [], generations: [] },
      };

      mockUseAdminStats.mockReturnValue({
        data: zeroStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);

      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should show zeros
      expect(screen.getAllByText('0').length).toBeGreaterThan(0);
      expect(screen.getByText('0 Bytes')).toBeInTheDocument();
    });
  });

  describe('[P2] Responsive Layout', () => {
    beforeEach(() => {
      mockUseAdminStats.mockReturnValue({
        data: mockAdminStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);
    });

    it('should apply responsive grid classes', () => {
      const { container } = render(<AdminDashboardPage />, { wrapper: createWrapper() });

      // Should have responsive grid classes
      const grids = container.querySelectorAll('.grid');
      expect(grids.length).toBeGreaterThan(0);

      // Check for responsive breakpoint classes
      const hasResponsiveClasses = Array.from(grids).some((grid) => {
        const classes = grid.className;
        return classes.includes('md:grid-cols') || classes.includes('lg:grid-cols');
      });

      expect(hasResponsiveClasses).toBe(true);
    });

    it('should have container with padding', () => {
      const { container } = render(<AdminDashboardPage />, { wrapper: createWrapper() });

      const mainContainer = container.querySelector('.container');
      expect(mainContainer).toBeInTheDocument();
      expect(mainContainer).toHaveClass('mx-auto', 'p-6');
    });
  });

  describe('[P1] Section Organization', () => {
    beforeEach(() => {
      mockUseAdminStats.mockReturnValue({
        data: mockAdminStats,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
      } as never);
    });

    it('should render all 5 sections in correct order', () => {
      render(<AdminDashboardPage />, { wrapper: createWrapper() });

      const sections = screen.getAllByRole('heading', { level: 2 });

      expect(sections).toHaveLength(5);
      expect(sections[0]).toHaveTextContent('Users');
      expect(sections[1]).toHaveTextContent('Content');
      expect(sections[2]).toHaveTextContent('Activity');
      expect(sections[3]).toHaveTextContent('Generations');
      expect(sections[4]).toHaveTextContent('Admin Tools');
    });

    it('should have semantic section elements', () => {
      const { container } = render(<AdminDashboardPage />, { wrapper: createWrapper() });

      const sections = container.querySelectorAll('section');
      expect(sections.length).toBeGreaterThanOrEqual(3);
    });
  });
});
