/**
 * Hook Tests: useExport
 *
 * Story: 4-7 Document Export
 * Coverage: Export flow, loading states, error handling, download handling
 *
 * Test Count: 5 tests
 * Priority: P1 (3), P2 (2)
 *
 * Test Framework: Vitest
 */

import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useExport } from '../useExport';

// Mock fetch globally
global.fetch = vi.fn();

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document.createElement and appendChild/removeChild
const mockLink = {
  href: '',
  download: '',
  click: vi.fn(),
};
global.document.createElement = vi.fn((tagName) => {
  if (tagName === 'a') {
    return mockLink as unknown as HTMLAnchorElement;
  }
  return {} as HTMLElement;
});
global.document.body.appendChild = vi.fn();
global.document.body.removeChild = vi.fn();

describe('useExport Hook', () => {
  const mockDraftId = 'test-draft-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('[P1] should successfully export DOCX and trigger download', async () => {
    // GIVEN: API returns successful DOCX response
    const mockBlob = new Blob(['mock docx content'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: {
        get: (name: string) => {
          if (name === 'content-type')
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          if (name === 'content-disposition')
            return 'attachment; filename="Test_Draft.docx"';
          return null;
        },
      },
    });

    // WHEN: Hook is rendered and export is called
    const { result } = renderHook(() => useExport(mockDraftId));

    const exportPromise = result.current.handleExport('docx');

    // THEN: Loading state is true during export
    expect(result.current.isExporting).toBe(true);

    // WHEN: Export completes
    const success = await exportPromise;

    // THEN: Export succeeds
    await waitFor(() => {
      expect(success).toBe(true);
    });

    // THEN: Loading state returns to false
    expect(result.current.isExporting).toBe(false);

    // THEN: No error
    expect(result.current.error).toBeNull();

    // THEN: Fetch was called with correct parameters
    expect(global.fetch).toHaveBeenCalledWith(`/api/v1/drafts/${mockDraftId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ format: 'docx' }),
    });

    // THEN: Blob URL was created
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));

    // THEN: Download was triggered
    expect(mockLink.click).toHaveBeenCalledTimes(1);
    expect(mockLink.download).toBe('Test_Draft.docx');

    // THEN: Blob URL was cleaned up
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('[P1] should handle PDF export with correct MIME type', async () => {
    // GIVEN: API returns successful PDF response
    const mockBlob = new Blob(['mock pdf content'], { type: 'application/pdf' });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: {
        get: (name: string) => {
          if (name === 'content-type') return 'application/pdf';
          if (name === 'content-disposition') return 'attachment; filename="Report.pdf"';
          return null;
        },
      },
    });

    // WHEN: Export PDF
    const { result } = renderHook(() => useExport(mockDraftId));
    const success = await result.current.handleExport('pdf');

    // THEN: Export succeeds
    expect(success).toBe(true);

    // THEN: Correct filename
    expect(mockLink.download).toBe('Report.pdf');
  });

  it('[P1] should handle Markdown export', async () => {
    // GIVEN: API returns successful Markdown response
    const mockBlob = new Blob(['# Markdown Content'], { type: 'text/markdown' });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: {
        get: (name: string) => {
          if (name === 'content-type') return 'text/markdown';
          if (name === 'content-disposition') return 'attachment; filename="draft.md"';
          return null;
        },
      },
    });

    // WHEN: Export Markdown
    const { result } = renderHook(() => useExport(mockDraftId));
    const success = await result.current.handleExport('markdown');

    // THEN: Export succeeds
    expect(success).toBe(true);

    // THEN: Correct filename
    expect(mockLink.download).toBe('draft.md');
  });

  it('[P2] should handle API error and set error state', async () => {
    // GIVEN: API returns error response
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
    });

    // WHEN: Export is called
    const { result } = renderHook(() => useExport(mockDraftId));
    const success = await result.current.handleExport('docx');

    // THEN: Export fails
    await waitFor(() => {
      expect(success).toBe(false);
    });

    // THEN: Error state is set
    expect(result.current.error).toBeTruthy();
    expect(result.current.error).toContain('Export failed');

    // THEN: Loading state is false
    expect(result.current.isExporting).toBe(false);

    // THEN: No download was triggered
    expect(mockLink.click).not.toHaveBeenCalled();
  });

  it('[P2] should handle network error gracefully', async () => {
    // GIVEN: Network error occurs
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network error')
    );

    // WHEN: Export is called
    const { result } = renderHook(() => useExport(mockDraftId));
    const success = await result.current.handleExport('pdf');

    // THEN: Export fails
    await waitFor(() => {
      expect(success).toBe(false);
    });

    // THEN: Error state is set
    expect(result.current.error).toBe('Network error');

    // THEN: Loading state is false
    expect(result.current.isExporting).toBe(false);
  });

  it('[P2] should fallback to default filename if Content-Disposition missing', async () => {
    // GIVEN: API response without Content-Disposition header
    const mockBlob = new Blob(['content'], { type: 'application/pdf' });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: {
        get: (name: string) => {
          if (name === 'content-type') return 'application/pdf';
          return null; // No Content-Disposition
        },
      },
    });

    // WHEN: Export is called
    const { result } = renderHook(() => useExport(mockDraftId));
    const success = await result.current.handleExport('pdf');

    // THEN: Export succeeds with fallback filename
    expect(success).toBe(true);
    expect(mockLink.download).toBe('draft.pdf'); // Fallback filename
  });
});
