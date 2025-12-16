/**
 * Redirect: /admin/audit -> /operations/audit
 * Story 7.11: Navigation Restructure
 *
 * This route is maintained for backwards compatibility.
 * Bookmarks and deep links to /admin/audit will redirect to /operations/audit.
 */

import { redirect } from 'next/navigation';

export default function AdminAuditRedirectPage() {
  redirect('/operations/audit');
}
