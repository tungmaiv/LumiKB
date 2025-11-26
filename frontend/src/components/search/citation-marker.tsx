'use client';

import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface CitationMarkerProps {
  number: number;
  onClick: (number: number) => void;
  documentName?: string;
  excerpt?: string;
  pageNumber?: number;
  verified?: boolean; // For future Verify All feature
  className?: string;
}

export function CitationMarker({
  number,
  onClick,
  documentName,
  excerpt,
  pageNumber,
  verified = false,
  className,
}: CitationMarkerProps) {
  const handleClick = () => {
    onClick(number);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick(number);
    }
  };

  // Truncate excerpt to 120 chars for tooltip
  const truncatedExcerpt = excerpt
    ? excerpt.length > 120
      ? `${excerpt.substring(0, 120)}...`
      : excerpt
    : '';

  const tooltipContent =
    documentName || excerpt ? (
      <div className="max-w-xs">
        {documentName && (
          <p className="font-semibold text-xs mb-1">
            {documentName}
            {pageNumber && ` (p. ${pageNumber})`}
          </p>
        )}
        {truncatedExcerpt && <p className="text-xs text-muted-foreground">{truncatedExcerpt}</p>}
      </div>
    ) : null;

  const badge = (
    <Badge
      className={cn(
        'cursor-pointer bg-[#0066CC] text-white hover:bg-[#004C99]',
        'focus:ring-2 focus:ring-[#0066CC] focus:ring-offset-2 focus:outline-none',
        'transition-colors',
        'inline-flex items-center justify-center',
        'ml-0.5 mr-0.5',
        verified && 'bg-[#10B981] hover:bg-[#059669]', // Green if verified
        className
      )}
      role="button"
      tabIndex={0}
      aria-label={`Citation ${number}${documentName ? ` from ${documentName}` : ''}`}
      data-testid={`citation-marker-${number}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      [{number}]
    </Badge>
  );

  // Only wrap in Tooltip if we have content to show
  if (!tooltipContent) {
    return badge;
  }

  return (
    <Tooltip delayDuration={300}>
      <TooltipTrigger asChild>{badge}</TooltipTrigger>
      <TooltipContent>{tooltipContent}</TooltipContent>
    </Tooltip>
  );
}
