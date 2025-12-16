'use client';

import { Activity, Database, FileText, HardDrive, Search, Users } from 'lucide-react';

import { StatCard } from '@/components/admin/stat-card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminStats } from '@/hooks/useAdminStats';

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round(bytes / Math.pow(k, i) * 100) / 100} ${sizes[i]}`;
}

export default function AdminDashboardPage() {
  const { data: stats, isLoading, error } = useAdminStats();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Failed to load statistics'}
          </p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
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

      <section>
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
    </div>
  );
}
