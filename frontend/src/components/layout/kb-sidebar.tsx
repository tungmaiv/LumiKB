'use client';

import { useEffect, useState } from 'react';
import { Plus, Database, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { KbSelectorItem } from '@/components/kb/kb-selector-item';
import { KbCreateModal } from '@/components/kb/kb-create-modal';
import { useKBStore } from '@/lib/stores/kb-store';
import { useAuthStore } from '@/lib/stores/auth-store';

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

export function KbSidebar(): React.ReactElement {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { kbs, activeKb, isLoading, error, fetchKbs, setActiveKb } = useKBStore();
  const user = useAuthStore((state) => state.user);

  // Check if user has admin permission on any KB (or can create new ones)
  // Users who are authenticated can create KBs (they become owner with ADMIN)
  const canCreateKb = !!user;

  useEffect(() => {
    fetchKbs();
  }, [fetchKbs]);

  const handleKbClick = (kb: (typeof kbs)[0]) => {
    setActiveKb(kb);
  };

  return (
    <div className="flex h-full flex-col bg-sidebar">
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

      {/* KB List */}
      <ScrollArea className="flex-1 px-2 py-2">
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
        ) : (
          <div className="space-y-1">
            {kbs.map((kb) => (
              <KbSelectorItem
                key={kb.id}
                name={kb.name}
                documentCount={kb.document_count}
                permissionLevel={kb.permission_level || 'READ'}
                isActive={activeKb?.id === kb.id}
                onClick={() => handleKbClick(kb)}
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
