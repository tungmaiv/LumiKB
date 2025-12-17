/**
 * Unit tests for Processing Pipeline Widget.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * RED PHASE: All tests are designed to FAIL until implementation is complete.
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useRouter } from 'next/navigation';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

// Mock data factory
function createProcessingPipelineData(overrides = {}) {
  return {
    documentsProcessed: 127,
    avgProcessingTimeMs: 8500,
    errorRate: 2.3,
    trend: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
      value: Math.floor(Math.random() * 20) + 5,
    })),
    ...overrides,
  };
}

// Test wrapper with providers
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe('ProcessingPipelineWidget', () => {
  const mockRouter = { push: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
  });

  describe('AC2: Documents processed, avg time, error rate', () => {
    it('renders_documents_processed_count', async () => {
      const data = createProcessingPipelineData();

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-docs-count')).toBeInTheDocument();
      });

      expect(screen.getByTestId('processing-docs-count')).toHaveTextContent('127');
    });

    it('renders_avg_processing_time', async () => {
      const data = createProcessingPipelineData();

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-avg-time')).toBeInTheDocument();
      });

      expect(screen.getByTestId('processing-avg-time')).toHaveTextContent('8.5s');
    });

    it('renders_error_rate_percentage', async () => {
      const data = createProcessingPipelineData();

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-error-rate')).toBeInTheDocument();
      });

      expect(screen.getByTestId('processing-error-rate')).toHaveTextContent('2.3%');
    });

    it('shows_warning_indicator_for_high_error_rate', async () => {
      const data = createProcessingPipelineData({ errorRate: 15.5 });

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-error-rate')).toHaveClass('text-destructive');
      });
    });
  });

  describe('AC7: Sparkline charts for trends', () => {
    it('renders_sparkline_for_trend', async () => {
      const data = createProcessingPipelineData();

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-sparkline')).toBeInTheDocument();
      });
    });
  });

  describe('AC8: Click navigation', () => {
    it('navigates_to_document_timeline_on_click', async () => {
      const data = createProcessingPipelineData();

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-widget')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('processing-widget'));

      expect(mockRouter.push).toHaveBeenCalledWith('/admin/observability/documents');
    });
  });

  describe('Edge cases', () => {
    it('handles_zero_documents_processed', async () => {
      const data = createProcessingPipelineData({
        documentsProcessed: 0,
        avgProcessingTimeMs: 0,
        errorRate: 0,
      });

      const ProcessingPipelineWidget = await import('../processing-widget').then(
        (m) => m.ProcessingPipelineWidget
      );

      renderWithProviders(<ProcessingPipelineWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId('processing-docs-count')).toHaveTextContent('0');
      });
    });
  });
});
