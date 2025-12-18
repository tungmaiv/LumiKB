/**
 * Debug Info Panel Component - Story 9-15: KB Debug Mode & Prompt Configuration
 *
 * Displays RAG pipeline telemetry in a collapsible panel.
 * AC-9.15.14: Chat UI shows collapsible "Debug Info" panel when debug data received
 * AC-9.15.15: Debug panel shows KB parameters in formatted table
 * AC-9.15.16: Debug panel shows retrieved chunks with similarity scores (expandable)
 * AC-9.15.17: Debug panel shows timing breakdown (retrieval_ms, context_assembly_ms)
 * AC-9.15.18: Debug info only visible to users with KB admin/edit permissions
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Bug, Clock, FileText, Settings, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import type { DebugInfo, ChunkDebugInfo } from '@/types/debug';

interface DebugInfoPanelProps {
  /** Debug info from RAG pipeline */
  debugInfo: DebugInfo;
  /** CSS class name */
  className?: string;
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
 * Single chunk item with expandable preview
 */
function ChunkItem({ chunk, index }: { chunk: ChunkDebugInfo; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-md p-2 text-xs" data-testid={`debug-chunk-${index}`}>
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <button className="p-0.5">
            {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>
          <FileText className="h-3 w-3 text-muted-foreground" />
          <span className="font-medium truncate max-w-[200px]">{chunk.document_name}</span>
          {chunk.page_number && (
            <span className="text-muted-foreground">p.{chunk.page_number}</span>
          )}
        </div>
        <Badge
          variant="outline"
          className={cn('font-mono', getScoreColor(chunk.similarity_score))}
          data-testid={`debug-chunk-${index}-score`}
        >
          {(chunk.similarity_score * 100).toFixed(1)}%
        </Badge>
      </div>
      {expanded && (
        <div
          className="mt-2 pl-6 text-muted-foreground whitespace-pre-wrap break-words"
          data-testid={`debug-chunk-${index}-preview`}
        >
          {chunk.preview}
        </div>
      )}
    </div>
  );
}

/**
 * Debug Info Panel - displays RAG pipeline telemetry
 */
export function DebugInfoPanel({ debugInfo, className }: DebugInfoPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { kb_params, chunks_retrieved, timing, query_rewrite } = debugInfo;
  const queryRewriteMs = timing.query_rewrite_ms ?? 0;
  const totalTime = timing.retrieval_ms + timing.context_assembly_ms + queryRewriteMs;

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn('border rounded-lg bg-muted/30', className)}
      data-testid="debug-info-panel"
    >
      <CollapsibleTrigger className="flex items-center justify-between w-full p-3 hover:bg-muted/50 transition-colors">
        <div className="flex items-center gap-2">
          <Bug className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-medium">Debug Info</span>
          <Badge variant="secondary" className="text-xs">
            {chunks_retrieved.length} chunks
          </Badge>
          <Badge variant="outline" className="text-xs font-mono">
            {formatMs(totalTime)}
          </Badge>
          {query_rewrite?.was_rewritten && (
            <Badge variant="outline" className="text-xs text-blue-600 dark:text-blue-400">
              <RefreshCw className="h-3 w-3 mr-1" />
              rewritten
            </Badge>
          )}
        </div>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </CollapsibleTrigger>

      <CollapsibleContent className="px-3 pb-3">
        <div className="space-y-4">
          {/* KB Parameters Section (AC-9.15.15) */}
          <section data-testid="debug-kb-params">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium uppercase text-muted-foreground">
                KB Parameters
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex flex-col">
                <span className="text-muted-foreground">Citation Style</span>
                <span className="font-medium capitalize" data-testid="debug-citation-style">
                  {kb_params.citation_style}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-muted-foreground">Language</span>
                <span className="font-medium uppercase" data-testid="debug-language">
                  {kb_params.response_language}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-muted-foreground">Uncertainty</span>
                <span className="font-medium capitalize" data-testid="debug-uncertainty">
                  {kb_params.uncertainty_handling.replace('_', ' ')}
                </span>
              </div>
              <div className="flex flex-col col-span-2">
                <span className="text-muted-foreground">System Prompt</span>
                <span
                  className="font-mono text-[11px] truncate"
                  title={kb_params.system_prompt_preview}
                  data-testid="debug-system-prompt"
                >
                  {kb_params.system_prompt_preview || '(default)'}
                </span>
              </div>
            </div>
          </section>

          {/* Query Rewrite Section (Story 8-0) */}
          {query_rewrite && (
            <section data-testid="debug-query-rewrite">
              <div className="flex items-center gap-2 mb-2">
                <RefreshCw className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs font-medium uppercase text-muted-foreground">
                  Query Rewrite
                </span>
                {query_rewrite.was_rewritten ? (
                  <Badge
                    variant="outline"
                    className="text-[10px] text-green-600 dark:text-green-400"
                  >
                    rewritten
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px] text-muted-foreground">
                    unchanged
                  </Badge>
                )}
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex flex-col">
                  <span className="text-muted-foreground">Original Query</span>
                  <span
                    className="font-mono text-[11px] break-words"
                    data-testid="debug-original-query"
                  >
                    {query_rewrite.original_query}
                  </span>
                </div>
                {query_rewrite.was_rewritten && (
                  <div className="flex flex-col">
                    <span className="text-muted-foreground">Rewritten Query</span>
                    <span
                      className="font-mono text-[11px] break-words text-blue-600 dark:text-blue-400"
                      data-testid="debug-rewritten-query"
                    >
                      {query_rewrite.rewritten_query}
                    </span>
                  </div>
                )}
                <div className="flex gap-4 text-[11px]">
                  {query_rewrite.model_used && (
                    <div className="flex items-center gap-1">
                      <span className="text-muted-foreground">Model:</span>
                      <span className="font-mono" data-testid="debug-rewrite-model">
                        {query_rewrite.model_used}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <span className="text-muted-foreground">Time:</span>
                    <span className="font-mono" data-testid="debug-rewrite-time">
                      {formatMs(query_rewrite.latency_ms)}
                    </span>
                  </div>
                </div>
                {/* Story 8-0.1: Display extracted topics (AC-8.0.1.5) */}
                {query_rewrite.extracted_topics && query_rewrite.extracted_topics.length > 0 && (
                  <div className="flex flex-col mt-2">
                    <span className="text-muted-foreground">Extracted Topics:</span>
                    <div className="flex flex-wrap gap-1 mt-1" data-testid="debug-extracted-topics">
                      {query_rewrite.extracted_topics.map((topic, idx) => (
                        <Badge key={idx} variant="secondary" className="text-[10px] font-normal">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Timing Section (AC-9.15.17) */}
          <section data-testid="debug-timing">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium uppercase text-muted-foreground">Timing</span>
            </div>
            <div className="flex flex-wrap gap-4 text-xs">
              {queryRewriteMs > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Rewrite:</span>
                  <span className="font-mono font-medium" data-testid="debug-rewrite-timing">
                    {formatMs(queryRewriteMs)}
                  </span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Retrieval:</span>
                <span className="font-mono font-medium" data-testid="debug-retrieval-time">
                  {formatMs(timing.retrieval_ms)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Context:</span>
                <span className="font-mono font-medium" data-testid="debug-context-time">
                  {formatMs(timing.context_assembly_ms)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Total:</span>
                <span className="font-mono font-medium" data-testid="debug-total-time">
                  {formatMs(totalTime)}
                </span>
              </div>
            </div>
          </section>

          {/* Retrieved Chunks Section (AC-9.15.16) */}
          <section data-testid="debug-chunks">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium uppercase text-muted-foreground">
                Retrieved Chunks ({chunks_retrieved.length})
              </span>
            </div>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {chunks_retrieved.map((chunk, index) => (
                <ChunkItem key={index} chunk={chunk} index={index} />
              ))}
              {chunks_retrieved.length === 0 && (
                <p className="text-xs text-muted-foreground italic">No chunks retrieved</p>
              )}
            </div>
          </section>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
