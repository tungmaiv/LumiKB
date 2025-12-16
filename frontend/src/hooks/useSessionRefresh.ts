'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { refreshSession } from '@/lib/api/auth';
import { SESSION_EXPIRED_EVENT } from '@/lib/api/client';

// Configuration for session refresh behavior
const SESSION_REFRESH_CONFIG = {
  // How often to check if session needs refresh (5 minutes)
  CHECK_INTERVAL_MS: 5 * 60 * 1000,

  // Minimum time between refresh attempts (to prevent rapid-fire refreshes)
  MIN_REFRESH_INTERVAL_MS: 2 * 60 * 1000,

  // If user is idle for this long, stop refreshing (let session expire)
  IDLE_THRESHOLD_MS: 30 * 60 * 1000, // 30 minutes

  // Debounce time for activity tracking
  ACTIVITY_DEBOUNCE_MS: 1000,
};

/**
 * Hook that implements sliding session behavior.
 *
 * While the user is actively using the application, this hook periodically
 * refreshes the session to prevent JWT timeout. If the user becomes idle
 * for longer than IDLE_THRESHOLD_MS, the session is allowed to expire naturally.
 *
 * The hook tracks user activity via:
 * - Mouse movements
 * - Keyboard events
 * - Touch events
 * - Scroll events
 * - Focus events
 *
 * It also listens for SESSION_EXPIRED_EVENT from the API client to handle
 * cases where the session expires between checks (e.g., browser was closed).
 */
export function useSessionRefresh(): void {
  const { isAuthenticated, clearUser } = useAuthStore();

  // Track timestamps for refresh logic
  const lastActivityRef = useRef<number>(Date.now());
  const lastRefreshRef = useRef<number>(0);
  const isRefreshingRef = useRef<boolean>(false);

  // Update activity timestamp (debounced via requestAnimationFrame)
  const updateActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
  }, []);

  // Attempt to refresh session
  const attemptRefresh = useCallback(async () => {
    // Guard against concurrent refreshes
    if (isRefreshingRef.current) {
      return;
    }

    // Check if enough time has passed since last refresh
    const now = Date.now();
    const timeSinceLastRefresh = now - lastRefreshRef.current;
    if (timeSinceLastRefresh < SESSION_REFRESH_CONFIG.MIN_REFRESH_INTERVAL_MS) {
      return;
    }

    // Check if user is idle (no activity for IDLE_THRESHOLD_MS)
    const timeSinceActivity = now - lastActivityRef.current;
    if (timeSinceActivity > SESSION_REFRESH_CONFIG.IDLE_THRESHOLD_MS) {
      // User is idle - don't refresh, let session expire naturally
      return;
    }

    isRefreshingRef.current = true;

    try {
      await refreshSession();
      lastRefreshRef.current = Date.now();
    } catch {
      // Refresh failed - likely session expired
      // The 401 handler in client.ts will dispatch SESSION_EXPIRED_EVENT
      // No need to handle here, just log silently
    } finally {
      isRefreshingRef.current = false;
    }
  }, []);

  // Handle session expired event from API client
  useEffect(() => {
    const handleSessionExpired = () => {
      // Clear auth state and let auth guard redirect to login
      clearUser();
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);

    return () => {
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, [clearUser]);

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    // Activity events to track
    const events = [
      'mousemove',
      'mousedown',
      'keydown',
      'touchstart',
      'scroll',
      'focus',
    ] as const;

    // Throttled activity handler
    let rafId: number | null = null;
    const handleActivity = () => {
      if (rafId === null) {
        rafId = requestAnimationFrame(() => {
          updateActivity();
          rafId = null;
        });
      }
    };

    // Add listeners
    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [isAuthenticated, updateActivity]);

  // Periodic session refresh check
  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    // Initial refresh on mount (ensures fresh session on page load)
    // Only if we haven't refreshed recently
    const timeSinceLastRefresh = Date.now() - lastRefreshRef.current;
    if (timeSinceLastRefresh > SESSION_REFRESH_CONFIG.MIN_REFRESH_INTERVAL_MS) {
      attemptRefresh();
    }

    // Set up periodic check
    const intervalId = setInterval(() => {
      attemptRefresh();
    }, SESSION_REFRESH_CONFIG.CHECK_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [isAuthenticated, attemptRefresh]);

  // Refresh on visibility change (when user returns to tab)
  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // User returned to tab - update activity and try refresh
        updateActivity();
        attemptRefresh();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, updateActivity, attemptRefresh]);
}
