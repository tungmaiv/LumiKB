/**
 * Unit tests for ModelHealthIndicator component
 * Story 7-2: Centralized LLM Configuration (AC-7.2.4)
 *
 * Tests:
 * - Displaying healthy model status
 * - Displaying unhealthy model status with error messages
 * - Loading state display
 * - Refresh button functionality
 * - Latency color coding
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ModelHealthIndicator } from '../model-health-indicator';
import type { LLMHealthResponse } from '@/types/llm-config';

// Mock TooltipProvider
vi.mock('@/components/ui/tooltip', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/components/ui/tooltip')>();
  return {
    ...actual,
    TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

const mockHealthyResponse: LLMHealthResponse = {
  embedding_health: {
    model_type: 'embedding',
    model_name: 'text-embedding-3-small',
    is_healthy: true,
    latency_ms: 150,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  generation_health: {
    model_type: 'generation',
    model_name: 'Claude 3 Sonnet',
    is_healthy: true,
    latency_ms: 320,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  overall_healthy: true,
};

const mockUnhealthyResponse: LLMHealthResponse = {
  embedding_health: {
    model_type: 'embedding',
    model_name: 'text-embedding-3-small',
    is_healthy: false,
    latency_ms: null,
    error_message: 'Connection refused: Unable to reach embedding API',
    last_checked: '2024-01-15T10:35:00Z',
  },
  generation_health: {
    model_type: 'generation',
    model_name: 'Claude 3 Sonnet',
    is_healthy: true,
    latency_ms: 450,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  overall_healthy: false,
};

const mockPartialHealthResponse: LLMHealthResponse = {
  embedding_health: null,
  generation_health: {
    model_type: 'generation',
    model_name: 'Claude 3 Sonnet',
    is_healthy: true,
    latency_ms: 200,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  overall_healthy: true,
};

describe('ModelHealthIndicator', () => {
  const defaultProps = {
    health: mockHealthyResponse,
    isLoading: false,
    onRefresh: vi.fn().mockResolvedValue(undefined),
    isRefreshing: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Display', () => {
    it('should render Model Health Status title', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByText('Model Health Status')).toBeInTheDocument();
    });

    it('should display "All Healthy" badge when overall_healthy is true', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByText('All Healthy')).toBeInTheDocument();
    });

    it('should display "Issues Detected" badge when overall_healthy is false', () => {
      render(<ModelHealthIndicator {...defaultProps} health={mockUnhealthyResponse} />);

      expect(screen.getByText('Issues Detected')).toBeInTheDocument();
    });

    it('should display embedding model name', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByText('Embedding Model')).toBeInTheDocument();
      expect(screen.getByText('text-embedding-3-small')).toBeInTheDocument();
    });

    it('should display generation model name', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByText('Generation Model')).toBeInTheDocument();
      expect(screen.getByText('Claude 3 Sonnet')).toBeInTheDocument();
    });

    it('should display latency for healthy models', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByText('150ms')).toBeInTheDocument();
      expect(screen.getByText('320ms')).toBeInTheDocument();
    });

    it('should display "Not configured" when model is null', () => {
      render(<ModelHealthIndicator {...defaultProps} health={mockPartialHealthResponse} />);

      expect(screen.getByText('Not configured')).toBeInTheDocument();
    });
  });

  describe('Unhealthy State', () => {
    it('should show error details tooltip for unhealthy model', () => {
      render(<ModelHealthIndicator {...defaultProps} health={mockUnhealthyResponse} />);

      expect(screen.getByText('Error details')).toBeInTheDocument();
    });

    it('should not show latency for unhealthy model with null latency', () => {
      render(<ModelHealthIndicator {...defaultProps} health={mockUnhealthyResponse} />);

      // Embedding model has null latency, generation model has 450ms
      expect(screen.queryByText('null')).not.toBeInTheDocument();
      expect(screen.getByText('450ms')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should display loading message when isLoading is true and no health data', () => {
      render(
        <ModelHealthIndicator
          {...defaultProps}
          health={undefined}
          isLoading={true}
        />
      );

      expect(screen.getByText('Loading health status...')).toBeInTheDocument();
    });

    it('should display health data when available even if loading', () => {
      render(
        <ModelHealthIndicator
          {...defaultProps}
          isLoading={true}
        />
      );

      // Should show health data, not loading message
      expect(screen.queryByText('Loading health status...')).not.toBeInTheDocument();
      expect(screen.getByText('text-embedding-3-small')).toBeInTheDocument();
    });
  });

  describe('Refresh Button', () => {
    it('should render Test Connection button', () => {
      render(<ModelHealthIndicator {...defaultProps} />);

      expect(screen.getByRole('button', { name: /test connection/i })).toBeInTheDocument();
    });

    it('should call onRefresh when button is clicked', async () => {
      const mockOnRefresh = vi.fn().mockResolvedValue(undefined);
      render(<ModelHealthIndicator {...defaultProps} onRefresh={mockOnRefresh} />);

      const button = screen.getByRole('button', { name: /test connection/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalledTimes(1);
      });
    });

    it('should disable button when isRefreshing is true', () => {
      render(<ModelHealthIndicator {...defaultProps} isRefreshing={true} />);

      const button = screen.getByRole('button', { name: /test connection/i });
      expect(button).toBeDisabled();
    });

    it('should disable button when isLoading is true', () => {
      render(
        <ModelHealthIndicator
          {...defaultProps}
          health={undefined}
          isLoading={true}
        />
      );

      const button = screen.getByRole('button', { name: /test connection/i });
      expect(button).toBeDisabled();
    });

    it('should display error message when refresh fails', async () => {
      const mockOnRefresh = vi.fn().mockRejectedValue(new Error('Network error'));
      render(<ModelHealthIndicator {...defaultProps} onRefresh={mockOnRefresh} />);

      const button = screen.getByRole('button', { name: /test connection/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Latency Color Coding', () => {
    it('should show green color for fast latency (<500ms)', () => {
      const fastHealth: LLMHealthResponse = {
        ...mockHealthyResponse,
        embedding_health: {
          ...mockHealthyResponse.embedding_health!,
          latency_ms: 100,
        },
      };
      render(<ModelHealthIndicator {...defaultProps} health={fastHealth} />);

      const latencyElement = screen.getByText('100ms');
      expect(latencyElement).toHaveClass('text-green-600');
    });

    it('should show yellow color for medium latency (500-999ms)', () => {
      const mediumHealth: LLMHealthResponse = {
        ...mockHealthyResponse,
        embedding_health: {
          ...mockHealthyResponse.embedding_health!,
          latency_ms: 750,
        },
      };
      render(<ModelHealthIndicator {...defaultProps} health={mediumHealth} />);

      const latencyElement = screen.getByText('750ms');
      expect(latencyElement).toHaveClass('text-yellow-600');
    });

    it('should show orange color for slow latency (>=1000ms)', () => {
      const slowHealth: LLMHealthResponse = {
        ...mockHealthyResponse,
        embedding_health: {
          ...mockHealthyResponse.embedding_health!,
          latency_ms: 1500,
        },
      };
      render(<ModelHealthIndicator {...defaultProps} health={slowHealth} />);

      const latencyElement = screen.getByText('1500ms');
      expect(latencyElement).toHaveClass('text-orange-600');
    });
  });

  describe('No Health Data', () => {
    it('should not display badges when no health data available', () => {
      render(
        <ModelHealthIndicator
          {...defaultProps}
          health={undefined}
          isLoading={false}
        />
      );

      expect(screen.queryByText('All Healthy')).not.toBeInTheDocument();
      expect(screen.queryByText('Issues Detected')).not.toBeInTheDocument();
    });
  });
});
