/**
 * Redirect: /admin/kb-stats -> /operations/kb-stats
 * Story 7.11: Navigation Restructure
 *
 * This route is maintained for backwards compatibility.
 * Bookmarks and deep links to /admin/kb-stats will redirect to /operations/kb-stats.
 * Query parameters (like ?kb_id=xxx) are preserved in the redirect.
 */

'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function AdminKBStatsRedirectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Preserve query parameters in the redirect
    const kbId = searchParams.get('kb_id');
    const targetUrl = kbId
      ? `/operations/kb-stats?kb_id=${kbId}`
      : '/operations/kb-stats';
    router.replace(targetUrl);
  }, [router, searchParams]);

  return null;
}
