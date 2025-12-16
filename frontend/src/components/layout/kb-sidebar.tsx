'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { Plus, Database, FolderOpen, Clock, Sparkles, Search, X, LayoutDashboard, Archive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { KbSelectorItem } from '@/components/kb/kb-selector-item';
import { KbCreateModal } from '@/components/kb/kb-create-modal';
import { KBActionsMenu } from '@/components/kb/kb-actions-menu';
import { useKBStore } from '@/lib/stores/kb-store';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRecentKBs } from '@/hooks/useRecentKBs';
import { useKBRecommendations } from '@/hooks/useKBRecommendations';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

function KbSelectorSkeleton(): React.ReactElement {
  return (
    <div className="space-y-2 p-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-2">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-5 w-10 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function RecentKbsSkeleton(): React.ReactElement {
  return (
    <div className="space-y-1 px-2">
      {[1, 2].map((i) => (
        <div key={i} className="flex items-center gap-2 px-3 py-1.5">
          <Skeleton className="h-3 w-3 rounded" />
          <Skeleton className="h-3 flex-1" />
        </div>
      ))}
    </div>
  );
}

export function KbSidebar(): React.ReactElement {
  const router = useRouter();
  const pathname = usePathname();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const isDashboardActive = pathname === '/dashboard';

  const { kbs, activeKb, isLoading, error, fetchKbs, setActiveKb, showArchived, setShowArchived } = useKBStore();
  const user = useAuthStore((state) => state.user);

  // Filter KBs based on search query (name, description, or tags) and archived status
  const filteredKbs = useMemo(() => {
    let filtered = kbs;

    // Filter by archived status unless showArchived is true
    if (!showArchived) {
      filtered = filtered.filter((kb) => !kb.archived_at);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (kb) =>
          kb.name.toLowerCase().includes(query) ||
          (kb.description && kb.description.toLowerCase().includes(query)) ||
          (kb.tags && kb.tags.some((tag) => tag.toLowerCase().includes(query)))
      );
    }

    return filtered;
  }, [kbs, searchQuery, showArchived]);

  // Count of archived KBs
  const archivedCount = useMemo(() => kbs.filter((kb) => kb.archived_at).length, [kbs]);

  // Show search when there are many KBs (5+)
  const showSearch = kbs.length >= 5;

  // Fetch recent KBs and recommendations
  const {
    data: recentKBs,
    isLoading: isLoadingRecent,
  } = useRecentKBs();
  const {
    data: recommendations,
    isLoading: isLoadingRecommendations,
  } = useKBRecommendations();

  // Check if user has admin permission on any KB (or can create new ones)
  // Users who are authenticated can create KBs (they become owner with ADMIN)
  const canCreateKb = !!user;

  // Always fetch with include_archived=true to get accurate archived count for the toggle
  // The filtering is done client-side based on showArchived state
  useEffect(() => {
    fetchKbs({ include_archived: true });
  }, [fetchKbs]);

  const handleKbClick = useCallback((kb: KnowledgeBase) => {
    setActiveKb(kb);
  }, [setActiveKb]);

  const handleToggleArchived = useCallback((checked: boolean) => {
    setShowArchived(checked);
  }, [setShowArchived]);

  const handleRecentKbClick = (kbId: string) => {
    // Find KB in store and set as active, then navigate to search
    const kb = kbs.find((k) => k.id === kbId);
    if (kb) {
      setActiveKb(kb);
    }
    router.push(`/search?kb=${kbId}`);
  };

  const handleRecommendationClick = (kbId: string) => {
    // Find KB in store and set as active, then navigate to search
    const kb = kbs.find((k) => k.id === kbId);
    if (kb) {
      setActiveKb(kb);
    }
    router.push(`/search?kb=${kbId}`);
  };

  // Check if user has no access history for empty state
  const hasNoHistory = !isLoadingRecent && (!recentKBs || recentKBs.length === 0);
  const hasRecommendations = !isLoadingRecommendations && recommendations && recommendations.length > 0;

  return (
    <div className="flex h-full flex-col bg-sidebar">
      {/* Dashboard Link */}
      <div className="p-2">
        <Link
          href="/dashboard"
          className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent ${
            isDashboardActive
              ? 'bg-accent text-accent-foreground'
              : 'text-sidebar-foreground'
          }`}
        >
          <LayoutDashboard className="h-5 w-5" />
          Dashboard
        </Link>
      </div>

      <Separator />

      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-sidebar-foreground" />
          <h2 className="font-semibold text-sidebar-foreground">Knowledge Bases</h2>
        </div>
        {canCreateKb && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            aria-label="Create Knowledge Base"
            onClick={() => setIsCreateModalOpen(true)}
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      <Separator />

      {/* Search Box - only show when there are many KBs */}
      {showSearch && (
        <div className="px-3 py-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by name or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 pl-8 pr-8 text-sm"
              aria-label="Search knowledge bases by name or tags"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-0.5 top-1/2 h-7 w-7 -translate-y-1/2"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Show Archived Toggle - Story 7-26: AC-7.26.5 */}
      {archivedCount > 0 && (
        <div className="px-3 py-2 flex items-center justify-between">
          <Label
            htmlFor="show-archived"
            className="text-xs text-muted-foreground flex items-center gap-1.5 cursor-pointer"
          >
            <Archive className="h-3.5 w-3.5" />
            Show Archived ({archivedCount})
          </Label>
          <Switch
            id="show-archived"
            checked={showArchived}
            onCheckedChange={handleToggleArchived}
            className="scale-75"
            aria-label="Toggle show archived knowledge bases"
          />
        </div>
      )}

      {/* KB List with Recent and Recommendations sections */}
      <ScrollArea className="flex-1 px-2 py-2">
        {/* Recent KBs Section - hide when searching */}
        {!searchQuery && (isLoadingRecent || (recentKBs && recentKBs.length > 0)) && (
          <div className="mb-4">
            <div className="flex items-center gap-2 px-3 py-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Recent
              </span>
            </div>
            {isLoadingRecent ? (
              <RecentKbsSkeleton />
            ) : (
              <div className="space-y-0.5">
                {recentKBs?.slice(0, 5).map((recentKb) => (
                  <button
                    key={recentKb.kb_id}
                    onClick={() => handleRecentKbClick(recentKb.kb_id)}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-sm hover:bg-accent focus:bg-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    aria-label={`Open ${recentKb.kb_name}`}
                  >
                    <Database className="h-3 w-3 text-muted-foreground" />
                    <span className="truncate flex-1">{recentKb.kb_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {recentKb.document_count} docs
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recommendations Section - show for new users or when no history, hide when searching */}
        {!searchQuery && hasNoHistory && hasRecommendations && (
          <div className="mb-4">
            <div className="flex items-center gap-2 px-3 py-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Suggested for you
              </span>
            </div>
            <div className="space-y-0.5">
              {recommendations?.slice(0, 3).map((rec) => (
                <button
                  key={rec.kb_id}
                  onClick={() => handleRecommendationClick(rec.kb_id)}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-sm hover:bg-accent focus:bg-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label={`Open ${rec.kb_name} - ${rec.reason}`}
                  title={rec.reason}
                >
                  <Database className="h-3 w-3 text-muted-foreground" />
                  <span className="truncate flex-1">{rec.kb_name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Separator if we have recent or recommendations - hide when searching */}
        {!searchQuery && ((recentKBs && recentKBs.length > 0) || (hasNoHistory && hasRecommendations)) && kbs.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-2 px-3 py-2">
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                All Knowledge Bases
              </span>
            </div>
          </div>
        )}

        {/* Search results header when searching */}
        {searchQuery && (
          <div className="mb-2">
            <div className="flex items-center justify-between px-3 py-2">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Search Results
              </span>
              <span className="text-xs text-muted-foreground">
                {filteredKbs.length} of {kbs.length}
              </span>
            </div>
          </div>
        )}

        {/* All KBs List */}
        {isLoading ? (
          <KbSelectorSkeleton />
        ) : error ? (
          <div className="px-3 py-4 text-sm text-destructive">{error}</div>
        ) : kbs.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-3 py-8 text-center">
            <FolderOpen className="h-10 w-10 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground mb-4">No Knowledge Bases available</p>
            {canCreateKb && (
              <Button variant="outline" size="sm" onClick={() => setIsCreateModalOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create your first Knowledge Base
              </Button>
            )}
          </div>
        ) : filteredKbs.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-3 py-8 text-center">
            <Search className="h-10 w-10 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">No matching Knowledge Bases</p>
            <p className="text-xs text-muted-foreground mt-1">
              Try a different search term
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredKbs.map((kb) => (
              <KbSelectorItem
                key={kb.id}
                name={kb.name}
                documentCount={kb.document_count}
                permissionLevel={kb.permission_level || 'READ'}
                tags={kb.tags}
                isActive={activeKb?.id === kb.id}
                isArchived={!!kb.archived_at}
                onClick={() => handleKbClick(kb)}
                actionSlot={
                  kb.permission_level === 'ADMIN' ? (
                    <KBActionsMenu kb={kb} />
                  ) : undefined
                }
              />
            ))}
          </div>
        )}
      </ScrollArea>

      <Separator />

      {/* Footer - Storage indicator */}
      <div className="p-4">
        <div className="text-xs text-muted-foreground">
          <div className="flex justify-between">
            <span>Storage used</span>
            <span>Coming soon</span>
          </div>
          <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
            <div className="h-full w-1/3 rounded-full bg-primary/50" />
          </div>
        </div>
      </div>

      {/* Create KB Modal */}
      <KbCreateModal open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen} />
    </div>
  );
}
