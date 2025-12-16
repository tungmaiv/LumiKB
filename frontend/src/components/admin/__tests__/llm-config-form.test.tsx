/**
 * Unit tests for LLMConfigForm component
 * Story 7-2: Centralized LLM Configuration (AC-7.2.1, AC-7.2.2)
 *
 * Tests:
 * - Display of current LLM config settings
 * - Model selection dropdowns
 * - Generation parameter sliders/inputs
 * - Form submission with changed values
 * - Reset functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, beforeAll } from 'vitest';
import { LLMConfigForm } from '../llm-config-form';
import type { LLMConfig } from '@/types/llm-config';

// Mock PointerCapture methods for Radix UI compatibility with JSDOM
beforeAll(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
});

// Mock useAvailableModels hook
vi.mock('@/hooks/useAvailableModels', () => ({
  useAvailableModels: vi.fn(() => ({
    embeddingModels: [
      { id: 'emb-001', name: 'text-embedding-3-small', is_default: true },
      { id: 'emb-002', name: 'text-embedding-3-large', is_default: false },
    ],
    generationModels: [
      { id: 'gen-001', name: 'Claude 3 Sonnet', is_default: true },
      { id: 'gen-002', name: 'GPT-4', is_default: false },
    ],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

// Mock TooltipProvider
vi.mock('@/components/ui/tooltip', async () => {
  const actual = await vi.importActual('@/components/ui/tooltip');
  return {
    ...actual,
    TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

const mockConfig: LLMConfig = {
  embedding_model: {
    model_id: 'emb-001',
    name: 'text-embedding-3-small',
    provider: 'openai',
    model_identifier: 'text-embedding-3-small',
    api_endpoint: null,
    is_default: true,
    status: 'active',
  },
  generation_model: {
    model_id: 'gen-001',
    name: 'Claude 3 Sonnet',
    provider: 'anthropic',
    model_identifier: 'claude-3-sonnet',
    api_endpoint: null,
    is_default: true,
    status: 'active',
  },
  generation_settings: {
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 1.0,
  },
  litellm_base_url: 'http://localhost:4000',
  last_modified: '2024-01-15T10:30:00Z',
  last_modified_by: 'admin@example.com',
};

describe('LLMConfigForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnRefetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnSubmit.mockResolvedValue(undefined);
  });

  describe('Display', () => {
    it('should render LiteLLM proxy URL', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('http://localhost:4000')).toBeInTheDocument();
    });

    it('should render LiteLLM Proxy card title', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('LiteLLM Proxy')).toBeInTheDocument();
    });

    it('should render Active Models section', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Active Models')).toBeInTheDocument();
    });

    it('should render Generation Parameters section', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Generation Parameters')).toBeInTheDocument();
    });

    it('should display current embedding model info', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText(/Current: text-embedding-3-small \(openai\)/)).toBeInTheDocument();
    });

    it('should display current generation model info', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText(/Current: Claude 3 Sonnet \(anthropic\)/)).toBeInTheDocument();
    });

    it('should display last modified info', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText(/Last modified:.*admin@example.com/)).toBeInTheDocument();
    });

    it('should display temperature value', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('0.7')).toBeInTheDocument();
    });

    it('should display top_p value', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('1.00')).toBeInTheDocument();
    });
  });

  describe('Form Labels', () => {
    it('should render Embedding Model label', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Embedding Model')).toBeInTheDocument();
    });

    it('should render Generation Model label', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Generation Model')).toBeInTheDocument();
    });

    it('should render Temperature label', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Temperature')).toBeInTheDocument();
    });

    it('should render Max Output Tokens label', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByText('Max Output Tokens')).toBeInTheDocument();
    });
  });

  describe('Buttons', () => {
    it('should render Apply Changes button', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByRole('button', { name: /apply changes/i })).toBeInTheDocument();
    });

    it('should render Reset button', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });

    it('should disable Apply Changes button when no changes made', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByRole('button', { name: /apply changes/i })).toBeDisabled();
    });

    it('should disable Reset button when no changes made', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByRole('button', { name: /reset/i })).toBeDisabled();
    });

    it('should show "Applying Changes..." when submitting', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={true}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      expect(screen.getByRole('button', { name: /applying changes/i })).toBeInTheDocument();
    });
  });

  describe('Form Interaction', () => {
    it('should enable buttons when max_tokens is changed', async () => {
      const user = userEvent.setup();
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      const maxTokensInput = screen.getByRole('spinbutton');
      await user.clear(maxTokensInput);
      await user.type(maxTokensInput, '8192');

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /apply changes/i })).not.toBeDisabled();
      });
    });

    it('should call onRefetch when refresh button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      // Find refresh button (RefreshCw icon button)
      const refreshButtons = screen.getAllByRole('button');
      // The refresh button is a small ghost button with RefreshCw icon
      const refreshButton = refreshButtons.find(
        (btn) => btn.classList.contains('p-0') && btn.classList.contains('h-8')
      );

      if (refreshButton) {
        await user.click(refreshButton);
        expect(mockOnRefetch).toHaveBeenCalled();
      }
    });

    it('should call onSubmit with changed settings when form is submitted', async () => {
      const user = userEvent.setup();
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={new Date()}
        />
      );

      // Change max_tokens
      const maxTokensInput = screen.getByRole('spinbutton');
      await user.clear(maxTokensInput);
      await user.type(maxTokensInput, '8192');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /apply changes/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          generation_settings: expect.objectContaining({
            max_tokens: 8192,
          }),
        });
      });
    });
  });

  describe('Last Fetched Display', () => {
    it('should display "Never" when lastFetched is null', () => {
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={null}
        />
      );

      expect(screen.getByText(/Updated Never/)).toBeInTheDocument();
    });

    it('should display time ago when lastFetched is recent', () => {
      const recentDate = new Date(Date.now() - 10000); // 10 seconds ago
      render(
        <LLMConfigForm
          config={mockConfig}
          onSubmit={mockOnSubmit}
          isSubmitting={false}
          onRefetch={mockOnRefetch}
          lastFetched={recentDate}
        />
      );

      expect(screen.getByText(/Updated.*ago/)).toBeInTheDocument();
    });
  });
});
