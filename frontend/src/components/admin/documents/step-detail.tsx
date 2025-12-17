/**
 * Step Detail Component
 *
 * Story 9-10: Document Timeline UI
 * AC5: Click step to see detailed metrics
 * AC6: Error steps show error type and full error message
 */
import { formatBytes, formatNumber } from '@/lib/utils';

interface StepMetrics {
  file_size?: number;
  mime_type?: string;
  pages_extracted?: number;
  text_length?: number;
  parser_used?: string;
  chunks_created?: number;
  avg_chunk_size?: number;
  vectors_generated?: number;
  embedding_model?: string;
  points_indexed?: number;
  collection_name?: string;
  [key: string]: unknown;
}

interface StepDetailProps {
  stepName: string;
  status: string;
  metrics: StepMetrics | null | undefined;
  errorMessage: string | null | undefined;
}

interface MetricItemProps {
  label: string;
  value: string | number | null | undefined;
}

function MetricItem({ label, value }: MetricItemProps) {
  return (
    <div className="flex justify-between py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? '—'}</span>
    </div>
  );
}

export function StepDetail({ stepName, status, metrics, errorMessage }: StepDetailProps) {
  return (
    <div className="mt-3 pt-3 border-t" data-testid="step-detail">
      {/* Error message for failed steps */}
      {status === 'failed' && errorMessage && (
        <div
          className="mb-3 p-2 rounded bg-destructive/10 text-destructive text-sm"
          data-testid="step-error-message"
        >
          <span className="font-medium">Error: </span>
          {errorMessage}
        </div>
      )}

      {/* Step-specific metrics */}
      <div className="grid grid-cols-1 gap-1 text-sm">
        {stepName === 'upload' && (
          <>
            <MetricItem
              label="File Size"
              value={metrics?.file_size ? formatBytes(metrics.file_size) : null}
            />
            <MetricItem label="MIME Type" value={metrics?.mime_type} />
          </>
        )}
        {stepName === 'parse' && (
          <>
            <MetricItem label="Pages Extracted" value={metrics?.pages_extracted} />
            <MetricItem
              label="Text Length"
              value={metrics?.text_length ? formatNumber(metrics.text_length) : null}
            />
            <MetricItem label="Parser" value={metrics?.parser_used} />
          </>
        )}
        {stepName === 'chunk' && (
          <>
            <MetricItem label="Chunks Created" value={metrics?.chunks_created} />
            <MetricItem
              label="Avg Chunk Size"
              value={metrics?.avg_chunk_size ? formatNumber(metrics.avg_chunk_size) : null}
            />
          </>
        )}
        {stepName === 'embed' && (
          <>
            <MetricItem label="Vectors Generated" value={metrics?.vectors_generated} />
            <MetricItem label="Embedding Model" value={metrics?.embedding_model} />
          </>
        )}
        {stepName === 'index' && (
          <>
            <MetricItem label="Points Indexed" value={metrics?.points_indexed} />
            <MetricItem label="Collection" value={metrics?.collection_name} />
          </>
        )}

        {/* Show no metrics message if no metrics available */}
        {!metrics && status !== 'failed' && (
          <div className="text-muted-foreground text-center py-2">No metrics available</div>
        )}
      </div>
    </div>
  );
}
