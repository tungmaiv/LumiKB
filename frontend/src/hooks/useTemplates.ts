/**
 * useTemplates hook - Fetch all generation templates
 *
 * Story 4.9: Generation Templates
 * Fetches template list from /api/v1/generate/templates endpoint
 */

import { useQuery } from '@tanstack/react-query';

export interface Template {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  sections: string[];
  example_output: string | null;
}

interface TemplateListResponse {
  templates: Template[];
}

async function fetchTemplates(): Promise<Template[]> {
  const response = await fetch('/api/v1/generate/templates', {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }

  const data: TemplateListResponse = await response.json();
  return data.templates;
}

export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: fetchTemplates,
    staleTime: Infinity, // Templates don't change
  });
}

async function fetchTemplate(templateId: string): Promise<Template> {
  const response = await fetch(`/api/v1/generate/templates/${templateId}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch template: ${templateId}`);
  }

  return response.json();
}

export function useTemplate(templateId: string) {
  return useQuery({
    queryKey: ['templates', templateId],
    queryFn: () => fetchTemplate(templateId),
    enabled: !!templateId, // Only run when templateId provided
    staleTime: Infinity,
  });
}
