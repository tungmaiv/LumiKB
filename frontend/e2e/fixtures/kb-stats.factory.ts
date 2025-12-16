/**
 * KB Statistics Factory
 * Story 5-6 Automation: Reusable mock data for KB statistics tests
 *
 * Provides factory functions to generate consistent mock KB statistics
 * data for E2E and component tests.
 */

export interface TopDocument {
  id: string;
  filename: string;
  access_count: number;
}

export interface KBStatsData {
  kb_id: string;
  kb_name: string;
  document_count: number;
  storage_bytes: number;
  total_chunks: number;
  total_embeddings: number;
  searches_30d: number;
  generations_30d: number;
  unique_users_30d: number;
  top_documents: TopDocument[];
  last_updated: string;
}

/**
 * Create default KB stats with realistic data
 */
export function createKBStats(overrides?: Partial<KBStatsData>): KBStatsData {
  const defaults: KBStatsData = {
    kb_id: '550e8400-e29b-41d4-a716-446655440000',
    kb_name: 'Engineering Documentation',
    document_count: 42,
    storage_bytes: 104857600, // 100MB
    total_chunks: 1250,
    total_embeddings: 1250,
    searches_30d: 285,
    generations_30d: 98,
    unique_users_30d: 12,
    top_documents: [
      {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'architecture-guide.pdf',
        access_count: 50,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174001',
        filename: 'api-reference.md',
        access_count: 45,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174002',
        filename: 'deployment-runbook.docx',
        access_count: 38,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174003',
        filename: 'troubleshooting-guide.md',
        access_count: 32,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174004',
        filename: 'onboarding-checklist.pdf',
        access_count: 28,
      },
    ],
    last_updated: new Date().toISOString(),
  };

  return deepMerge(defaults, overrides || {});
}

/**
 * Create empty KB stats (for newly created KB with no documents)
 */
export function createEmptyKBStats(kbId?: string, kbName?: string): KBStatsData {
  return {
    kb_id: kbId || '550e8400-e29b-41d4-a716-446655440001',
    kb_name: kbName || 'Empty Knowledge Base',
    document_count: 0,
    storage_bytes: 0,
    total_chunks: 0,
    total_embeddings: 0,
    searches_30d: 0,
    generations_30d: 0,
    unique_users_30d: 0,
    top_documents: [],
    last_updated: new Date().toISOString(),
  };
}

/**
 * Create large KB stats (for performance/load testing)
 */
export function createLargeKBStats(): KBStatsData {
  return createKBStats({
    kb_name: 'Enterprise Knowledge Base',
    document_count: 5000,
    storage_bytes: 53687091200, // 50GB
    total_chunks: 125000,
    total_embeddings: 125000,
    searches_30d: 15000,
    generations_30d: 5000,
    unique_users_30d: 250,
    top_documents: [
      {
        id: '123e4567-e89b-12d3-a456-426614174010',
        filename: 'product-specifications.pdf',
        access_count: 1250,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174011',
        filename: 'customer-support-handbook.docx',
        access_count: 1100,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174012',
        filename: 'engineering-standards.md',
        access_count: 980,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174013',
        filename: 'compliance-policies.pdf',
        access_count: 875,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174014',
        filename: 'quarterly-roadmap.pptx',
        access_count: 720,
      },
    ],
  });
}

/**
 * Create KB stats with high activity (for testing activity metrics)
 */
export function createHighActivityKBStats(): KBStatsData {
  return createKBStats({
    kb_name: 'Active Project KB',
    document_count: 150,
    storage_bytes: 314572800, // 300MB
    total_chunks: 5000,
    total_embeddings: 5000,
    searches_30d: 5000,
    generations_30d: 2500,
    unique_users_30d: 45,
  });
}

/**
 * Create KB stats with low activity (for testing inactive KB scenarios)
 */
export function createLowActivityKBStats(): KBStatsData {
  return createKBStats({
    kb_name: 'Archived Project KB',
    document_count: 20,
    storage_bytes: 20971520, // 20MB
    total_chunks: 500,
    total_embeddings: 500,
    searches_30d: 5,
    generations_30d: 1,
    unique_users_30d: 2,
    top_documents: [
      {
        id: '123e4567-e89b-12d3-a456-426614174020',
        filename: 'legacy-system-docs.pdf',
        access_count: 3,
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174021',
        filename: 'deprecated-api.md',
        access_count: 2,
      },
    ],
  });
}

/**
 * Create KB stats with various storage sizes (for storage visualization testing)
 */
export function createKBStatsWithStorageSize(storageBytes: number, kbName?: string): KBStatsData {
  return createKBStats({
    kb_name: kbName || `KB with ${formatBytes(storageBytes)} storage`,
    storage_bytes: storageBytes,
  });
}

/**
 * Create multiple KB stats for dropdown/selection testing
 */
export function createMultipleKBStats(count: number): KBStatsData[] {
  return Array.from({ length: count }, (_, i) => ({
    kb_id: `550e8400-e29b-41d4-a716-44665544000${i}`,
    kb_name: `Knowledge Base ${i + 1}`,
    document_count: 10 + i * 5,
    storage_bytes: 10485760 * (i + 1), // 10MB increments
    total_chunks: 100 + i * 50,
    total_embeddings: 100 + i * 50,
    searches_30d: 50 + i * 10,
    generations_30d: 20 + i * 5,
    unique_users_30d: 5 + i,
    top_documents: [
      {
        id: `doc-${i}-1`,
        filename: `document-${i}-1.pdf`,
        access_count: 10 + i,
      },
    ],
    last_updated: new Date().toISOString(),
  }));
}

/**
 * Format bytes to human-readable string
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Deep merge helper for partial overrides
 */
function deepMerge(target: KBStatsData, source: Partial<KBStatsData>): KBStatsData {
  const result = { ...target };

  for (const key in source) {
    const sourceValue = source[key as keyof KBStatsData];
    const targetValue = result[key as keyof KBStatsData];

    if (
      sourceValue &&
      typeof sourceValue === 'object' &&
      !Array.isArray(sourceValue) &&
      targetValue &&
      typeof targetValue === 'object' &&
      !Array.isArray(targetValue)
    ) {
      (result[key as keyof KBStatsData] as unknown as Record<string, unknown>) = {
        ...(targetValue as Record<string, unknown>),
        ...(sourceValue as Record<string, unknown>),
      };
    } else if (sourceValue !== undefined) {
      (result[key as keyof KBStatsData] as typeof sourceValue) = sourceValue;
    }
  }

  return result;
}
