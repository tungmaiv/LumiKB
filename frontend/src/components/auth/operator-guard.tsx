/**
 * Operator Guard component for route-level operator access control
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * AC-7.11.16: Ensures only users with OPERATOR level (2+) can access operator pages.
 * Non-operator users are redirected to the dashboard.
 *
 * Uses permission_level instead of is_superuser for RBAC compliance.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, ShieldAlert } from 'lucide-react';
import { useAuthStore, useIsOperator } from '@/lib/stores/auth-store';

interface OperatorGuardProps {
  children: React.ReactNode;
}

export function OperatorGuard({ children }: OperatorGuardProps) {
  const router = useRouter();
  const { isLoading, isAuthenticated } = useAuthStore();
  const isOperator = useIsOperator();

  useEffect(() => {
    // Wait for auth check to complete
    if (isLoading) return;

    // If not authenticated, AuthGuard will handle redirect to login
    if (!isAuthenticated) return;

    // If authenticated but not operator level, redirect to dashboard
    if (!isOperator) {
      router.replace('/dashboard');
    }
  }, [isLoading, isAuthenticated, isOperator, router]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Verifying access...</p>
        </div>
      </div>
    );
  }

  // Show access denied briefly before redirect
  if (!isOperator && isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <ShieldAlert className="h-12 w-12 text-destructive" />
          <h1 className="text-xl font-semibold">Access Denied</h1>
          <p className="text-sm text-muted-foreground">
            You do not have permission to access this page.
          </p>
          <p className="text-xs text-muted-foreground">Operator access (level 2+) is required.</p>
        </div>
      </div>
    );
  }

  // Render children for operator-level users
  return <>{children}</>;
}
