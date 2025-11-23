'use client';

import { useEffect, useState } from 'react';
import { Plus, Database, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { KbSelectorItem } from '@/components/kb/kb-selector-item';
import { fetchKnowledgeBases, type KnowledgeBase } from '@/lib/api/knowledge-bases';

// Map API permission levels to component permission props
function mapPermission(
  apiPermission: KnowledgeBase['permission_level']
): 'viewer' | 'editor' | 'admin' {
  switch (apiPermission) {
    case 'ADMIN':
      return 'admin';
    case 'WRITE':
      return 'editor';
    case 'READ':
    default:
      return 'viewer';
  }
}

export function KbSidebar(): React.ReactElement {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadKnowledgeBases() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchKnowledgeBases();
        setKbs(data);
      } catch (err) {
        // If not authenticated, show empty state (user will see login prompt)
        if (err instanceof Error && err.message.includes('401')) {
          setKbs([]);
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load knowledge bases');
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadKnowledgeBases();
  }, []);

  return (
    <div className="flex h-full flex-col bg-sidebar">
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-sidebar-foreground" />
          <h2 className="font-semibold text-sidebar-foreground">Knowledge Bases</h2>
        </div>
        <Button
          variant="ghost"
          size="icon"
          disabled
          className="h-8 w-8"
          aria-label="New Knowledge Base"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <Separator />

      {/* KB List */}
      <ScrollArea className="flex-1 px-2 py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="px-3 py-4 text-sm text-destructive">{error}</div>
        ) : kbs.length === 0 ? (
          <div className="px-3 py-4 text-sm text-muted-foreground">
            No knowledge bases available. Run the seed script to create a demo KB.
          </div>
        ) : (
          <div className="space-y-1">
            {kbs.map((kb) => (
              <KbSelectorItem
                key={kb.id}
                name={kb.name}
                documentCount={kb.document_count}
                permission={mapPermission(kb.permission_level)}
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
    </div>
  );
}
