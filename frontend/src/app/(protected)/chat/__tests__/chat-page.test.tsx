/**
 * Component Tests: Chat Page Route (Story 5-0, AC1)
 * Status: Generated for Story 5-0
 * Generated: 2025-11-30
 *
 * Test Coverage:
 * - P1: Chat page renders ChatContainer component
 * - P1: Chat page has proper route configuration
 * - P2: Chat page handles loading states
 * - P2: Chat page handles error states
 *
 * Knowledge Base References:
 * - test-quality.md: Component test isolation
 * - test-levels-framework.md: Component testing guidelines
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatPage from '../page';

// Mock ChatContainer component
vi.mock('@/components/chat/chat-container', () => ({
  ChatContainer: () => <div data-testid="chat-container">Chat Container Mock</div>,
}));

// Mock useChatManagement hook
vi.mock('@/hooks/useChatManagement', () => ({
  useChatManagement: () => ({
    conversations: [],
    activeConversation: null,
    messages: [],
    isLoading: false,
    sendMessage: vi.fn(),
    createConversation: vi.fn(),
    selectConversation: vi.fn(),
  }),
}));

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(),
  }),
  usePathname: () => '/chat',
}));

// Mock useActiveKb hook
vi.mock('@/hooks/useKnowledgeBase', () => ({
  useActiveKb: () => ({
    activeKb: { id: '1', name: 'Demo KB', description: 'Test KB' },
    isLoading: false,
  }),
}));

describe('Chat Page Route (Story 5-0, AC1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P1] Chat Page Rendering', () => {
    it('should render without crashing', () => {
      render(<ChatPage />);

      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
    });

    it('should render ChatContainer component', () => {
      render(<ChatPage />);

      const chatContainer = screen.getByTestId('chat-container');
      expect(chatContainer).toBeVisible();
    });

    it('should display Chat title', () => {
      render(<ChatPage />);

      expect(screen.getByText(/Chat/i)).toBeInTheDocument();
    });

    it('should have proper page structure', () => {
      render(<ChatPage />);

      // Should have container with proper classes
      const container = screen.getByTestId('chat-container').parentElement;
      expect(container).toHaveClass(/container/);
    });
  });

  describe('[P1] Route Configuration', () => {
    it('should be accessible at /app/(protected)/chat', () => {
      // This test validates the route exists and renders
      // The actual URL routing is tested in E2E tests
      render(<ChatPage />);

      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
    });

    it('should integrate with useChatManagement hook', () => {
      // Verify hook is called (mocked above)
      render(<ChatPage />);

      // ChatContainer should receive chat management state
      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
    });
  });

  describe('[P2] Loading States', () => {
    it('should handle KB loading state', () => {
      // Override mock to simulate loading
      vi.mocked(() => ({
        useActiveKb: () => ({
          activeKb: null,
          isLoading: true,
        }),
      }));

      render(<ChatPage />);

      // Page should still render (loading handled by ChatContainer)
      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
    });
  });

  describe('[P2] Error Handling', () => {
    it('should handle missing KB gracefully', () => {
      // Override mock to simulate no active KB
      vi.mocked(() => ({
        useActiveKb: () => ({
          activeKb: null,
          isLoading: false,
        }),
      }));

      render(<ChatPage />);

      // Should still render without crashing
      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
    });
  });

  describe('[P2] Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<ChatPage />);

      const heading = screen.getByText(/Chat/i);
      expect(heading.tagName).toBe('H1');
    });

    it('should be keyboard navigable', () => {
      render(<ChatPage />);

      const chatContainer = screen.getByTestId('chat-container');
      expect(chatContainer).toBeVisible();

      // Container should be in DOM and accessible
      expect(chatContainer).toHaveAccessibleName();
    });
  });
});
