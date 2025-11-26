'use client';

import * as React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { CitationMarker } from './citation-marker';
import { HighlightedText } from '@/components/ui/highlighted-text';
import { useExplanation } from '@/lib/hooks/use-explanation';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronUp } from 'lucide-react';

export interface SearchResult {
  documentId: string;
  documentName: string;
  kbId: string;
  kbName: string;
  chunkText: string;
  relevanceScore: number;
  pageNumber?: number;
  sectionHeader?: string;
  updatedAt: string; // ISO timestamp
  citationNumbers?: number[]; // If cited in answer
  charStart: number;
  charEnd: number;
}

interface SearchResultCardProps {
  result: SearchResult;
  query: string; // Story 3.9: needed for explanation
  onUseInDraft: (result: SearchResult) => void;
  onView: (documentId: string) => void;
  onFindSimilar: (result: SearchResult) => void;
  index: number;
  className?: string;
}

export function SearchResultCard({
  result,
  query,
  onUseInDraft,
  onView,
  onFindSimilar,
  index,
  className,
}: SearchResultCardProps) {
  const {
    documentId,
    documentName,
    kbName,
    chunkText,
    relevanceScore,
    updatedAt,
    citationNumbers,
  } = result;

  // Story 3.9: Fetch explanation (AC4, AC5)
  const { data: explanation, isLoading: explanationLoading } = useExplanation(query, result);

  // Story 3.9: Expandable detail panel (AC3)
  const [isExpanded, setIsExpanded] = React.useState(false);

  const handleUseInDraft = () => {
    onUseInDraft(result);
  };

  const handleView = () => {
    onView(documentId);
  };

  const handleFindSimilar = () => {
    onFindSimilar(result);
  };

  // Format relevance score as percentage
  const relevancePercentage = Math.round(relevanceScore * 100);

  // Format relative timestamp
  const relativeTime = formatDistanceToNow(new Date(updatedAt), {
    addSuffix: true,
  });

  // Get relevance score color
  const getRelevanceColor = (): string => {
    if (relevancePercentage >= 80) return 'text-[#10B981]'; // Green
    if (relevancePercentage >= 60) return 'text-[#F59E0B]'; // Amber
    return 'text-gray-600';
  };

  // Story 3.9: Get match quality label (AC3)
  const getMatchQuality = (score: number): string => {
    if (score >= 0.9) return 'Very strong match';
    if (score >= 0.75) return 'Strong match';
    if (score >= 0.6) return 'Good match';
    return 'Moderate match';
  };

  return (
    <Card
      className={cn('p-4 hover:shadow-md transition-shadow border border-gray-200', className)}
      data-testid={`search-result-card-${index}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2">
          <span className="text-2xl">📄</span>
          <div>
            <h3 className="font-semibold">{documentName}</h3>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge variant="secondary" className="text-xs">
                {kbName}
              </Badge>
              <span className={cn('text-sm font-medium', getRelevanceColor())}>
                {relevancePercentage}% match
              </span>
              <span className="text-xs text-gray-500">{relativeTime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Story 3.9: Excerpt with keyword highlighting (AC2) */}
      <p className="text-sm mt-3 text-gray-700">
        <HighlightedText text={chunkText} keywords={explanation?.keywords || []} />
      </p>
      {citationNumbers && citationNumbers.length > 0 && (
        <div className="flex gap-1 mt-2">
          {citationNumbers.map((num) => (
            <CitationMarker key={num} number={num} onClick={() => {}} />
          ))}
        </div>
      )}

      {/* Story 3.9: Relevance Explanation Section (AC1, AC3) */}
      <div className="mt-3 border-t pt-3">
        {explanationLoading ? (
          <Skeleton className="h-8 w-full" />
        ) : explanation ? (
          <>
            <div className="text-sm">
              <span className="font-medium text-muted-foreground">Relevant because: </span>
              <span>{explanation.explanation}</span>
            </div>

            {/* Expand/Collapse Button (AC3, AC7) */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-2 text-xs h-8"
              aria-label={
                isExpanded
                  ? 'Hide detailed relevance explanation'
                  : 'Show detailed relevance explanation'
              }
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3 mr-1" />
                  Show more
                </>
              )}
            </Button>

            {/* Detail Panel (AC3, AC7, AC8) */}
            {isExpanded && (
              <div
                className="mt-3 p-3 bg-muted rounded-md space-y-3"
                role="region"
                aria-labelledby={`explanation-heading-${index}`}
              >
                <div id={`explanation-heading-${index}`} className="sr-only">
                  Detailed relevance explanation
                </div>

                {/* Semantic Distance (AC3) */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Semantic Match</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline">{relevancePercentage}%</Badge>
                    <span className="text-sm">{getMatchQuality(relevanceScore)}</span>
                  </div>
                </div>

                {/* Matching Concepts (AC3) */}
                {explanation.concepts.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Matching Concepts</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {explanation.concepts.map((concept, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {concept}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Related Documents (AC3, AC8 - responsive grid) */}
                {explanation.relatedDocuments.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Related Documents</p>
                    <div className="mt-2 space-y-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1">
                      {explanation.relatedDocuments.map((doc) => (
                        <button
                          key={doc.docId}
                          onClick={() => onFindSimilar(result)}
                          className="flex items-center justify-between w-full p-2 text-left hover:bg-accent rounded text-xs min-h-[44px]"
                          aria-label={`Find content similar to ${doc.docName}`}
                        >
                          <span className="truncate">{doc.docName}</span>
                          <span className="text-muted-foreground ml-2 whitespace-nowrap">
                            {Math.round(doc.relevance * 100)}%
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        ) : null}
      </div>
      <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleUseInDraft}
          className="text-xs"
          aria-label="Add to draft selection"
        >
          Use in Draft
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleView}
          className="text-xs"
          aria-label={`View ${documentName}`}
        >
          View
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleFindSimilar}
          className="text-xs"
          aria-label={`Find content similar to ${documentName}`}
        >
          Similar
        </Button>
      </div>
    </Card>
  );
}
