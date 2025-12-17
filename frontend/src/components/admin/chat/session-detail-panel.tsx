/**
 * Session Detail Panel Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC2: Click session row to view full conversation thread in detail panel
 */
'use client';

import { useCallback, useEffect, useMemo } from 'react';
import { format } from 'date-fns';
import { MessageCircle, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useChatMessages } from '@/hooks/useChatHistory';
import { ConversationThread, ConversationThreadSkeleton } from './conversation-thread';
import { ExportDialog } from './export-dialog';

interface SessionDetailPanelProps {
  sessionId: string | null;
  onClose: () => void;
}

export function SessionDetailPanel({ sessionId, onClose }: SessionDetailPanelProps) {
  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useChatMessages(sessionId);

  // Flatten all pages of messages
  const messages = useMemo(() => {
    if (!data) return [];
    return data.pages.flatMap((page) => page.items);
  }, [data]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (sessionId) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [sessionId, onClose]);

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const total = data?.pages[0]?.total || 0;

  return (
    <Sheet open={!!sessionId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl lg:max-w-2xl overflow-hidden flex flex-col"
      >
        <SheetHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Conversation
            </SheetTitle>
            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <ExportDialog messages={messages} sessionId={sessionId || ''} />
              )}
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {sessionId && (
            <div className="text-sm text-muted-foreground mt-2">
              <span className="font-mono">{sessionId.slice(0, 16)}...</span>
              {messages.length > 0 && (
                <>
                  <span className="mx-2">•</span>
                  <span>{total} messages</span>
                  <span className="mx-2">•</span>
                  <span>{format(new Date(messages[0].created_at), 'MMM d, yyyy')}</span>
                </>
              )}
            </div>
          )}
        </SheetHeader>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <ConversationThreadSkeleton />
          ) : (
            <>
              <ConversationThread messages={messages} />

              {/* Load More Button */}
              {hasNextPage && (
                <div className="flex justify-center py-4 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLoadMore}
                    disabled={isFetchingNextPage}
                    data-testid="load-more"
                  >
                    {isFetchingNextPage ? 'Loading...' : 'Load More Messages'}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
