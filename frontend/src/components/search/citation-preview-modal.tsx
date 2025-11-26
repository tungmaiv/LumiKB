'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ExternalLink } from 'lucide-react';
import type { Citation } from '@/components/search/citation-card';

interface CitationPreviewModalProps {
  citation: Citation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onOpenDocument: (documentId: string, charStart: number, charEnd: number) => void;
}

interface CitationContext {
  before: string;
  cited: string;
  after: string;
}

export function CitationPreviewModal({
  citation,
  open,
  onOpenChange,
  onOpenDocument,
}: CitationPreviewModalProps) {
  const [content, setContent] = useState<CitationContext | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !citation) {
      setContent(null);
      setError(null);
      return;
    }

    async function fetchContext() {
      if (!citation) return;

      try {
        setIsLoading(true);
        setError(null);

        // Calculate range for surrounding context (±200 chars)
        const start = Math.max(0, citation.charStart - 200);
        const end = citation.charEnd + 200;

        // Fetch surrounding context from backend
        const response = await fetch(
          `/api/v1/documents/${citation.documentId}/content?start=${start}&end=${end}`
        );

        if (!response.ok) {
          throw new Error('Failed to load citation context');
        }

        const fullText = await response.text();

        // Calculate relative positions in the fetched range
        const beforeEnd = citation.charStart - start;
        const citedStart = beforeEnd;
        const citedEnd = citedStart + (citation.charEnd - citation.charStart);

        // Split into before, cited, after
        const before = fullText.substring(0, citedStart);
        const cited = fullText.substring(citedStart, citedEnd);
        const after = fullText.substring(citedEnd);

        setContent({ before, cited, after });
      } catch (err) {
        console.error('Failed to fetch citation context:', err);
        setError('Failed to load full context');
        // Fallback to excerpt only
        if (citation) {
          setContent({
            before: '',
            cited: citation.excerpt,
            after: '',
          });
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchContext();
  }, [citation, open]);

  if (!citation) {
    return null;
  }

  const handleOpenDocument = () => {
    onOpenDocument(citation.documentId, citation.charStart, citation.charEnd);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-lg">{citation.documentName}</DialogTitle>
          <DialogDescription className="text-sm">
            {citation.pageNumber && `Page ${citation.pageNumber}`}
            {citation.pageNumber && citation.sectionHeader && ' • '}
            {citation.sectionHeader}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          ) : content ? (
            <div className="bg-muted/30 rounded-lg p-4 prose prose-sm max-w-none">
              {content.before && (
                <p className="text-muted-foreground italic mb-2">{content.before}</p>
              )}
              <p className="bg-yellow-100 dark:bg-yellow-800 px-2 py-1 rounded font-medium my-2">
                {content.cited}
              </p>
              {content.after && (
                <p className="text-muted-foreground italic mt-2">{content.after}</p>
              )}
            </div>
          ) : null}
        </div>

        <DialogFooter className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            data-testid="citation-preview-close"
          >
            Close
          </Button>
          <Button onClick={handleOpenDocument} data-testid="citation-preview-open-document">
            <ExternalLink className="w-4 h-4 mr-2" />
            Open Full Document
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
