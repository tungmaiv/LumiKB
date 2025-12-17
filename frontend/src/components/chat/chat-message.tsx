/**
 * ChatMessage Component - Epic 4, Story 4.2
 * Story 9-15: Added debug info panel support
 * Renders individual chat messages with user/AI styling, timestamps, and citations
 */

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';
import { DebugInfoPanel } from './debug-info-panel';
import type { DebugInfo } from '@/types/debug';

interface Citation {
  number: number;
  documentName: string;
  excerpt: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations: Citation[];
  confidence?: number;
  onCitationClick?: (citation: Citation) => void;
  /** Debug info (AC-9.15.14) - displayed in collapsible panel for assistant messages */
  debugInfo?: DebugInfo;
}

/**
 * Format relative timestamp
 */
function formatTimestamp(date: Date): string {
  const secondsAgo = (Date.now() - date.getTime()) / 1000;

  if (secondsAgo < 30) {
    return 'just now';
  }

  return formatDistanceToNow(date, { addSuffix: true });
}

/**
 * Get confidence level styling
 */
function getConfidenceStyles(confidence: number) {
  if (confidence >= 0.8) {
    return {
      color: 'bg-green-500',
      text: 'High confidence',
      className: 'bg-green-500',
    };
  } else if (confidence >= 0.5) {
    return {
      color: 'bg-amber-500',
      text: 'Medium confidence',
      className: 'bg-amber-500',
    };
  } else {
    return {
      color: 'bg-red-500',
      text: 'Low confidence - verify carefully',
      className: 'bg-red-500',
    };
  }
}

/**
 * Parse content and extract citation markers [1], [2], etc.
 */
function parseCitationsInContent(
  content: string,
  citations: Citation[],
  onCitationClick?: (citation: Citation) => void
): React.ReactNode {
  // Match citation markers like [1], [2], etc.
  const citationRegex = /\[(\d+)\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(content)) !== null) {
    const beforeText = content.substring(lastIndex, match.index);
    if (beforeText) {
      parts.push(beforeText);
    }

    const citationNumber = parseInt(match[1], 10);
    const citation = citations.find((c) => c.number === citationNumber);

    if (citation) {
      parts.push(
        <Badge
          key={`citation-${citationNumber}-${match.index}`}
          variant="default"
          className="mx-1 cursor-pointer hover:bg-primary/80"
          data-testid="citation-badge"
          onClick={(e) => {
            e.preventDefault();
            if (onCitationClick) {
              onCitationClick(citation);
            }
          }}
        >
          [{citationNumber}]
        </Badge>
      );
    } else {
      parts.push(match[0]); // If citation not found, show raw text
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(content.substring(lastIndex));
  }

  return parts.length > 0 ? parts : content;
}

export function ChatMessage({
  role,
  content,
  timestamp,
  citations,
  confidence,
  onCitationClick,
  debugInfo,
}: ChatMessageProps) {
  const isUser = role === 'user';
  const isAssistant = role === 'assistant';
  const showConfidence = isAssistant && confidence !== undefined;
  const confidenceStyles = showConfidence ? getConfidenceStyles(confidence) : null;
  // AC-9.15.14: Show debug panel for assistant messages when debug info is present
  const showDebugPanel = isAssistant && debugInfo !== undefined;

  return (
    <div
      data-testid="chat-message"
      data-role={role}
      className={cn(
        'flex flex-col gap-2 max-w-3xl mb-4',
        isUser && 'ml-auto items-end justify-end',
        isAssistant && 'mr-auto items-start justify-start'
      )}
    >
      {/* Message Bubble */}
      <div
        className={cn(
          'rounded-lg px-4 py-3 shadow-sm',
          isUser && 'bg-primary text-primary-foreground',
          isAssistant && 'bg-card border'
        )}
      >
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {isAssistant ? parseCitationsInContent(content, citations, onCitationClick) : content}
        </div>
      </div>

      {/* Metadata Row */}
      <div
        className={cn(
          'flex items-center gap-3 text-xs text-muted-foreground px-2',
          isUser && 'justify-end'
        )}
      >
        {/* Timestamp */}
        <span data-testid="message-timestamp">{formatTimestamp(timestamp)}</span>

        {/* Confidence Indicator (AI only) */}
        {showConfidence && confidenceStyles && (
          <div
            data-testid="confidence-indicator"
            className={cn('flex items-center gap-2', confidenceStyles.className)}
          >
            <div className="flex items-center gap-1">
              <div className="h-2 w-16 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn('h-full', confidenceStyles.className)}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
              <span className="text-xs">{Math.round(confidence * 100)}%</span>
            </div>
            {confidence < 0.5 && <span className="text-red-600 font-medium">Verify carefully</span>}
          </div>
        )}
      </div>

      {/* Debug Info Panel (AC-9.15.14-17) - only for assistant messages with debug data */}
      {showDebugPanel && debugInfo && <DebugInfoPanel debugInfo={debugInfo} className="w-full" />}
    </div>
  );
}
