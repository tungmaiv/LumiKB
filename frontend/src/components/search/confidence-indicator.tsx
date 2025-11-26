'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

interface ConfidenceIndicatorProps {
  confidence: number; // 0-1 float
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ConfidenceIndicator({
  confidence,
  showLabel = true,
  size = 'md',
  className,
}: ConfidenceIndicatorProps) {
  const percentage = Math.round(confidence * 100);

  // Color mapping based on UX spec thresholds
  const getConfidenceColor = (): string => {
    if (percentage >= 80) return 'bg-[#10B981]'; // Green
    if (percentage >= 50) return 'bg-[#F59E0B]'; // Amber
    return 'bg-[#EF4444]'; // Red
  };

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={cn('flex items-center gap-2', className)} data-testid="confidence-indicator">
      {showLabel && <span className={cn('text-gray-600', textSizeClasses[size])}>Confidence:</span>}
      <div className={cn('flex-1 bg-[#E5E5E5] rounded-full overflow-hidden', sizeClasses[size])}>
        <div
          className={cn('h-full transition-all duration-300', getConfidenceColor())}
          style={{ width: `${percentage}%` }}
          role="meter"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Confidence level: ${percentage}%`}
        />
      </div>
      <span className={cn('font-semibold', textSizeClasses[size])}>{percentage}%</span>
    </div>
  );
}
