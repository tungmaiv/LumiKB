/**
 * Unit tests for useTemplates hook
 *
 * Story 4.9: Generation Templates
 * Tests template fetching and caching behavior
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, test, vi, beforeEach, afterEach } from 'vitest';
import { useTemplates, useTemplate, type Template } from '../useTemplates';
import React from 'react';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Helper to create query client wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useTemplates', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('[P1] fetches templates successfully', async () => {
    // GIVEN: API returns templates successfully
    const mockTemplates: Template[] = [
      {
        id: 'rfp_response',
        name: 'RFP Response Section',
        description: 'Generate a structured RFP response',
        system_prompt: 'You are an expert proposal writer...',
        sections: ['Executive Summary', 'Technical Approach'],
        example_output: '## Executive Summary...',
      },
      {
        id: 'checklist',
        name: 'Technical Checklist',
        description: 'Create a requirement checklist',
        system_prompt: 'Generate a checklist...',
        sections: ['Requirements List'],
        example_output: '- [ ] OAuth 2.0...',
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ templates: mockTemplates }),
    });

    // WHEN: Hook is rendered
    const { result } = renderHook(() => useTemplates(), {
      wrapper: createWrapper(),
    });

    // THEN: Hook starts in loading state
    expect(result.current.isLoading).toBe(true);

    // WHEN: Waiting for fetch to complete
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // THEN: Templates data is returned
    expect(result.current.data).toEqual(mockTemplates);
    expect(result.current.data?.length).toBe(2);
    expect(result.current.isError).toBe(false);

    // AND: Fetch was called with correct URL and credentials
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/generate/templates', {
      credentials: 'include',
    });
  });

  test('[P1] handles fetch error gracefully', async () => {
    // GIVEN: API returns error
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    // WHEN: Hook is rendered
    const { result } = renderHook(() => useTemplates(), {
      wrapper: createWrapper(),
    });

    // WHEN: Waiting for fetch to complete
    await waitFor(() => expect(result.current.isError).toBe(true));

    // THEN: Error state is set
    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toBe('Failed to fetch templates');
    expect(result.current.data).toBeUndefined();
  });

  test('[P2] uses infinite staleTime for caching', async () => {
    // GIVEN: API returns templates
    const mockTemplates: Template[] = [
      {
        id: 'rfp_response',
        name: 'RFP Response Section',
        description: 'Test',
        system_prompt: 'Test prompt',
        sections: [],
        example_output: null,
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ templates: mockTemplates }),
    });

    // WHEN: Hook is rendered
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result, rerender } = renderHook(() => useTemplates(), { wrapper });

    // WHEN: Waiting for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // THEN: Fetch called once
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // WHEN: Hook is re-rendered (simulating component re-render)
    rerender();

    // THEN: Fetch is NOT called again (data is cached with staleTime: Infinity)
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockTemplates);
  });

  test('[P1] returns all 4 templates in production data', async () => {
    // GIVEN: Real template data structure
    const mockTemplates: Template[] = [
      {
        id: 'rfp_response',
        name: 'RFP Response Section',
        description: 'Generate a structured RFP response',
        system_prompt: 'You are an expert...',
        sections: ['Executive Summary', 'Technical Approach', 'Relevant Experience', 'Pricing'],
        example_output: '## Executive Summary...',
      },
      {
        id: 'checklist',
        name: 'Technical Checklist',
        description: 'Create a requirement checklist',
        system_prompt: 'Generate a checklist...',
        sections: ['Requirements List'],
        example_output: '- [ ] OAuth...',
      },
      {
        id: 'gap_analysis',
        name: 'Gap Analysis',
        description: 'Compare requirements',
        system_prompt: 'Generate gap analysis...',
        sections: ['Gap Analysis Table'],
        example_output: '| Requirement | Current State |...',
      },
      {
        id: 'custom',
        name: 'Custom Prompt',
        description: 'Generate based on your instructions',
        system_prompt: "Follow user's custom instructions...",
        sections: [],
        example_output: null,
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ templates: mockTemplates }),
    });

    // WHEN: Hook fetches templates
    const { result } = renderHook(() => useTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // THEN: All 4 templates are returned
    expect(result.current.data?.length).toBe(4);
    const templateIds = result.current.data?.map((t) => t.id);
    expect(templateIds).toContain('rfp_response');
    expect(templateIds).toContain('checklist');
    expect(templateIds).toContain('gap_analysis');
    expect(templateIds).toContain('custom');
  });
});

describe('useTemplate', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('[P1] fetches single template by ID successfully', async () => {
    // GIVEN: API returns specific template
    const mockTemplate: Template = {
      id: 'rfp_response',
      name: 'RFP Response Section',
      description: 'Generate a structured RFP response',
      system_prompt: 'You are an expert proposal writer...',
      sections: ['Executive Summary', 'Technical Approach'],
      example_output: '## Executive Summary...',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTemplate,
    });

    // WHEN: Hook is rendered with template ID
    const { result } = renderHook(() => useTemplate('rfp_response'), {
      wrapper: createWrapper(),
    });

    // WHEN: Waiting for fetch to complete
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // THEN: Template data is returned
    expect(result.current.data).toEqual(mockTemplate);
    expect(result.current.data?.id).toBe('rfp_response');

    // AND: Fetch was called with correct URL
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/generate/templates/rfp_response', {
      credentials: 'include',
    });
  });

  test('[P1] handles 404 error for invalid template ID', async () => {
    // GIVEN: API returns 404
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    // WHEN: Hook is rendered with invalid ID
    const { result } = renderHook(() => useTemplate('invalid_id'), {
      wrapper: createWrapper(),
    });

    // WHEN: Waiting for fetch to complete
    await waitFor(() => expect(result.current.isError).toBe(true));

    // THEN: Error state is set
    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toBe('Failed to fetch template: invalid_id');
  });

  test('[P2] query is disabled when templateId is empty', () => {
    // GIVEN: Hook is rendered without template ID
    const { result } = renderHook(() => useTemplate(''), {
      wrapper: createWrapper(),
    });

    // THEN: Query is not executed
    expect(mockFetch).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  test('[P2] uses infinite staleTime for caching', async () => {
    // GIVEN: API returns template
    const mockTemplate: Template = {
      id: 'checklist',
      name: 'Technical Checklist',
      description: 'Test',
      system_prompt: 'Test prompt',
      sections: [],
      example_output: null,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTemplate,
    });

    // WHEN: Hook is rendered
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result, rerender } = renderHook(() => useTemplate('checklist'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // THEN: Fetch called once
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // WHEN: Re-rendering hook
    rerender();

    // THEN: Fetch NOT called again (cached)
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockTemplate);
  });
});
