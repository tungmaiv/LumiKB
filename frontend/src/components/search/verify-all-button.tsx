'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertTriangle } from 'lucide-react';
import { useVerificationStore } from '@/lib/hooks/use-verification';
import { type Citation } from './citation-card';

interface VerifyAllButtonProps {
  answerId: string;
  citations: Citation[];
  isStreaming: boolean;
}

export function VerifyAllButton({ answerId, citations, isStreaming }: VerifyAllButtonProps) {
  const startVerification = useVerificationStore((s) => s.startVerification);
  const isAllVerified = useVerificationStore((s) => s.isAllVerified());
  const { verified, total } = useVerificationStore((s) => s.getProgress());

  if (citations.length === 0) {
    return (
      <div className="text-sm text-amber-600 dark:text-amber-400 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        No sources cited - use with caution
      </div>
    );
  }

  if (citations.length === 1) {
    // Single citation - just show preview button
    return (
      <Button variant="outline" size="sm" disabled={isStreaming}>
        Preview Citation
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Button
        variant="outline"
        size="sm"
        onClick={() => startVerification(answerId, citations.length)}
        disabled={isStreaming}
        aria-label={`Verify all ${citations.length} citations systematically`}
      >
        <CheckCircle className="h-4 w-4 mr-2" />
        Verify All ({citations.length} citations)
      </Button>

      {isAllVerified && (
        <Badge variant="default" className="bg-green-700 text-white dark:bg-green-600">
          ✓ All verified
        </Badge>
      )}

      {verified > 0 && !isAllVerified && (
        <span className="text-sm text-muted-foreground">
          {verified}/{total} verified
        </span>
      )}
    </div>
  );
}
