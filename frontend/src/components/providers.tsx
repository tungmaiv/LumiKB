'use client';

import { useEffect, useRef } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useSessionRefresh } from '@/hooks/useSessionRefresh';

interface ProvidersProps {
  children: React.ReactNode;
}

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

export function Providers({ children }: ProvidersProps) {
  const checkAuth = useAuthStore((state) => state.checkAuth);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const queryClient = getQueryClient();
  const prevAuthRef = useRef<boolean | null>(null);

  // Check authentication state on app mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Session refresh hook - keeps session alive while user is active
  // This implements sliding sessions to prevent JWT timeout during active use
  useSessionRefresh();

  // Clear query cache when authentication state changes (login/logout)
  // This ensures stale data from previous sessions doesn't persist
  useEffect(() => {
    if (prevAuthRef.current !== null && prevAuthRef.current !== isAuthenticated) {
      // Auth state changed - clear all cached queries
      queryClient.clear();
    }
    prevAuthRef.current = isAuthenticated;
  }, [isAuthenticated, queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={0}>
        {children}
        <Toaster position="top-right" richColors closeButton />
      </TooltipProvider>
    </QueryClientProvider>
  );
}
