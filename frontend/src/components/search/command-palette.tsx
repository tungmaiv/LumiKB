'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SearchIcon } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { Dialog, DialogContent } from '@/components/ui/dialog';

interface QuickSearchResult {
  document_id: string;
  document_name: string;
  kb_id: string;
  kb_name: string;
  excerpt: string;
  relevance_score: number;
}

interface QuickSearchResponse {
  query: string;
  results: QuickSearchResult[];
  kb_count: number;
  response_time_ms: number;
}

interface CommandPaletteProps {
  /**
   * Whether the palette is open
   */
  open: boolean;
  /**
   * Callback when open state changes
   */
  onOpenChange: (open: boolean) => void;
}

/**
 * CommandPalette - Quick search overlay triggered by ⌘K/Ctrl+K (Story 3.7, AC1-AC7)
 *
 * Features:
 * - Global keyboard shortcut ⌘K/Ctrl+K
 * - Debounced search (300ms)
 * - Arrow key navigation
 * - Top 5 results
 * - Navigate to full search on select
 */
export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QuickSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounced search effect (AC10)
  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    const controller = new AbortController(); // AC10: request cancellation
    const timeoutId = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/v1/search/quick', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, kb_ids: null }), // AC6: cross-KB default
          signal: controller.signal,
        });

        if (!response.ok) {
          if (response.status === 503) {
            throw new Error('Search temporarily unavailable'); // AC9
          }
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const data: QuickSearchResponse = await response.json();
        setResults(data.results);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err.message); // AC9
        }
      } finally {
        setLoading(false);
      }
    }, 300); // AC10: 300ms debounce

    return () => {
      clearTimeout(timeoutId);
      controller.abort(); // AC10: cancel previous requests
    };
  }, [query]);

  // Handle result selection (AC5)
  const handleSelect = (documentId: string) => {
    onOpenChange(false); // Close palette
    // Navigate to full search view with the query pre-filled
    router.push(`/search?q=${encodeURIComponent(query)}&highlight=${documentId}`);
  };

  // Reset state when closed (AC7)
  useEffect(() => {
    if (!open) {
      setQuery('');
      setResults([]);
      setError(null);
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 shadow-lg">
        <Command className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-group]]:px-2 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5">
          <CommandInput
            placeholder="Search knowledge bases..." // AC3
            value={query}
            onValueChange={setQuery}
            autoFocus // AC1: focus on open
          />
          <CommandList>
            {/* Empty state (AC9) */}
            <CommandEmpty>
              {error ? (
                <div className="py-6 text-center text-sm">
                  <p className="text-destructive">{error}</p>
                  <button
                    onClick={() => router.push(`/search?q=${encodeURIComponent(query)}`)}
                    className="mt-2 text-primary underline-offset-4 hover:underline"
                  >
                    Open full search
                  </button>
                </div>
              ) : query.length < 2 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  Type at least 2 characters to search
                </div>
              ) : (
                <div className="py-6 text-center text-sm">
                  <p>No matches found</p>
                  <p className="mt-1 text-muted-foreground">
                    Try broader terms or{' '}
                    <button
                      onClick={() => router.push(`/search?q=${encodeURIComponent(query)}`)}
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      search all Knowledge Bases
                    </button>
                  </p>
                </div>
              )}
            </CommandEmpty>

            {/* Results (AC2, AC4) */}
            {results.length > 0 && (
              <CommandGroup heading="Results">
                {results.map((result) => (
                  <CommandItem
                    key={result.document_id}
                    value={result.document_id}
                    onSelect={() => handleSelect(result.document_id)} // AC5
                    className="flex flex-col items-start gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <SearchIcon className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{result.document_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{result.kb_name}</span>
                      <span>•</span>
                      <span>{Math.round(result.relevance_score * 100)}% match</span>
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{result.excerpt}</p>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>

          {/* Loading indicator (AC10) */}
          {loading && (
            <div className="border-t px-4 py-2 text-xs text-muted-foreground">Searching...</div>
          )}
        </Command>
      </DialogContent>
    </Dialog>
  );
}
