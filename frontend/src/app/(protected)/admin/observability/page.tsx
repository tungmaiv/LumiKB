/**
 * Observability Dashboard Page
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Admin page for monitoring:
 * - LLM usage and costs
 * - Document processing pipeline
 * - Chat activity
 * - System health
 */

import { ObservabilityDashboard } from '@/components/admin/observability-dashboard';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

export default function ObservabilityPage() {
  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <ObservabilityDashboard initialPeriod="day" refreshInterval={30000} />
      </div>
    </DashboardLayout>
  );
}
