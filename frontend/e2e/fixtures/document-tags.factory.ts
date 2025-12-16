/**
 * Story 5-22 Test Fixtures: Document Tags
 * Generated: 2025-12-06
 *
 * Mock data factories for document tags E2E tests.
 * Follows network-first testing pattern with route interception.
 */

// ============================================================
// Mock Document with Tags
// ============================================================

export interface MockDocumentTag {
  id: string;
  name: string;
  content_type: string;
  status: 'processed' | 'processing' | 'failed' | 'pending';
  created_at: string;
  metadata: {
    tags: string[];
    file_size?: number;
    page_count?: number;
  };
}

export interface MockDocumentTagsResponse {
  documents: MockDocumentTag[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// ============================================================
// Factory Functions
// ============================================================

/**
 * Create a single document with tags
 */
export function createMockDocumentWithTags(
  overrides: Partial<MockDocumentTag> = {}
): MockDocumentTag {
  const id = overrides.id || `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  return {
    id,
    name: overrides.name || `Document ${id.slice(-4)}.pdf`,
    content_type: overrides.content_type || 'application/pdf',
    status: overrides.status || 'processed',
    created_at: overrides.created_at || new Date().toISOString(),
    metadata: {
      tags: overrides.metadata?.tags || [],
      file_size: overrides.metadata?.file_size || 1024 * 1024,
      page_count: overrides.metadata?.page_count || 10,
    },
  };
}

/**
 * Create multiple documents with various tag configurations
 */
export function createMockDocumentsWithTags(count: number = 10): MockDocumentTag[] {
  const tagSets = [
    ['policy', 'hr', 'onboarding'],
    ['technical', 'api', 'documentation'],
    ['legal', 'compliance', 'gdpr'],
    ['marketing', 'sales'],
    ['finance', 'quarterly'],
    [], // No tags
    ['archived'],
    ['important', 'urgent', 'review'],
    ['draft'],
    ['approved', 'published'],
  ];

  const fileTypes = [
    { ext: 'pdf', contentType: 'application/pdf' },
    { ext: 'docx', contentType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
    { ext: 'txt', contentType: 'text/plain' },
    { ext: 'md', contentType: 'text/markdown' },
  ];

  return Array.from({ length: count }, (_, i) => {
    const fileType = fileTypes[i % fileTypes.length];
    const tags = tagSets[i % tagSets.length];

    return createMockDocumentWithTags({
      id: `doc-${i + 1}`,
      name: `Document ${i + 1}.${fileType.ext}`,
      content_type: fileType.contentType,
      status: i % 5 === 0 ? 'processing' : 'processed',
      created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
      metadata: {
        tags,
        file_size: 1024 * 1024 * (i + 1),
        page_count: (i + 1) * 5,
      },
    });
  });
}

/**
 * Create a document with maximum tags (10 tags, 50 chars each)
 */
export function createMockDocumentWithMaxTags(): MockDocumentTag {
  const maxTags = Array.from({ length: 10 }, (_, i) => `tag-${i + 1}-${'a'.repeat(40)}`);

  return createMockDocumentWithTags({
    id: 'doc-max-tags',
    name: 'Document with Max Tags.pdf',
    metadata: {
      tags: maxTags,
    },
  });
}

/**
 * Create paginated response for documents with tags
 */
export function createMockPaginatedDocuments(
  page: number = 1,
  pageSize: number = 50,
  total: number = 100
): MockDocumentTagsResponse {
  const documents = createMockDocumentsWithTags(Math.min(pageSize, total - (page - 1) * pageSize));

  return {
    documents,
    total,
    page,
    page_size: pageSize,
    has_more: page * pageSize < total,
  };
}

// ============================================================
// Available Tags for KB
// ============================================================

/**
 * Get all unique tags available in a KB
 */
export function getAvailableTags(): string[] {
  return [
    'policy',
    'hr',
    'onboarding',
    'technical',
    'api',
    'documentation',
    'legal',
    'compliance',
    'gdpr',
    'marketing',
    'sales',
    'finance',
    'quarterly',
    'archived',
    'important',
    'urgent',
    'review',
    'draft',
    'approved',
    'published',
  ];
}

// ============================================================
// Tag Update Mock Responses
// ============================================================

export interface TagUpdateRequest {
  tags: string[];
}

export interface TagUpdateResponse {
  id: string;
  name: string;
  metadata: {
    tags: string[];
  };
  updated_at: string;
}

/**
 * Create mock response for tag update
 */
export function createTagUpdateResponse(
  documentId: string,
  documentName: string,
  newTags: string[]
): TagUpdateResponse {
  return {
    id: documentId,
    name: documentName,
    metadata: {
      tags: newTags,
    },
    updated_at: new Date().toISOString(),
  };
}

// ============================================================
// Error Responses
// ============================================================

export function createTagValidationError(message: string) {
  return {
    detail: message,
    errors: [
      {
        loc: ['body', 'tags'],
        msg: message,
        type: 'value_error',
      },
    ],
  };
}

export const TAG_ERRORS = {
  TOO_MANY_TAGS: createTagValidationError('Maximum 10 tags allowed per document'),
  TAG_TOO_LONG: createTagValidationError('Tag must be 50 characters or less'),
  DUPLICATE_TAG: createTagValidationError('Duplicate tags are not allowed'),
  EMPTY_TAG: createTagValidationError('Empty tags are not allowed'),
  PERMISSION_DENIED: {
    detail: 'Insufficient permissions to modify document tags',
  },
};
