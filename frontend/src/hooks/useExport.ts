'use client';

import { useState } from 'react';

export type ExportFormat = 'docx' | 'pdf' | 'markdown';

interface UseExportOptions {
  draftId: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function useExport({ draftId, onSuccess, onError }: UseExportOptions) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setError(null);

    try {
      // Call export API
      const response = await fetch(`/api/v1/drafts/${draftId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ format }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Export failed: ${response.statusText}`);
      }

      // Create blob from response
      const blob = await response.blob();

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('content-disposition');
      const filename =
        contentDisposition?.split('filename=')[1]?.replace(/"/g, '') || `draft.${format}`;

      // Trigger download
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Cleanup
      URL.revokeObjectURL(url);

      onSuccess?.();
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      setError(errorMessage);
      onError?.(errorMessage);
      return false;
    } finally {
      setIsExporting(false);
    }
  };

  return { handleExport, isExporting, error };
}
