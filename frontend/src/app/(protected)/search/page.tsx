'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useSearchStream } from '@/lib/hooks/use-search-stream';
import { CitationMarker } from '@/components/search/citation-marker';
import { CitationCard, type Citation } from '@/components/search/citation-card';
import { CitationPreviewModal } from '@/components/search/citation-preview-modal';
import { ConfidenceIndicator } from '@/components/search/confidence-indicator';
import { SearchResultCard, type SearchResult } from '@/components/search/search-result-card';
import { DraftSelectionPanel } from '@/components/search/draft-selection-panel';
import { VerifyAllButton } from '@/components/search/verify-all-button';
import { VerificationControls } from '@/components/search/verification-controls';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useDraftStore, type DraftResult } from '@/lib/stores/draft-store';
import { useVerificationStore } from '@/lib/hooks/use-verification';
import { similarSearch } from '@/lib/api/search';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { Check, FileText } from 'lucide-react';
import { GenerationModal } from '@/components/generation/generation-modal';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('q') || '';
  const chunkId = searchParams.get('chunk_id'); // Similar search param (Story 3.8)
  const kbIdsParam = searchParams.get('kb_ids');
  const kbIds = kbIdsParam ? kbIdsParam.split(',') : null;

  const { answer, citations, confidence, isLoading, error } = useSearchStream(query, kbIds);
  const [selectedCitation, setSelectedCitation] = useState<number | null>(null);
  const [citationsPanelOpen, setCitationsPanelOpen] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewCitation, setPreviewCitation] = useState<Citation | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [generationModalOpen, setGenerationModalOpen] = useState(false);

  const { addToDraft } = useDraftStore();
  const { isVerifying, currentCitationIndex, verifiedCitations } = useVerificationStore();

  // Story 3.10: Auto-open preview when verification mode active (AC4)
  useEffect(() => {
    if (isVerifying && citations[currentCitationIndex]) {
      setPreviewCitation(citations[currentCitationIndex]);
      setPreviewModalOpen(true);

      // Scroll to current citation card in panel
      const element = document.getElementById(
        `citation-card-${citations[currentCitationIndex].number}`
      );
      if (element) {
        try {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch {
          element.scrollIntoView();
        }
      }
    }
  }, [isVerifying, currentCitationIndex, citations]);

  const handleCitationClick = (number: number) => {
    setSelectedCitation(number);
    // Scroll to citation card in right panel
    const element = document.getElementById(`citation-card-${number}`);
    if (element) {
      try {
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch {
        // Fallback for browsers that don't support smooth scrolling
        element.scrollIntoView();
      }
    }
  };

  // Clear highlight after 2 seconds
  useEffect(() => {
    if (selectedCitation !== null) {
      const timer = setTimeout(() => setSelectedCitation(null), 2000);
      return () => clearTimeout(timer);
    }
  }, [selectedCitation]);

  const handlePreview = (citation: Citation) => {
    setPreviewCitation(citation);
    setPreviewModalOpen(true);
  };

  const handleOpenDocument = (documentId: string, charStart: number, charEnd: number) => {
    router.push(`/documents/${documentId}?highlight=${charStart}-${charEnd}`);
  };

  // Handle similar search (Story 3.8, AC3)
  useEffect(() => {
    if (!chunkId) return;

    const fetchSimilarResults = async () => {
      setSimilarLoading(true);
      try {
        const response = await similarSearch({ chunkId, kbIds, limit: 10 });

        // Convert API response to SearchResult format
        const results: SearchResult[] = response.results.map((r) => ({
          documentId: r.documentId,
          documentName: r.documentName,
          kbId: r.kbId,
          kbName: r.kbName,
          chunkText: r.chunkText,
          relevanceScore: r.relevanceScore,
          pageNumber: r.pageNumber,
          sectionHeader: r.sectionHeader,
          updatedAt: new Date().toISOString(), // Backend doesn't return this yet
          charStart: r.charStart,
          charEnd: r.charEnd,
        }));

        setSearchResults(results);
      } catch (err: unknown) {
        const error = err as { detail?: string };
        toast.error(error.detail || 'Failed to find similar content');
      } finally {
        setSimilarLoading(false);
      }
    };

    fetchSimilarResults();
  }, [chunkId, kbIds]);

  // Action handlers for SearchResultCard (Story 3.8)
  const handleUseInDraft = (result: SearchResult) => {
    const draftResult: DraftResult = {
      chunkId: result.documentId, // Using documentId as chunkId (temp - need actual chunk_id)
      documentId: result.documentId,
      documentName: result.documentName,
      chunkText: result.chunkText.substring(0, 100), // Truncate for panel display
      kbId: result.kbId,
      kbName: result.kbName,
      relevanceScore: result.relevanceScore,
    };

    addToDraft(draftResult);
    toast.success('Added to draft selection', {
      description: result.documentName,
      duration: 2000,
    });
  };

  const handleView = (documentId: string) => {
    router.push(`/documents/${documentId}`);
  };

  const handleFindSimilar = (result: SearchResult) => {
    // Navigate to similar search with chunk_id param
    const params = new URLSearchParams({
      q: `Similar to: ${result.documentName}`,
      chunk_id: result.documentId, // Using documentId as chunkId (temp)
    });
    router.push(`/search?${params.toString()}`);
  };

  const handleGenerate = (params: { templateId: string; context: string }) => {
    // Story 4.9: Navigate to generation page with template and context
    // This will be wired to the actual generation endpoint in later stories
    toast.success('Generation started', {
      description: `Using template: ${params.templateId}`,
    });
    console.log('Generation params:', params);
    // TODO: Wire to /api/v1/generate/stream endpoint (Story 4.5)
  };

  const renderAnswerWithCitations = (text: string) => {
    // Parse text and replace [n] with CitationMarker components
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const num = parseInt(match[1], 10);
        const citation = citations.find((c) => c.number === num);
        const isCurrentlyHighlighted =
          isVerifying && citations[currentCitationIndex]?.number === num;
        const isVerified = verifiedCitations.has(num);

        return (
          <span
            key={index}
            className={cn(
              'inline-flex items-center gap-1',
              isCurrentlyHighlighted && 'ring-2 ring-primary ring-offset-2 rounded'
            )}
          >
            <CitationMarker
              number={num}
              onClick={handleCitationClick}
              documentName={citation?.documentName}
              excerpt={citation?.excerpt}
              pageNumber={citation?.pageNumber}
            />
            {isVerified && <Check className="inline h-3 w-3 text-green-600" />}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Error state
  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{error}</AlertDescription>
          <Button onClick={() => window.location.reload()} className="mt-2" variant="outline">
            Try Again
          </Button>
        </Alert>
      </div>
    );
  }

  // Empty state
  if (!isLoading && answer === '' && confidence === null && query) {
    return (
      <div className="flex h-full">
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto mt-12 text-center">
            <h2 className="text-2xl font-bold mb-4">No matches found</h2>
            <p className="text-gray-600 mb-6">Try different terms or search all Knowledge Bases</p>
            <div className="space-y-2">
              <p className="text-sm text-[#3B82F6]">Suggested actions:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {kbIds && <li>• Search all Knowledge Bases (currently filtered)</li>}
                <li>• Try broader keywords</li>
              </ul>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-full relative">
      {/* Center Panel: Search Results */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Search Results</h2>
          <div className="flex items-center gap-2">
            {/* Generate Draft Button (Story 4.9) */}
            <Button
              variant="default"
              size="sm"
              onClick={() => setGenerationModalOpen(true)}
              disabled={!answer}
            >
              <FileText className="h-4 w-4 mr-2" />
              Generate Draft
            </Button>
            {/* Mobile/Tablet Citations Button */}
            <Button
              variant="outline"
              size="sm"
              className="xl:hidden"
              onClick={() => setCitationsPanelOpen(!citationsPanelOpen)}
            >
              Citations ({citations.length})
            </Button>
          </div>
        </div>
        {query && <p className="text-sm text-gray-600 mb-6">Query: &quot;{query}&quot;</p>}

        {/* Answer Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          {isLoading && !answer ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          ) : (
            <>
              <div
                className="prose max-w-none text-base leading-relaxed"
                data-testid="search-answer"
                role="region"
                aria-live="polite"
                aria-label="Search answer"
              >
                {renderAnswerWithCitations(answer)}
              </div>
              {confidence !== null && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <ConfidenceIndicator confidence={confidence} />
                </div>
              )}

              {/* Verify All Button (Story 3.10, AC1) */}
              {answer && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <VerifyAllButton
                    answerId={query} // Using query as answerId for now
                    citations={citations}
                    isStreaming={isLoading}
                  />
                </div>
              )}

              {/* Verification Controls (Story 3.10, AC2, AC3, AC5) */}
              {isVerifying && <VerificationControls citations={citations} />}
            </>
          )}
        </div>

        {/* Search Result Cards (Story 3.8) */}
        {(searchResults.length > 0 || similarLoading) && (
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {chunkId ? 'Similar Results' : 'Sources'}
            </h3>
            {similarLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : (
              <div className="space-y-4">
                {searchResults.map((result, index) => (
                  <SearchResultCard
                    key={`${result.documentId}-${index}`}
                    result={result}
                    query={query}
                    onUseInDraft={handleUseInDraft}
                    onView={handleView}
                    onFindSimilar={handleFindSimilar}
                    index={index}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Right Panel: Citations */}
      <aside
        className={`
          w-80 border-l border-gray-200 overflow-y-auto p-6 bg-gray-50
          xl:block
          lg:${citationsPanelOpen ? 'block' : 'hidden'}
          max-lg:${citationsPanelOpen ? 'absolute right-0 top-0 h-full z-10 shadow-lg' : 'hidden'}
        `}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Citations</h3>
          {citations.length > 0 && (
            <span className="text-sm text-gray-600">({citations.length})</span>
          )}
        </div>

        {isLoading && citations.length === 0 ? (
          <p className="text-sm text-gray-500">Loading citations...</p>
        ) : citations.length === 0 ? (
          <p className="text-sm text-gray-500">No citations yet</p>
        ) : (
          <div className="space-y-3">
            {citations.map((citation) => (
              <CitationCard
                key={citation.number}
                citation={citation}
                highlighted={selectedCitation === citation.number}
                onPreview={handlePreview}
                onOpenDocument={handleOpenDocument}
              />
            ))}
          </div>
        )}
      </aside>

      {/* Citation Preview Modal */}
      <CitationPreviewModal
        citation={previewCitation}
        open={previewModalOpen}
        onOpenChange={setPreviewModalOpen}
        onOpenDocument={handleOpenDocument}
      />

      {/* Draft Selection Panel (Story 3.8, AC4 + Story 4.4, AC6) */}
      <DraftSelectionPanel kbId={kbIds?.[0] || ''} />

      {/* Generation Modal (Story 4.9) */}
      <GenerationModal
        open={generationModalOpen}
        onClose={() => setGenerationModalOpen(false)}
        onGenerate={handleGenerate}
      />
    </div>
  );
}
