/**
 * ViewModeToggle Component (Story 7-31)
 *
 * Toggle between Original and Markdown view modes in the chunk viewer.
 *
 * AC-7.31.1: Toggle Component - renders in viewer header with Original | Markdown options
 * AC-7.31.3: Disabled When Unavailable - markdown option grayed out when not available
 * AC-7.31.5: Visual Indication - clear selected state styling
 */

'use client';

import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { FileText, Code } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export type ViewMode = 'original' | 'markdown';

interface ViewModeToggleProps {
  /** Whether markdown content is available for the document */
  markdownAvailable: boolean;
  /** Current view mode */
  value: ViewMode;
  /** Callback when mode changes */
  onChange: (mode: ViewMode) => void;
}

/**
 * Toggle component for switching between Original and Markdown view modes.
 *
 * Features:
 * - Two options: Original (FileText icon) and Markdown (Code icon)
 * - Markdown option disabled with tooltip when not available
 * - Clear visual indication of selected state via data-state attribute
 *
 * @example
 * <ViewModeToggle
 *   markdownAvailable={true}
 *   value="markdown"
 *   onChange={(mode) => setViewMode(mode)}
 * />
 */
export function ViewModeToggle({
  markdownAvailable,
  value,
  onChange,
}: ViewModeToggleProps) {
  // Handle value change from toggle group
  const handleChange = (newValue: string) => {
    // Only trigger onChange for valid mode values
    // ToggleGroup may return empty string when deselecting (type="single" allows deselect)
    if (newValue === 'original' || newValue === 'markdown') {
      onChange(newValue);
    }
  };

  return (
    <TooltipProvider>
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={handleChange}
        variant="outline"
        className="border rounded-md"
      >
        <ToggleGroupItem
          value="original"
          aria-label="Original view"
          className="px-3 py-1.5 text-sm gap-1.5"
        >
          <FileText className="h-4 w-4" />
          Original
        </ToggleGroupItem>

        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex">
              <ToggleGroupItem
                value="markdown"
                aria-label="Markdown view"
                disabled={!markdownAvailable}
                className="px-3 py-1.5 text-sm gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Code className="h-4 w-4" />
                Markdown
              </ToggleGroupItem>
            </span>
          </TooltipTrigger>
          {!markdownAvailable && (
            <TooltipContent>
              <p>Markdown not available for this document</p>
            </TooltipContent>
          )}
        </Tooltip>
      </ToggleGroup>
    </TooltipProvider>
  );
}
