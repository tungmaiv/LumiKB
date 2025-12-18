/**
 * Session Selector component - Story 8-0: Chat Session Persistence
 *
 * Dropdown for viewing and switching between past chat sessions.
 * Displays session previews, message counts, and timestamps.
 */

'use client';

import { useState, useCallback } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { ChevronDown, History, MessageSquare, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  useChatSessions,
  type ChatSessionItem,
  type ChatSessionMessagesResponse,
} from '@/hooks/useChatSessions';

export interface SessionSelectorProps {
  kbId: string;
  /** Currently active conversation ID */
  currentConversationId?: string;
  /** Called when user selects a session to load */
  onSessionSelect: (session: ChatSessionMessagesResponse) => void;
  /** Whether the chat is currently streaming */
  disabled?: boolean;
}

/**
 * Dropdown component for browsing and loading past chat sessions.
 *
 * @example
 * <SessionSelector
 *   kbId="kb-uuid"
 *   currentConversationId={currentConvId}
 *   onSessionSelect={(session) => {
 *     // Load messages into chat
 *     setMessages(session.messages);
 *   }}
 * />
 */
export function SessionSelector({
  kbId,
  currentConversationId,
  onSessionSelect,
  disabled = false,
}: SessionSelectorProps) {
  const { sessions, total, isLoading, error, refresh, loadSession, isLoadingSession } =
    useChatSessions({ kbId });

  const [open, setOpen] = useState(false);

  const handleSessionClick = useCallback(
    async (session: ChatSessionItem) => {
      // Don't reload current session
      if (session.conversation_id === currentConversationId) {
        setOpen(false);
        return;
      }

      const loadedSession = await loadSession(session.conversation_id);
      if (loadedSession) {
        onSessionSelect(loadedSession);
        setOpen(false);
      }
    },
    [currentConversationId, loadSession, onSessionSelect]
  );

  // Format session timestamp for display
  const formatSessionTime = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffHours < 24) {
      return formatDistanceToNow(date, { addSuffix: true });
    } else if (diffHours < 24 * 7) {
      return format(date, 'EEE, h:mm a');
    } else {
      return format(date, 'MMM d, yyyy');
    }
  };

  // Truncate preview text
  const truncatePreview = (text: string, maxLength = 50): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          disabled={disabled || isLoadingSession}
          className="gap-1"
          data-testid="session-selector-trigger"
        >
          {isLoadingSession ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <History className="h-4 w-4" />
          )}
          <span className="hidden sm:inline">History</span>
          {total > 0 && <span className="ml-1 text-xs text-muted-foreground">({total})</span>}
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Chat History</span>
          {isLoading && <Loader2 className="h-3 w-3 animate-spin" />}
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {error && <div className="px-2 py-1.5 text-sm text-destructive">{error}</div>}

        {!isLoading && sessions.length === 0 && (
          <div className="px-2 py-4 text-center text-sm text-muted-foreground">
            No past sessions found.
            <br />
            Start chatting to create history.
          </div>
        )}

        {sessions.map((session) => {
          const isCurrent = session.conversation_id === currentConversationId;
          return (
            <DropdownMenuItem
              key={session.conversation_id}
              onClick={() => void handleSessionClick(session)}
              disabled={isLoadingSession}
              className={`flex flex-col items-start gap-1 py-2 cursor-pointer ${
                isCurrent ? 'bg-accent' : ''
              }`}
              data-testid={`session-item-${session.conversation_id}`}
            >
              <div className="flex w-full items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {formatSessionTime(session.last_message_at)}
                </span>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <MessageSquare className="h-3 w-3" />
                  <span>{Math.ceil(session.message_count / 2)}</span>
                  {isCurrent && (
                    <span className="ml-1 text-xs font-medium text-primary">(current)</span>
                  )}
                </div>
              </div>
              <span className="text-sm font-medium line-clamp-1">
                {truncatePreview(session.first_message_preview, 60)}
              </span>
            </DropdownMenuItem>
          );
        })}

        {total > sessions.length && (
          <>
            <DropdownMenuSeparator />
            <div className="px-2 py-1.5 text-center text-xs text-muted-foreground">
              Showing {sessions.length} of {total} sessions
            </div>
          </>
        )}

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => void refresh()}
          disabled={isLoading}
          className="justify-center text-xs"
        >
          {isLoading ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
          Refresh
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
