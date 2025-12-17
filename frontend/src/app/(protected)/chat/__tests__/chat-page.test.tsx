/**
 * Component Tests: Chat Page Route (Story 5-0, AC1)
 * Status: Generated for Story 5-0
 * Generated: 2025-11-30
 *
 * Test Coverage:
 * - P1: Chat page renders correctly
 * - P1: Chat page handles KB selection state
 * - P2: Chat page input functionality
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatPage from '../page';

// Mock scrollIntoView - JSDOM doesn't implement it
Element.prototype.scrollIntoView = vi.fn();

// Mock kb-store
vi.mock('@/lib/stores/kb-store', () => ({
  useActiveKb: vi.fn(),
}));

import { useActiveKb } from '@/lib/stores/kb-store';

const mockUseActiveKb = vi.mocked(useActiveKb);

describe('Chat Page Route (Story 5-0, AC1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: active KB is selected
    mockUseActiveKb.mockReturnValue({
      id: 'kb-1',
      name: 'Demo KB',
      description: 'Test knowledge base',
    } as ReturnType<typeof useActiveKb>);
  });

  describe('[P1] Chat Page Rendering', () => {
    it('should render without crashing', () => {
      render(<ChatPage />);

      // Should show the KB name in the title
      expect(screen.getByText(/Chat with Demo KB/i)).toBeInTheDocument();
    });

    it('should display chat input area', () => {
      render(<ChatPage />);

      // Should have text input
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should display empty state message', () => {
      render(<ChatPage />);

      // Initial state shows prompt
      expect(screen.getByText(/ask a question about this knowledge base/i)).toBeInTheDocument();
    });
  });

  describe('[P1] KB Selection State', () => {
    it('should show select KB message when no KB active', () => {
      mockUseActiveKb.mockReturnValue(null);

      render(<ChatPage />);

      // Should prompt to select a KB
      expect(screen.getByText(/please select a knowledge base/i)).toBeInTheDocument();
    });

    it('should render chat interface when KB is active', () => {
      render(<ChatPage />);

      // Should show KB name and chat interface
      expect(screen.getByText(/Chat with Demo KB/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    });
  });

  describe('[P2] Input Functionality', () => {
    it('should allow typing in chat input', async () => {
      render(<ChatPage />);

      const textarea = screen.getByPlaceholderText(/ask a question/i);
      await userEvent.type(textarea, 'Test message');

      expect(textarea).toHaveValue('Test message');
    });

    it('should have send button', () => {
      render(<ChatPage />);

      // Find button with send icon (no text, just icon)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should disable send button when input is empty', () => {
      render(<ChatPage />);

      // Find the send button (it's the button without text)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1]; // Send button is usually last

      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has text', async () => {
      render(<ChatPage />);

      const textarea = screen.getByPlaceholderText(/ask a question/i);
      await userEvent.type(textarea, 'Test message');

      // Find the send button
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];

      await waitFor(() => {
        expect(sendButton).not.toBeDisabled();
      });
    });
  });
});
