/**
 * Admin layout with AdminGuard for route-level access control
 * Story 5.18: User Management UI (AC-5.18.6)
 *
 * Ensures all admin pages require is_superuser=true.
 */

import { AdminGuard } from '@/components/auth/admin-guard';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminGuard>{children}</AdminGuard>;
}
