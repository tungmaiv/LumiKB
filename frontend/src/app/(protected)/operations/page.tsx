'use client';

import Link from 'next/link';
import { Activity, Database, FileSearch, Wrench } from 'lucide-react';

import { StatCard } from '@/components/admin/stat-card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminStats } from '@/hooks/useAdminStats';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

/**
 * Operations Dashboard - Hub page for operational tasks
 *
 * AC-7.11.4: Operations dropdown displays this as hub
 * AC-7.11.6: Card-based hub with links to all sub-sections
 *
 * Available to Operators (level 2+) and Administrators (level 3)
 */
export default function OperationsDashboardPage() {
  const { data: stats, isLoading, error } = useAdminStats();

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Operations Dashboard</h1>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Operations Dashboard</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load statistics'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <Wrench className="h-8 w-8" />
            <h1 className="text-2xl font-bold">Operations Dashboard</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor system operations, audit logs, and processing queues
          </p>
        </div>

        {/* Quick Stats */}
        {stats && (
          <section className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Quick Stats</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Processing Queue"
                value={stats.documents.by_status.PENDING || 0}
                description={`Failed: ${stats.documents.by_status.FAILED || 0}`}
                icon={Activity}
              />
              <StatCard
                title="Knowledge Bases"
                value={stats.knowledge_bases.total}
                description={`Active: ${stats.knowledge_bases.by_status.active || 0}`}
                icon={Database}
              />
              <StatCard
                title="Ready Documents"
                value={stats.documents.by_status.READY || 0}
                description={`Total: ${stats.documents.total}`}
                icon={Database}
              />
              <StatCard
                title="Searches (24h)"
                value={stats.activity.searches.last_24h}
                description={`7d: ${stats.activity.searches.last_7d}`}
                icon={FileSearch}
              />
            </div>
          </section>
        )}

        {/* Operations Tools */}
        <section>
          <h2 className="text-xl font-semibold mb-4">Operations Tools</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Link href="/operations/audit">
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900">
                    <FileSearch className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">Audit Logs</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      View system audit logs and security events
                    </p>
                  </div>
                </div>
              </div>
            </Link>
            <Link href="/operations/queue">
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900">
                    <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      Processing Queue
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Monitor background task processing queues
                    </p>
                  </div>
                </div>
              </div>
            </Link>
            <Link href="/operations/kb-stats">
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900">
                    <Database className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      KB Statistics
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      View detailed statistics for knowledge bases
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
