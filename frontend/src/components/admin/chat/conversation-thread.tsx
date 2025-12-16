/**
 * Conversation Thread Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC2: Click session row to view full conversation thread
 * AC3: User messages and assistant messages rendered with distinct styling
 * AC5: Token usage and response time shown per assistant message
 *
 * Story 9-15: Debug Info in Chat History
 * Displays debug info for assistant messages when KB debug_mode was enabled
 */
'use client';

import { useState, useMemo } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Bot, Bug, ChevronDown, ChevronRight, Clock, FileText, Settings, User, Zap, ChevronsUpDown } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ChatMessageItem, ChatHistoryDebugInfo } from '@/hooks/useChatHistory';
import { CitationDisplay } from './citation-display';

interface ConversationThreadProps {
  messages: ChatMessageItem[];
  isLoading?: boolean;
}

/** Max characters before truncating message content */
const MAX_CONTENT_LENGTH = 500;

/**
 * Format token count with comma separators
 */
function formatTokens(count: number | null): string {
  if (count === null) return '-';
  return count.toLocaleString();
}

/**
 * Format response time
 */
function formatResponseTime(ms: number | null): string {
  if (ms === null) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * Format milliseconds to human-readable string
 */
function formatMs(ms: number): string {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${ms.toFixed(0)}ms`;
}

/**
 * Get color class for similarity score
 */
function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600 dark:text-green-400';
  if (score >= 0.5) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
}

/**
 * Debug Info Section for Chat History (Story 9-15)
 * Displays RAG pipeline telemetry from stored chat history
 * Styled to match dark theme UI spec
 */
function DebugInfoSection({ debugInfo }: { debugInfo: ChatHistoryDebugInfo }) {
  const [isOpen, setIsOpen] = useState(false);

  const { kb_params, chunks_retrieved, timing } = debugInfo;
  const totalTime = timing
    ? timing.retrieval_ms + timing.context_assembly_ms
    : 0;
  const chunkCount = chunks_retrieved?.length ?? 0;

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="mt-3 border border-border/50 rounded-lg bg-muted/30"
      data-testid="chat-history-debug-info"
    >
      <CollapsibleTrigger className="flex items-center justify-between w-full px-3 py-2 hover:bg-muted/50 transition-colors rounded-t-lg">
        <div className="flex items-center gap-2">
          <Bug className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Debug Info</span>
          {chunkCount > 0 && (
            <Badge variant="secondary" className="text-[10px] h-5 px-1.5 bg-secondary/80">
              {chunkCount} chunks
            </Badge>
          )}
          {timing && (
            <Badge variant="outline" className="text-[10px] font-mono h-5 px-1.5">
              {formatMs(totalTime)}
            </Badge>
          )}
        </div>
        {isOpen ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </CollapsibleTrigger>

      <CollapsibleContent className="px-3 pb-3 border-t border-border/30">
        <div className="space-y-4 pt-3">
          {/* KB Parameters */}
          {kb_params && (
            <section data-testid="debug-kb-params" className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Settings className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  KB Parameters
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs bg-background/40 rounded-md p-2">
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Citation:</span>
                  <span className="font-medium capitalize">{kb_params.citation_style}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Language:</span>
                  <span className="font-medium uppercase">{kb_params.response_language}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Uncertainty:</span>
                  <span className="font-medium capitalize">
                    {kb_params.uncertainty_handling.replace('_', ' ')}
                  </span>
                </div>
                {kb_params.system_prompt_preview && (
                  <div className="col-span-2 pt-1 border-t border-border/30">
                    <span className="text-muted-foreground">Prompt: </span>
                    <span className="font-mono text-[10px] text-muted-foreground/80" title={kb_params.system_prompt_preview}>
                      {kb_params.system_prompt_preview.slice(0, 60)}...
                    </span>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Timing */}
          {timing && (
            <section data-testid="debug-timing" className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Timing
                </span>
              </div>
              <div className="flex gap-4 text-xs bg-background/40 rounded-md p-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-muted-foreground">Retrieval:</span>
                  <Badge variant="outline" className="font-mono text-[10px] h-5 px-1.5">
                    {formatMs(timing.retrieval_ms)}
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-muted-foreground">Context:</span>
                  <Badge variant="outline" className="font-mono text-[10px] h-5 px-1.5">
                    {formatMs(timing.context_assembly_ms)}
                  </Badge>
                </div>
              </div>
            </section>
          )}

          {/* Retrieved Chunks */}
          {chunks_retrieved && chunks_retrieved.length > 0 && (
            <section data-testid="debug-chunks" className="space-y-2">
              <div className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Retrieved Chunks ({chunks_retrieved.length})
                </span>
              </div>
              <div className="space-y-1.5 max-h-[180px] overflow-y-auto bg-background/40 rounded-md p-2">
                {chunks_retrieved.map((chunk, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs bg-muted/30 rounded px-2.5 py-1.5 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Badge variant="outline" className="font-mono text-[10px] h-5 px-1.5 shrink-0">
                        #{chunk.chunk_index}
                      </Badge>
                      {chunk.document_name && (
                        <span className="truncate text-muted-foreground" title={chunk.document_name}>
                          {chunk.document_name}
                        </span>
                      )}
                    </div>
                    <Badge
                      variant="secondary"
                      className={cn('font-mono text-[10px] h-5 px-1.5 shrink-0', getScoreColor(chunk.relevance_score))}
                    >
                      {(chunk.relevance_score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

/**
 * Loading skeleton for conversation thread
 */
export function ConversationThreadSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'flex flex-col gap-2',
            i % 2 === 0 ? 'items-end' : 'items-start'
          )}
        >
          <Skeleton
            className={cn('h-20 rounded-lg', i % 2 === 0 ? 'w-2/3' : 'w-3/4')}
          />
        </div>
      ))}
    </div>
  );
}

/**
 * Collapsible message content for long responses
 */
function MessageContentView({
  text,
  isExpanded,
  onToggle,
}: {
  text: string;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isLongContent = text.length > MAX_CONTENT_LENGTH;
  const displayContent = isExpanded || !isLongContent
    ? text
    : text.slice(0, MAX_CONTENT_LENGTH) + '...';

  return (
    <div className="relative">
      <p className="text-sm leading-relaxed whitespace-pre-wrap" data-testid="message-content">
        {displayContent}
      </p>
      {isLongContent && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="mt-2 h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
          data-testid="content-toggle"
        >
          <ChevronsUpDown className="h-3 w-3 mr-1" />
          {isExpanded ? 'Show less' : `Show more (${text.length} chars)`}
        </Button>
      )}
    </div>
  );
}

/**
 * Single message bubble component
 */
function MessageBubble({ message }: { message: ChatMessageItem }) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [isContentExpanded, setIsContentExpanded] = useState(false);

  // Check if content is long enough to need collapsing
  const isLongContent = message.content.length > MAX_CONTENT_LENGTH;

  return (
    <div
      data-testid={`message-${message.id}`}
      className={cn(
        'flex flex-col gap-2 max-w-[80%]',
        isUser && 'ml-auto items-end',
        isAssistant && 'mr-auto items-start'
      )}
    >
      {/* Role indicator */}
      <div
        className={cn(
          'flex items-center gap-1 text-xs text-muted-foreground',
          isUser && 'flex-row-reverse'
        )}
      >
        {isUser ? (
          <User className="h-3 w-3" />
        ) : (
          <Bot className="h-3 w-3" />
        )}
        <span>{isUser ? 'User' : 'Assistant'}</span>
        {isLongContent && (
          <Badge variant="outline" className="text-[10px] h-4 px-1 ml-1">
            {message.content.length} chars
          </Badge>
        )}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          'rounded-lg px-4 py-3 shadow-sm',
          isUser && 'bg-primary text-primary-foreground',
          isAssistant && 'bg-muted'
        )}
      >
        <MessageContentView
          text={message.content}
          isExpanded={isContentExpanded}
          onToggle={() => setIsContentExpanded(!isContentExpanded)}
        />

        {/* Citations for assistant messages */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <CitationDisplay citations={message.citations} />
        )}

        {/* Debug info for assistant messages (Story 9-15) */}
        {isAssistant && message.debug_info && (
          <DebugInfoSection debugInfo={message.debug_info} />
        )}
      </div>

      {/* Metadata row */}
      <div
        className={cn(
          'flex items-center gap-3 text-xs text-muted-foreground px-1',
          isUser && 'justify-end'
        )}
      >
        {/* Timestamp */}
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
        </span>

        {/* Assistant-specific metrics (AC5) */}
        {isAssistant && (
          <>
            {message.token_count !== null && (
              <span className="flex items-center gap-1" data-testid="token-count">
                <Zap className="h-3 w-3" />
                {formatTokens(message.token_count)} tokens
              </span>
            )}
            {message.response_time_ms !== null && (
              <span data-testid="response-time">
                {formatResponseTime(message.response_time_ms)}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function ConversationThread({
  messages,
  isLoading,
}: ConversationThreadProps) {
  if (isLoading) {
    return <ConversationThreadSkeleton />;
  }

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        No messages in this conversation
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
}
