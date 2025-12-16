/**
 * KB Statistics Page (Operations section)
 *
 * Displays detailed statistics for knowledge bases:
 * - Document and storage metrics
 * - Usage metrics (searches, generations, users)
 * - Top accessed documents
 *
 * Story 7.11: Navigation Restructure - moved to /operations/kb-stats
 * Available to Operators (level 2+)
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Database, FileText, HardDrive, Search, FileSearch, Users, TrendingUp } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { StatCard } from '@/components/admin/stat-card';
import { useKBStats } from '@/hooks/useKBStats';
import { formatBytes } from '@/lib/utils';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { useKBStore } from '@/lib/stores/kb-store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  status: string;
}

export default function OperationsKBStatsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [kbId, setKbId] = useState<string | null>(searchParams.get('kb_id'));
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loadingKBs, setLoadingKBs] = useState(true);

  // KB store for sidebar sync
  const { kbs: storeKbs, activeKb, setActiveKb, fetchKbs } = useKBStore();

  const { data: stats, isLoading, error } = useKBStats(kbId);

  // Fetch available knowledge bases for selector
  useEffect(() => {
    const fetchKnowledgeBases = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/`, {
          credentials: 'include',
        });

        if (res.ok) {
          const response = await res.json();
          // API returns { data: [...], total, page, limit }
          setKnowledgeBases(Array.isArray(response) ? response : response.data || []);
        }
      } catch (err) {
        console.error('Failed to fetch knowledge bases:', err);
      } finally {
        setLoadingKBs(false);
      }
    };

    fetchKnowledgeBases();
    // Also fetch KBs into the store if not already loaded
    if (storeKbs.length === 0) {
      fetchKbs();
    }
  }, [storeKbs.length, fetchKbs]);

  // Sync KB selection with sidebar: when kbId changes, update sidebar's active KB
  useEffect(() => {
    if (kbId && storeKbs.length > 0) {
      const kbToSelect = storeKbs.find((kb) => kb.id === kbId);
      if (kbToSelect && activeKb?.id !== kbId) {
        setActiveKb(kbToSelect);
      }
    }
  }, [kbId, storeKbs, activeKb?.id, setActiveKb]);

  // Initialize from sidebar's active KB if no URL param provided
  useEffect(() => {
    if (!kbId && activeKb && !searchParams.get('kb_id')) {
      setKbId(activeKb.id);
      router.replace(`/operations/kb-stats?kb_id=${activeKb.id}`);
    }
  }, [activeKb, kbId, searchParams, router]);

  const handleKBChange = useCallback((newKbId: string) => {
    setKbId(newKbId);
    router.push(`/operations/kb-stats?kb_id=${newKbId}`);

    // Sync with sidebar
    const kbToSelect = storeKbs.find((kb) => kb.id === newKbId);
    if (kbToSelect) {
      setActiveKb(kbToSelect);
    }
  }, [router, storeKbs, setActiveKb]);

  if (!kbId) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Database className="h-8 w-8" />
                <h1 className="text-2xl font-bold">Knowledge Base Statistics</h1>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Select a knowledge base to view detailed statistics
              </p>
            </div>
            <Button variant="outline" onClick={() => router.push('/operations')}>
              Back to Operations
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Select Knowledge Base</CardTitle>
              <CardDescription>
                Choose a knowledge base to view statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingKBs ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <Select onValueChange={handleKBChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a knowledge base" />
                  </SelectTrigger>
                  <SelectContent>
                    {knowledgeBases.map((kb) => (
                      <SelectItem key={kb.id} value={kb.id}>
                        {kb.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <Skeleton className="h-10 w-64 mb-6" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
          <Skeleton className="h-64" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Knowledge Base Statistics</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-6">
            <p className="text-sm text-destructive mb-4">
              {error instanceof Error ? error.message : 'Failed to load KB statistics'}
            </p>
            <Button onClick={() => router.push('/operations')}>
              Return to Operations Dashboard
            </Button>
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
      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Database className="h-8 w-8" />
            <h1 className="text-2xl font-bold">{stats.kb_name}</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Knowledge Base Statistics
          </p>
        </div>
        <div className="flex items-center gap-2">
          {loadingKBs ? (
            <Skeleton className="h-10 w-64" />
          ) : (
            <Select value={kbId || undefined} onValueChange={handleKBChange}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Switch KB" />
              </SelectTrigger>
              <SelectContent>
                {knowledgeBases.map((kb) => (
                  <SelectItem key={kb.id} value={kb.id}>
                    {kb.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button variant="outline" onClick={() => router.push('/operations')}>
            Back to Operations
          </Button>
        </div>
      </div>

      {/* Document & Storage Metrics */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Documents & Storage</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Total Documents"
            value={stats.document_count}
            description="Documents in this KB"
            icon={FileText}
          />
          <StatCard
            title="Storage Used"
            value={formatBytes(stats.storage_bytes)}
            description={stats.document_count > 0 ? `Avg: ${formatBytes(stats.storage_bytes / stats.document_count)}` : 'No documents'}
            icon={HardDrive}
          />
          <StatCard
            title="Vector Chunks"
            value={stats.total_chunks}
            description={`${stats.total_embeddings} embeddings`}
            icon={Database}
          />
        </div>
      </section>

      {/* Usage Metrics (Last 30 Days) */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Usage (Last 30 Days)</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Searches"
            value={stats.searches_30d}
            description="Search queries performed"
            icon={Search}
          />
          <StatCard
            title="Generations"
            value={stats.generations_30d}
            description="Documents generated"
            icon={FileSearch}
          />
          <StatCard
            title="Unique Users"
            value={stats.unique_users_30d}
            description="Active users"
            icon={Users}
          />
        </div>
      </section>

      {/* Top Documents */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Top Accessed Documents (Last 30 Days)</h2>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Most Popular Documents
            </CardTitle>
            <CardDescription>
              Documents with the highest access count
            </CardDescription>
          </CardHeader>
          <CardContent>
            {stats.top_documents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No document access data available for the last 30 days.
              </p>
            ) : (
              <div className="space-y-4">
                {stats.top_documents.map((doc, index) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between border-b pb-3 last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{doc.filename}</p>
                        <p className="text-xs text-muted-foreground">ID: {doc.id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{doc.access_count}</p>
                      <p className="text-xs text-muted-foreground">accesses</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Metadata */}
      <div className="text-xs text-muted-foreground">
        Last updated: {new Date(stats.last_updated).toLocaleString()}
      </div>
      </div>
    </DashboardLayout>
  );
}
