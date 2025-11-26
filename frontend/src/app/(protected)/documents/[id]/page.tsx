'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  kb_id: string;
  content?: string;
  metadata?: {
    page_count?: number;
    file_size_bytes?: number;
  };
}

export default function DocumentViewerPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const highlightRef = useRef<HTMLSpanElement>(null);

  const documentId = params.id as string;
  const highlightParam = searchParams.get('highlight');

  const [document, setDocument] = useState<Document | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Parse highlight parameter
  const highlightRange = highlightParam
    ? (() => {
        try {
          const [startStr, endStr] = highlightParam.split('-');
          const start = parseInt(startStr, 10);
          const end = parseInt(endStr, 10);
          if (isNaN(start) || isNaN(end)) {
            console.warn('Invalid highlight parameter:', highlightParam);
            return null;
          }
          return { start, end };
        } catch (err) {
          console.warn('Failed to parse highlight parameter:', err);
          return null;
        }
      })()
    : null;

  useEffect(() => {
    async function fetchDocument() {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`/api/v1/documents/${documentId}`);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Document not found or you do not have access');
          }
          throw new Error('Failed to load document');
        }

        const data = await response.json();
        setDocument(data);
      } catch (err) {
        console.error('Failed to fetch document:', err);
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setIsLoading(false);
      }
    }

    if (documentId) {
      fetchDocument();
    }
  }, [documentId]);

  // Scroll to highlighted section when content loads
  useEffect(() => {
    if (highlightRef.current && highlightRange && document?.content) {
      try {
        highlightRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      } catch (err) {
        // Fallback for browsers that don't support smooth scrolling
        highlightRef.current.scrollIntoView();
      }
    }
  }, [highlightRange, document?.content]);

  const handleBackToSearch = () => {
    router.back();
  };

  if (isLoading) {
    return (
      <div className="flex h-full flex-col">
        <div className="border-b p-4">
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{error || 'Document not found'}</AlertDescription>
          <Button onClick={handleBackToSearch} className="mt-2" variant="outline">
            Go Back
          </Button>
        </Alert>
      </div>
    );
  }

  // Render content with highlight
  const renderContent = () => {
    if (!document.content) {
      return (
        <Alert>
          <AlertDescription>Document content is not available.</AlertDescription>
        </Alert>
      );
    }

    if (highlightRange) {
      const { start, end } = highlightRange;
      const before = document.content.substring(0, start);
      const highlighted = document.content.substring(start, end);
      const after = document.content.substring(end);

      return (
        <div className="prose prose-sm max-w-none whitespace-pre-wrap">
          <span>{before}</span>
          <span
            ref={highlightRef}
            className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded"
            data-testid="highlighted-passage"
          >
            {highlighted}
          </span>
          <span>{after}</span>
        </div>
      );
    }

    return <div className="prose prose-sm max-w-none whitespace-pre-wrap">{document.content}</div>;
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-white p-4">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          {highlightParam && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBackToSearch}
              data-testid="back-to-search"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back to Search
            </Button>
          )}
          <div className="flex-1">
            <h1 className="text-2xl font-bold truncate" title={document.name}>
              {document.name}
            </h1>
            {document.metadata && (
              <p className="text-sm text-gray-600 mt-1">
                {document.metadata.page_count && <>Pages: {document.metadata.page_count}</>}
                {document.metadata.page_count && document.metadata.file_size_bytes && ' • '}
                {document.metadata.file_size_bytes && (
                  <>Size: {(document.metadata.file_size_bytes / 1024).toFixed(1)} KB</>
                )}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8 bg-gray-50">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm p-8">{renderContent()}</div>
      </div>
    </div>
  );
}
