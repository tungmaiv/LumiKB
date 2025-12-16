/**
 * Admin Dashboard - Hub page for administrative tasks
 *
 * AC-7.11.5: Admin dropdown displays this as hub
 * AC-7.11.6: Card-based hub with links to admin-only sub-sections
 *
 * Available to Administrators (level 3) only
 * Note: Operational tools (audit, queue, kb-stats) moved to /operations section
 */
'use client';

import Link from 'next/link';
import { Activity, BarChart3, Cpu, Database, FileText, HardDrive, MessageCircle, Search, Users, Users2, Server, Settings, Shield, Workflow } from 'lucide-react';

import { StatCard } from '@/components/admin/stat-card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminStats } from '@/hooks/useAdminStats';
import { formatBytes } from '@/lib/utils';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

export default function AdminDashboardPage() {
  const { data: stats, isLoading, error } = useAdminStats();

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
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
          <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load statistics'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!stats) {
    return <DashboardLayout><div className="container mx-auto p-6" /></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Server className="h-8 w-8" />
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          System-wide statistics and metrics
        </p>
      </div>

      {/* User Statistics */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Users</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Total Users"
            value={stats.users.total}
            description="All registered users"
            icon={Users}
          />
          <StatCard
            title="Active Users"
            value={stats.users.active}
            description="Active in last 30 days"
            icon={Users}
          />
          <StatCard
            title="Inactive Users"
            value={stats.users.inactive}
            description="No activity in 30+ days"
            icon={Users}
          />
        </div>
      </section>

      {/* Knowledge Base & Document Statistics */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Content</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Knowledge Bases"
            value={stats.knowledge_bases.total}
            description={`Active: ${stats.knowledge_bases.by_status.active || 0}`}
            icon={Database}
          />
          <StatCard
            title="Total Documents"
            value={stats.documents.total}
            description={`Ready: ${stats.documents.by_status.READY || 0}`}
            icon={FileText}
          />
          <StatCard
            title="Storage Used"
            value={formatBytes(stats.storage.total_bytes)}
            description={`Avg: ${formatBytes(stats.storage.avg_doc_size_bytes)}`}
            icon={HardDrive}
          />
          <StatCard
            title="Failed Documents"
            value={stats.documents.by_status.FAILED || 0}
            description={`Pending: ${stats.documents.by_status.PENDING || 0}`}
            icon={FileText}
          />
        </div>
      </section>

      {/* Activity Statistics */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Activity</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Searches (24h)"
            value={stats.activity.searches.last_24h}
            description={`7d: ${stats.activity.searches.last_7d} | 30d: ${stats.activity.searches.last_30d}`}
            icon={Search}
            trend={stats.trends.searches}
            trendColor="#10b981"
          />
          <StatCard
            title="Searches (7d)"
            value={stats.activity.searches.last_7d}
            description={`30d: ${stats.activity.searches.last_30d}`}
            icon={Search}
            trend={stats.trends.searches}
            trendColor="#10b981"
          />
          <StatCard
            title="Searches (30d)"
            value={stats.activity.searches.last_30d}
            description="Last 30 days"
            icon={Search}
            trend={stats.trends.searches}
            trendColor="#10b981"
          />
        </div>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Generations</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Generations (24h)"
            value={stats.activity.generations.last_24h}
            description={`7d: ${stats.activity.generations.last_7d} | 30d: ${stats.activity.generations.last_30d}`}
            icon={Activity}
            trend={stats.trends.generations}
            trendColor="#8b5cf6"
          />
          <StatCard
            title="Generations (7d)"
            value={stats.activity.generations.last_7d}
            description={`30d: ${stats.activity.generations.last_30d}`}
            icon={Activity}
            trend={stats.trends.generations}
            trendColor="#8b5cf6"
          />
          <StatCard
            title="Generations (30d)"
            value={stats.activity.generations.last_30d}
            description="Last 30 days"
            icon={Activity}
            trend={stats.trends.generations}
            trendColor="#8b5cf6"
          />
        </div>
      </section>

      {/* Admin Tools - Admin-only functionality */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Admin Tools</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Link href="/admin/users">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900">
                  <Users className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">User Management</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    View, create, and manage user accounts
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/groups">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-100 dark:bg-teal-900">
                  <Users2 className="h-6 w-6 text-teal-600 dark:text-teal-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Group Management</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Organize users into groups for permissions
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/kb-permissions">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900">
                  <Shield className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">KB Permissions</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Manage user and group access to Knowledge Bases
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/config">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Settings className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">System Configuration</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Manage system-wide settings and configuration
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/models">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-100 dark:bg-cyan-900">
                  <Cpu className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Model Registry</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Manage embedding and generation models
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/traces">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-rose-100 dark:bg-rose-900">
                  <Workflow className="h-6 w-6 text-rose-600 dark:text-rose-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Trace Viewer</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    View and analyze distributed traces
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/chat-history">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-sky-100 dark:bg-sky-900">
                  <MessageCircle className="h-6 w-6 text-sky-600 dark:text-sky-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Chat History</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Browse and analyze user conversations
                  </p>
                </div>
              </div>
            </div>
          </Link>
          <Link href="/admin/observability">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer dark:bg-gray-900 dark:border-gray-700">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900">
                  <BarChart3 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Observability</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Monitor LLM usage, processing, and system health
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
