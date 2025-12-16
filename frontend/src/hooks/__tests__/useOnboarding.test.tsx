import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOnboarding } from '../useOnboarding';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ReactNode } from 'react';

// Mock auth store
const mockSetUser = vi.fn();
vi.mock('@/lib/stores/auth-store', () => ({
  useUser: vi.fn(() => ({ onboarding_completed: false })),
  useAuthStore: vi.fn((selector) =>
    selector({
      setUser: mockSetUser,
    })
  ),
}));

describe('useOnboarding', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('returns isOnboardingComplete from user state', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });

    expect(result.current.isOnboardingComplete).toBe(false);
  });

  it('markOnboardingComplete calls PUT /api/v1/users/me/onboarding', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ onboarding_completed: true }),
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOnboarding(), { wrapper });

    await result.current.markOnboardingComplete();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/users/me/onboarding',
      expect.objectContaining({
        method: 'PUT',
        credentials: 'include',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('markOnboardingComplete invalidates user query on success', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ onboarding_completed: true }),
    });
    global.fetch = mockFetch;

    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useOnboarding(), { wrapper });

    await result.current.markOnboardingComplete();

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['user'] });
    });
  });

  it('handles API errors gracefully', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Authentication required' }),
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOnboarding(), { wrapper });

    await expect(result.current.markOnboardingComplete()).rejects.toThrow(
      'Authentication required'
    );
  });

  it('returns isLoading state during mutation', async () => {
    const mockFetch = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                text: async () => JSON.stringify({}),
              }),
            100
          )
        )
    );
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOnboarding(), { wrapper });

    // Start mutation (don't await)
    result.current.markOnboardingComplete();

    // Check isLoading is true during mutation
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true);
    });
  });

  it('returns error state on API failure', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOnboarding(), { wrapper });

    try {
      await result.current.markOnboardingComplete();
    } catch {
      // Expected error
    }

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });
});
