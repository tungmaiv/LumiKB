/**
 * Permission Gate component for UI-level permission control
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * AC-7.11.12: Gating for Operator-level UI elements
 * AC-7.11.13: Gating for Administrator-level UI elements
 *
 * Usage:
 *   <PermissionGate level={PermissionLevel.OPERATOR}>
 *     <Button>Upload Document</Button>
 *   </PermissionGate>
 *
 *   <PermissionGate level={PermissionLevel.ADMINISTRATOR} fallback={<DisabledButton />}>
 *     <Button>Delete KB</Button>
 *   </PermissionGate>
 */

'use client';

import { type ReactNode } from 'react';
import { PermissionLevel } from '@/types/user';
import { useHasPermission } from '@/lib/stores/auth-store';

export interface PermissionGateProps {
  /** Minimum permission level required to render children */
  level: PermissionLevel;
  /** Content to render when user has permission */
  children: ReactNode;
  /** Optional fallback content when user lacks permission (defaults to null) */
  fallback?: ReactNode;
}

/**
 * Conditionally renders children based on user's permission level.
 * Uses cumulative permission model: higher levels inherit all lower permissions.
 */
export function PermissionGate({
  level,
  children,
  fallback = null,
}: PermissionGateProps) {
  const hasPermission = useHasPermission(level);

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Convenience component for Operator-level gating (level 2+)
 * AC-7.11.12: Upload/delete documents, create KBs
 */
export function OperatorGate({
  children,
  fallback = null,
}: Omit<PermissionGateProps, 'level'>) {
  return (
    <PermissionGate level={PermissionLevel.OPERATOR} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

/**
 * Convenience component for Administrator-level gating (level 3)
 * AC-7.11.13: Full access including KB deletion, user management
 */
export function AdminGate({
  children,
  fallback = null,
}: Omit<PermissionGateProps, 'level'>) {
  return (
    <PermissionGate level={PermissionLevel.ADMINISTRATOR} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}
