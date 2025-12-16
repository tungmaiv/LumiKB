/**
 * CitationMarker Component - Epic 4, Story 4.6, AC2
 * Non-editable inline citation marker [n] for draft editing
 */

'use client';

import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CitationMarkerProps {
  /** Citation number [n] */
  number: number;
  /** Callback when marker is clicked */
  onClick?: () => void;
  /** Callback when delete button is clicked */
  onDelete?: () => void;
  /** Whether marker is highlighted (from citations panel click) */
  isHighlighted?: boolean;
}

/**
 * Renders a non-editable citation marker as a React component.
 * Used in DraftEditor to prevent accidental edits to citation markers.
 *
 * Per AC2:
 * - Marker survives text edits around it (contentEditable=false)
 * - Explicit delete via × button removes citation from panel
 * - Copy/paste preserves marker
 *
 * @example
 * <CitationMarker
 *   number={1}
 *   onClick={handleScrollToPanel}
 *   onDelete={handleRemoveCitation}
 * />
 */
export function CitationMarker({
  number,
  onClick,
  onDelete,
  isHighlighted = false,
}: CitationMarkerProps) {
  return (
    <span
      contentEditable={false}
      suppressContentEditableWarning
      className={`
        inline-flex items-center gap-0.5 px-1 mx-0.5
        text-xs font-medium rounded
        cursor-pointer select-none
        transition-colors
        ${
          isHighlighted
            ? 'bg-blue-200 text-blue-900 ring-2 ring-blue-400'
            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
        }
      `}
      onClick={(e) => {
        e.preventDefault();
        onClick?.();
      }}
      data-citation-number={number}
      data-testid={`citation-marker-${number}`}
    >
      <span className="pointer-events-none">[{number}]</span>
      {onDelete && (
        <Button
          variant="ghost"
          size="icon"
          className="h-3 w-3 p-0 hover:bg-blue-300 rounded-sm"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          aria-label={`Remove citation ${number}`}
          data-testid={`delete-citation-${number}`}
        >
          <X className="h-2 w-2" />
        </Button>
      )}
    </span>
  );
}
