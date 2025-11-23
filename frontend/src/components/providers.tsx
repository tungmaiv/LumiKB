'use client';

import { useEffect } from 'react';
import { Toaster } from '@/components/ui/sonner';
import { useAuthStore } from '@/lib/stores/auth-store';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  // Check authentication state on app mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <>
      {children}
      <Toaster position="top-right" richColors closeButton />
    </>
  );
}
