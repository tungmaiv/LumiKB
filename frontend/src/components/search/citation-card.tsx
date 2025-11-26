'use client';

import * as React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import { useVerificationStore } from '@/lib/hooks/use-verification';

export interface Citation {
  number: number;
  documentId: string;
  documentName: string;
  pageNumber?: number;
  sectionHeader?: string;
  excerpt: string;
  charStart: number;
  charEnd: number;
}

interface CitationCardProps {
  citation: Citation;
  onPreview: (citation: Citation) => void;
  onOpenDocument: (documentId: string, charStart: number, charEnd: number) => void;
  highlighted?: boolean;
  className?: string;
}

export function CitationCard({
  citation,
  onPreview,
  onOpenDocument,
  highlighted = false,
  className,
}: CitationCardProps) {
  const {
    number,
    documentId,
    documentName,
    pageNumber,
    sectionHeader,
    excerpt,
    charStart,
    charEnd,
  } = citation;

  // Story 3.10: Verification state (AC2, AC3)
  const { isVerifying, currentCitationIndex, verifiedCitations } = useVerificationStore();
  const isCurrentlyHighlighted = isVerifying && currentCitationIndex === number - 1; // number is 1-indexed, index is 0-indexed
  const isVerified = verifiedCitations.has(number);

  const handlePreview = () => {
    onPreview(citation);
  };

  const handleOpenDocument = () => {
    onOpenDocument(documentId, charStart, charEnd);
  };

  // Truncate document name if > 40 chars
  const truncatedName =
    documentName.length > 40 ? `${documentName.substring(0, 37)}...` : documentName;

  // Truncate excerpt if > 200 chars
  const truncatedExcerpt = excerpt.length > 200 ? `${excerpt.substring(0, 197)}...` : excerpt;

  return (
    <Card
      id={`citation-card-${number}`}
      className={cn(
        'p-4 hover:shadow-md transition-shadow border border-[#E5E5E5]',
        highlighted && 'ring-2 ring-[#0066CC] border-[#0066CC]',
        isCurrentlyHighlighted && 'ring-2 ring-primary bg-accent',
        isVerified && 'border-green-500',
        className
      )}
      data-testid={`citation-card-${number}`}
    >
      <div className="flex items-start gap-2">
        <Badge className={cn('bg-[#0066CC] text-white shrink-0', isVerified && 'bg-green-700')}>
          [{number}]{isVerified && <Check className="inline h-3 w-3 ml-1" />}
        </Badge>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <h4 className="font-semibold text-sm truncate" title={documentName}>
              {truncatedName}
            </h4>
            {isVerified && (
              <Badge variant="default" className="bg-green-700 text-white text-xs">
                Verified ✓
              </Badge>
            )}
          </div>
          {(pageNumber || sectionHeader) && (
            <p className="text-xs text-gray-600 mt-1">
              {pageNumber && `Page ${pageNumber}`}
              {pageNumber && sectionHeader && ' • '}
              {sectionHeader}
            </p>
          )}
          <div className="text-sm mt-2 bg-gray-50 p-2 rounded">{truncatedExcerpt}</div>
          <div className="flex gap-2 mt-3">
            <Button variant="secondary" size="sm" onClick={handlePreview} className="text-xs">
              Preview
            </Button>
            <Button variant="ghost" size="sm" onClick={handleOpenDocument} className="text-xs">
              Open Document
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
