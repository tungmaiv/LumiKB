/**
 * Redirect: /admin/queue -> /operations/queue
 * Story 7.11: Navigation Restructure
 *
 * This route is maintained for backwards compatibility.
 * Bookmarks and deep links to /admin/queue will redirect to /operations/queue.
 */

import { redirect } from 'next/navigation';

export default function AdminQueueRedirectPage() {
  redirect('/operations/queue');
}
