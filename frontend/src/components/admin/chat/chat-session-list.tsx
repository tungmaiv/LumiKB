/**
 * Chat Session List Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC1: Session list displays user, KB name, message count, and last active timestamp
 */
'use client';

import { formatDistanceToNow } from 'date-fns';
import { MessageCircle, User } from 'lucide-react';

import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import type { ChatSession } from '@/hooks/useChatHistory';

interface ChatSessionListProps {
  sessions: ChatSession[];
  selectedSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  isLoading?: boolean;
}

/**
 * Truncate session ID for display
 */
function truncateSessionId(sessionId: string): string {
  if (sessionId.length <= 12) return sessionId;
  return `${sessionId.slice(0, 8)}...`;
}

/**
 * Loading skeleton for session list
 */
export function ChatSessionListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}

export function ChatSessionList({
  sessions,
  selectedSessionId,
  onSelectSession,
  isLoading,
}: ChatSessionListProps) {
  if (isLoading) {
    return <ChatSessionListSkeleton />;
  }

  if (sessions.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        No chat sessions found
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Session</TableHead>
          <TableHead>User</TableHead>
          <TableHead>Knowledge Base</TableHead>
          <TableHead>Messages</TableHead>
          <TableHead>Last Active</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sessions.map((session) => (
          <TableRow
            key={session.session_id}
            className={cn(
              'cursor-pointer',
              selectedSessionId === session.session_id && 'bg-muted'
            )}
            onClick={() => onSelectSession(session.session_id)}
            data-testid={`session-row-${session.session_id}`}
          >
            <TableCell className="font-mono text-sm">
              {truncateSessionId(session.session_id)}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="truncate max-w-[120px]">
                  {session.user_name || 'Unknown'}
                </span>
              </div>
            </TableCell>
            <TableCell className="truncate max-w-[150px]">
              {session.kb_name || '-'}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <MessageCircle className="h-4 w-4 text-muted-foreground" />
                {session.message_count}
              </div>
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatDistanceToNow(new Date(session.last_message_at), {
                addSuffix: true,
              })}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
