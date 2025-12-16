/**
 * Admin Guard component for route-level admin access control
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * AC-7.11.17-18: Ensures only users with ADMINISTRATOR level (3) can access admin pages.
 * Non-admin users are redirected to the dashboard.
 *
 * Uses permission_level instead of is_superuser for RBAC compliance.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, ShieldAlert } from 'lucide-react';
import { useAuthStore, useIsAdministrator } from '@/lib/stores/auth-store';

interface AdminGuardProps {
  children: React.ReactNode;
}

export function AdminGuard({ children }: AdminGuardProps) {
  const router = useRouter();
  const { isLoading, isAuthenticated } = useAuthStore();
  const isAdmin = useIsAdministrator();

  useEffect(() => {
    // Wait for auth check to complete
    if (isLoading) return;

    // If not authenticated, AuthGuard will handle redirect to login
    if (!isAuthenticated) return;

    // If authenticated but not admin, redirect to dashboard
    if (!isAdmin) {
      router.replace('/dashboard');
    }
  }, [isLoading, isAuthenticated, isAdmin, router]);

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
  if (!isAdmin && isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <ShieldAlert className="h-12 w-12 text-destructive" />
          <h1 className="text-xl font-semibold">Access Denied</h1>
          <p className="text-sm text-muted-foreground">
            You do not have permission to access this page.
          </p>
          <p className="text-xs text-muted-foreground">
            Administrator access (level 3) is required.
          </p>
        </div>
      </div>
    );
  }

  // Render children for admin users
  return <>{children}</>;
}
