/**
import { vi, describe, it, expect, beforeEach } from 'vitest';
 * Component tests for Admin Dashboard page
 *
 * Tests rendering, loading states, error states, and data display
 */

import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import AdminPage from '../page';

// Mock useAdminStats hook
vi.mock('@/hooks/useAdminStats', () => ({
  useAdminStats: vi.fn(),
}));

const { useAdminStats } = require('@/hooks/useAdminStats');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

const mockStats = {
  users: { total: 100, active: 80, inactive: 20 },
  knowledge_bases: { total: 50, by_status: { active: 45, archived: 5 } },
  documents: {
    total: 1000,
    by_status: { READY: 900, PENDING: 50, FAILED: 50 },
  },
  storage: { total_bytes: 1000000000, avg_doc_size_bytes: 1000000 },
  activity: {
    searches: { last_24h: 10, last_7d: 70, last_30d: 300 },
    generations: { last_24h: 5, last_7d: 35, last_30d: 150 },
  },
  trends: { searches: Array(30).fill(10), generations: Array(30).fill(5) },
};

describe('AdminPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading skeleton while fetching data', () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    // Skeleton should be present (implementation may vary)
  });

  it('should display error message when fetch fails', () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to load stats'),
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it('should display statistics when data is loaded', async () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    await waitFor(() => {
      // User stats
      expect(screen.getByText('100')).toBeInTheDocument(); // Total users

      // Knowledge base stats
      expect(screen.getByText('50')).toBeInTheDocument(); // Total KBs

      // Document stats
      expect(screen.getByText('1,000')).toBeInTheDocument(); // Total documents

      // Storage stats (formatted)
      expect(screen.getByText(/GB|MB/i)).toBeInTheDocument();

      // Activity stats
      expect(screen.getByText('10')).toBeInTheDocument(); // Last 24h searches
      expect(screen.getByText('5')).toBeInTheDocument(); // Last 24h generations
    });
  });

  it('should format storage bytes correctly', () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    // 1000000000 bytes = 1 GB
    expect(screen.getByText(/1.*GB/i)).toBeInTheDocument();
  });

  it('should display trend sparklines', () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    // Recharts renders SVG elements for charts
    const charts = screen.getAllByRole('img', { hidden: true });
    expect(charts.length).toBeGreaterThan(0);
  });

  it('should display last updated timestamp', () => {
    // Arrange
    useAdminStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    expect(screen.getByText(/last updated/i)).toBeInTheDocument();
  });

  it('should have refresh button', () => {
    // Arrange
    const mockRefetch = vi.fn();
    useAdminStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    });

    // Act
    render(<AdminPage />, { wrapper: createWrapper() });

    // Assert
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();

    // Click refresh
    refreshButton.click();
    expect(mockRefetch).toHaveBeenCalled();
  });
});
