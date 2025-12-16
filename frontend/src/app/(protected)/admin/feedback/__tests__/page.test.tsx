/**
 * Feedback Analytics Page Tests - Story 7-23
 *
 * Tests for the admin feedback analytics dashboard page:
 * - AC-7.23.1: Admin dashboard page at /admin/feedback
 * - AC-7.23.2: Pie chart for feedback type distribution
 * - AC-7.23.3: Line chart for 30-day trend
 * - AC-7.23.4: Table of 20 most recent feedback items
 * - AC-7.23.5: Modal for feedback detail view
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import FeedbackAnalyticsPage from '../page';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock recharts to avoid canvas rendering issues in tests
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: ({ data }: { data: Array<{ name: string; count: number }> }) => (
    <div data-testid="pie" data-items={data.length} />
  ),
  Cell: () => <div data-testid="pie-cell" />,
  LineChart: ({ children, data }: { children: ReactNode; data: Array<{ date: string; count: number }> }) => (
    <div data-testid="line-chart" data-items={data.length}>{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('FeedbackAnalyticsPage', () => {
  let queryClient: QueryClient;

  const mockAnalyticsData = {
    by_type: [
      { type: 'not_relevant', count: 10 },
      { type: 'inaccurate', count: 5 },
      { type: 'incomplete', count: 3 },
    ],
    by_day: [
      { date: '2025-12-01', count: 2 },
      { date: '2025-12-02', count: 3 },
      { date: '2025-12-03', count: 5 },
      { date: '2025-12-04', count: 1 },
      { date: '2025-12-05', count: 4 },
    ],
    recent: [
      {
        id: 'fb-1',
        timestamp: '2025-12-03T10:00:00Z',
        user_id: 'user-123',
        user_email: 'test@example.com',
        draft_id: 'draft-456',
        feedback_type: 'not_relevant',
        feedback_comments: 'This was not helpful for my use case',
        related_request_id: 'req-789',
      },
      {
        id: 'fb-2',
        timestamp: '2025-12-02T14:30:00Z',
        user_id: 'user-456',
        user_email: 'another@example.com',
        draft_id: 'draft-789',
        feedback_type: 'inaccurate',
        feedback_comments: 'The information was incorrect',
        related_request_id: null,
      },
      {
        id: 'fb-3',
        timestamp: '2025-12-01T09:15:00Z',
        user_id: null,
        user_email: null,
        draft_id: null,
        feedback_type: 'incomplete',
        feedback_comments: null,
        related_request_id: null,
      },
    ],
    total_count: 18,
  };

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    mockFetch.mockReset();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('loading state', () => {
    it('shows loading skeletons while fetching data', () => {
      mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<FeedbackAnalyticsPage />, { wrapper });

      // Should show skeleton loaders
      const skeletons = document.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('error state', () => {
    it('shows error message when API returns 403', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 403,
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(
        () => {
          expect(screen.getByText('Unauthorized: Admin access required')).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('shows error message when API returns 401', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(
        () => {
          expect(screen.getByText('Authentication required')).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('shows generic error for other failures', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(
        () => {
          expect(screen.getByText('Failed to fetch feedback analytics')).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('page header (AC-7.23.1)', () => {
    it('displays page title "Feedback Analytics"', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics')).toBeInTheDocument();
      });
    });

    it('shows total feedback count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('18')).toBeInTheDocument();
        expect(screen.getByText('Total Feedback')).toBeInTheDocument();
      });
    });

    it('has back navigation to admin page', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        const backLink = screen.getByRole('link', { name: '' });
        expect(backLink).toHaveAttribute('href', '/admin');
      });
    });
  });

  describe('feedback by type chart (AC-7.23.2)', () => {
    it('renders pie chart with type distribution', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Feedback by Type')).toBeInTheDocument();
        expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      });
    });

    it('shows "No feedback data" when by_type is empty', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockAnalyticsData,
            by_type: [],
          }),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('No feedback data')).toBeInTheDocument();
      });
    });
  });

  describe('feedback trend chart (AC-7.23.3)', () => {
    it('renders line chart with trend data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Feedback Trend')).toBeInTheDocument();
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });

    it('allows toggling between daily and weekly view', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Feedback Trend')).toBeInTheDocument();
      });

      // Find and click the view toggle
      const selectTrigger = screen.getByRole('combobox');
      fireEvent.click(selectTrigger);

      // Select weekly view
      await waitFor(() => {
        const weeklyOption = screen.getByRole('option', { name: 'Weekly' });
        fireEvent.click(weeklyOption);
      });
    });

    it('shows "No trend data" when by_day is empty', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockAnalyticsData,
            by_day: [],
          }),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('No trend data')).toBeInTheDocument();
      });
    });
  });

  describe('recent feedback table (AC-7.23.4)', () => {
    it('renders table with recent feedback items', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Recent Feedback')).toBeInTheDocument();
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    it('displays user email in table rows', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
        expect(screen.getByText('another@example.com')).toBeInTheDocument();
      });
    });

    it('shows "Anonymous" for null user email', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Anonymous')).toBeInTheDocument();
      });
    });

    it('displays feedback type badges', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Not Relevant')).toBeInTheDocument();
        expect(screen.getByText('Inaccurate')).toBeInTheDocument();
        expect(screen.getByText('Incomplete')).toBeInTheDocument();
      });
    });

    it('shows "No recent feedback" when recent is empty', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockAnalyticsData,
            recent: [],
          }),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('No recent feedback')).toBeInTheDocument();
      });
    });

    it('truncates long comments in table', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        // Comments column should have truncate class
        const commentCell = screen.getByText('This was not helpful for my use case');
        expect(commentCell.closest('td')).toHaveClass('truncate');
      });
    });

    it('shows "No comments" for null feedback_comments', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('No comments')).toBeInTheDocument();
      });
    });
  });

  describe('feedback detail modal (AC-7.23.5)', () => {
    it('opens modal when View button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Click the first View button
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Feedback Details')).toBeInTheDocument();
      });
    });

    it('shows feedback details in modal', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Click View for first item
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        // Check modal content
        const dialog = screen.getByRole('dialog');
        expect(within(dialog).getByText('test@example.com')).toBeInTheDocument();
        expect(within(dialog).getByText('Not Relevant')).toBeInTheDocument();
        expect(
          within(dialog).getByText('This was not helpful for my use case')
        ).toBeInTheDocument();
      });
    });

    it('shows draft link when draft_id is present', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Click View for first item (has draft_id)
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        const dialog = screen.getByRole('dialog');
        expect(within(dialog).getByText('Related Draft')).toBeInTheDocument();
        expect(within(dialog).getByText('draft-456')).toBeInTheDocument();
        expect(within(dialog).getByText('View Draft')).toBeInTheDocument();
      });
    });

    it('shows request ID when present', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Click View for first item (has related_request_id)
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        const dialog = screen.getByRole('dialog');
        expect(within(dialog).getByText('Request ID')).toBeInTheDocument();
        expect(within(dialog).getByText('req-789')).toBeInTheDocument();
      });
    });

    it('handles anonymous feedback in modal', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Click View for third item (anonymous, no draft, no comments)
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[2]);

      await waitFor(() => {
        const dialog = screen.getByRole('dialog');
        // Should show "Anonymous" for null user_email
        expect(within(dialog).getAllByText('Anonymous')).toHaveLength(1);
        // Should show "No comments provided" for null comments
        expect(within(dialog).getByText('No comments provided')).toBeInTheDocument();
      });
    });

    it('closes modal when dialog is dismissed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockAnalyticsData),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Open modal
      const viewButtons = screen.getAllByRole('button', { name: 'View' });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close modal by pressing Escape
      fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('no data state', () => {
    it('shows no data message when data is null', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(null),
      });

      render(<FeedbackAnalyticsPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('No Data')).toBeInTheDocument();
        expect(screen.getByText('No feedback data available yet.')).toBeInTheDocument();
      });
    });
  });
});
