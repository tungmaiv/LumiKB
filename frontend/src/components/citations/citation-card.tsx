'use client';

import { FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CitationCardProps {
  title: string;
  excerpt: string;
  source: string;
  relevanceScore?: number;
}

export function CitationCard({
  title,
  excerpt,
  source,
  relevanceScore,
}: CitationCardProps): React.ReactElement {
  return (
    <Card className="transition-colors hover:bg-accent/50">
      <CardHeader className="pb-2">
        <div className="flex items-start gap-2">
          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <div className="flex-1 min-w-0">
            <CardTitle className="truncate text-sm font-medium">{title}</CardTitle>
            <p className="truncate text-xs text-muted-foreground">{source}</p>
          </div>
          {relevanceScore !== undefined && (
            <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {Math.round(relevanceScore * 100)}%
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <p className="line-clamp-2 text-xs text-muted-foreground">{excerpt}</p>
      </CardContent>
    </Card>
  );
}
