/**
 * Unit tests for useGenerationStream hook (Story 4.5)
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useGenerationStream } from '../useGenerationStream';

// Mock fetch
global.fetch = vi.fn();

describe('useGenerationStream', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useGenerationStream());

    expect(result.current.status).toBeNull();
    expect(result.current.content).toBe('');
    expect(result.current.citations).toEqual([]);
    expect(result.current.confidence).toBeNull();
    expect(result.current.generationId).toBeNull();
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should start generation and set isGenerating to true', async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"type":"status","content":"Preparing..."}\n\n')
        );
        controller.close();
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'rfp_response',
        additionalPrompt: 'Focus on security',
        selectedChunkIds: ['chunk-1', 'chunk-2'],
      });
    });

    await waitFor(() => {
      expect(result.current.status).toBe('Preparing...');
    });
  });

  it('should accumulate token events into content', async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"type":"token","content":"OAuth "}\n\n')
        );
        controller.enqueue(
          new TextEncoder().encode('data: {"type":"token","content":"2.0 "}\n\n')
        );
        controller.enqueue(
          new TextEncoder().encode('data: {"type":"token","content":"implementation"}\n\n')
        );
        controller.close();
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'technical_checklist',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1'],
      });
    });

    await waitFor(() => {
      expect(result.current.content).toBe('OAuth 2.0 implementation');
    });
  });

  it('should collect citation events', async () => {
    const mockCitation = {
      number: 1,
      document_id: 'doc-123',
      document_name: 'Security_Arch.pdf',
      page_number: 14,
      section_header: 'Authentication',
      excerpt: 'OAuth 2.0 implementation...',
      char_start: 100,
      char_end: 200,
      confidence: 0.92,
    };

    const mockReadableStream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            `data: {"type":"citation","number":1,"data":${JSON.stringify(mockCitation)}}\n\n`
          )
        );
        controller.close();
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'rfp_response',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1'],
      });
    });

    await waitFor(() => {
      expect(result.current.citations).toHaveLength(1);
      expect(result.current.citations[0]).toEqual(mockCitation);
    });
  });

  it('should handle done event and set metadata', async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type":"done","generation_id":"gen-abc123","confidence":0.85,"sources_used":3}\n\n'
          )
        );
        controller.close();
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'custom',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1', 'chunk-2', 'chunk-3'],
      });
    });

    await waitFor(() => {
      expect(result.current.generationId).toBe('gen-abc123');
      expect(result.current.confidence).toBe(0.85);
      expect(result.current.sourcesUsed).toBe(3);
      expect(result.current.isGenerating).toBe(false);
      expect(result.current.status).toBe('Complete');
    });
  });

  it('should handle error events', async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"type":"error","message":"Insufficient sources"}\n\n')
        );
        controller.close();
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'rfp_response',
        additionalPrompt: '',
        selectedChunkIds: [],
      });
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Insufficient sources');
      expect(result.current.isGenerating).toBe(false);
    });
  });

  it('should handle cancellation via AbortController', async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        setTimeout(() => {
          controller.enqueue(
            new TextEncoder().encode('data: {"type":"token","content":"delayed"}\n\n')
          );
          controller.close();
        }, 100);
      },
    });

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useGenerationStream());

    act(() => {
      result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'rfp_response',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1'],
      });
    });

    // Cancel immediately
    act(() => {
      result.current.cancelGeneration();
    });

    await waitFor(() => {
      expect(result.current.isGenerating).toBe(false);
      expect(result.current.status).toBe('Cancelled');
    });
  });

  it('should reset state', () => {
    const { result } = renderHook(() => useGenerationStream());

    // Set some state
    act(() => {
      result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'custom',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1'],
      });
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.content).toBe('');
    expect(result.current.citations).toEqual([]);
    expect(result.current.status).toBeNull();
  });

  it('should handle fetch errors', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Permission denied' }),
    });

    const { result } = renderHook(() => useGenerationStream());

    await act(async () => {
      await result.current.startGeneration({
        kbId: 'kb-123',
        mode: 'rfp_response',
        additionalPrompt: '',
        selectedChunkIds: ['chunk-1'],
      });
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Permission denied');
      expect(result.current.isGenerating).toBe(false);
    });
  });
});
