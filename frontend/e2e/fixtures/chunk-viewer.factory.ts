/**
 * Factory for Document Chunk Viewer test data (Stories 5.25, 5.26)
 * Provides mock data for chunk lists, content streaming, and highlighting scenarios
 */

// ============================================================
// Types
// ============================================================

export interface ChunkMetadata {
  chunk_index: number;
  char_start: number;
  char_end: number;
  page_number: number | null;
  paragraph_index: number | null;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  content: string;
  metadata: ChunkMetadata;
  embedding_id: string;
  created_at: string;
}

export interface ChunkListResponse {
  chunks: DocumentChunk[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface DocumentContent {
  document_id: string;
  content_type: 'pdf' | 'html' | 'text' | 'markdown';
  content_url: string;
  file_size: number;
  file_name: string;
}

// ============================================================
// Mock Chunk Data
// ============================================================

/**
 * Create a single mock chunk
 */
export function createMockChunk(overrides: Partial<DocumentChunk> = {}): DocumentChunk {
  const chunkIndex = overrides.metadata?.chunk_index ?? 0;
  return {
    id: `chunk-${crypto.randomUUID()}`,
    document_id: `doc-${crypto.randomUUID()}`,
    content: `This is chunk ${chunkIndex} content. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.`,
    embedding_id: `emb-${crypto.randomUUID()}`,
    created_at: new Date().toISOString(),
    ...overrides,
    metadata: {
      chunk_index: chunkIndex,
      char_start: chunkIndex * 500,
      char_end: (chunkIndex + 1) * 500 - 1,
      page_number: Math.floor(chunkIndex / 3) + 1,
      paragraph_index: chunkIndex % 5,
      ...overrides.metadata,
    },
  };
}

/**
 * Create multiple mock chunks for a document
 */
export function createMockChunks(
  documentId: string,
  count: number = 10,
  options: { startIndex?: number; pageSize?: number } = {}
): DocumentChunk[] {
  const { startIndex = 0, pageSize = 500 } = options;
  const chunks: DocumentChunk[] = [];

  for (let i = 0; i < count; i++) {
    const chunkIndex = startIndex + i;
    chunks.push(
      createMockChunk({
        document_id: documentId,
        metadata: {
          chunk_index: chunkIndex,
          char_start: chunkIndex * pageSize,
          char_end: (chunkIndex + 1) * pageSize - 1,
          page_number: Math.floor(chunkIndex / 3) + 1,
          paragraph_index: chunkIndex % 5,
        },
      })
    );
  }

  return chunks;
}

/**
 * Create a paginated chunk list response
 */
export function createMockChunkListResponse(
  documentId: string,
  options: {
    total?: number;
    page?: number;
    pageSize?: number;
  } = {}
): ChunkListResponse {
  const { total = 50, page = 1, pageSize = 10 } = options;
  const startIndex = (page - 1) * pageSize;
  const chunksOnPage = Math.min(pageSize, total - startIndex);

  return {
    chunks: createMockChunks(documentId, chunksOnPage, { startIndex }),
    total,
    page,
    page_size: pageSize,
    has_next: startIndex + chunksOnPage < total,
    has_previous: page > 1,
  };
}

// ============================================================
// Document Content Data
// ============================================================

/**
 * Create mock document content metadata
 */
export function createMockDocumentContent(
  overrides: Partial<DocumentContent> = {}
): DocumentContent {
  return {
    document_id: `doc-${crypto.randomUUID()}`,
    content_type: 'pdf',
    content_url: '/api/v1/documents/mock-doc/content',
    file_size: 1024 * 1024, // 1MB
    file_name: 'test-document.pdf',
    ...overrides,
  };
}

/**
 * Create mock PDF document
 */
export function createMockPdfDocument(documentId: string): DocumentContent {
  return createMockDocumentContent({
    document_id: documentId,
    content_type: 'pdf',
    content_url: `/api/v1/documents/${documentId}/content`,
    file_name: 'technical-manual.pdf',
    file_size: 2 * 1024 * 1024,
  });
}

/**
 * Create mock HTML document
 */
export function createMockHtmlDocument(documentId: string): DocumentContent {
  return createMockDocumentContent({
    document_id: documentId,
    content_type: 'html',
    content_url: `/api/v1/documents/${documentId}/content`,
    file_name: 'web-article.html',
    file_size: 50 * 1024,
  });
}

/**
 * Create mock text document
 */
export function createMockTextDocument(documentId: string): DocumentContent {
  return createMockDocumentContent({
    document_id: documentId,
    content_type: 'text',
    content_url: `/api/v1/documents/${documentId}/content`,
    file_name: 'notes.txt',
    file_size: 10 * 1024,
  });
}

// ============================================================
// Search Result Scenarios
// ============================================================

/**
 * Create chunks with search matches highlighted
 */
export function createMockSearchResults(
  documentId: string,
  query: string,
  matchCount: number = 5
): DocumentChunk[] {
  const chunks: DocumentChunk[] = [];

  for (let i = 0; i < matchCount; i++) {
    chunks.push(
      createMockChunk({
        document_id: documentId,
        content: `This chunk contains the search term "${query}" which the user is looking for. Additional context around the match.`,
        metadata: {
          chunk_index: i * 3, // Sparse distribution
          char_start: i * 1500,
          char_end: i * 1500 + 499,
          page_number: i + 1,
          paragraph_index: i % 3,
        },
      })
    );
  }

  return chunks;
}

// ============================================================
// Edge Case Scenarios
// ============================================================

/**
 * Create empty chunk list response
 */
export function createEmptyChunkResponse(documentId: string): ChunkListResponse {
  return {
    chunks: [],
    total: 0,
    page: 1,
    page_size: 10,
    has_next: false,
    has_previous: false,
  };
}

/**
 * Create single chunk document
 */
export function createSingleChunkDocument(documentId: string): ChunkListResponse {
  return {
    chunks: [
      createMockChunk({
        document_id: documentId,
        content: 'This is the only chunk in a very short document.',
        metadata: {
          chunk_index: 0,
          char_start: 0,
          char_end: 49,
          page_number: 1,
          paragraph_index: 0,
        },
      }),
    ],
    total: 1,
    page: 1,
    page_size: 10,
    has_next: false,
    has_previous: false,
  };
}

/**
 * Create large document with many chunks
 */
export function createLargeDocumentChunks(documentId: string): ChunkListResponse {
  return createMockChunkListResponse(documentId, {
    total: 500,
    page: 1,
    pageSize: 20,
  });
}

/**
 * Create chunk with very long content
 */
export function createLongContentChunk(documentId: string): DocumentChunk {
  const longContent = 'A'.repeat(5000) + ' This is a very long chunk content. ' + 'B'.repeat(5000);
  return createMockChunk({
    document_id: documentId,
    content: longContent,
    metadata: {
      chunk_index: 0,
      char_start: 0,
      char_end: longContent.length - 1,
      page_number: 1,
      paragraph_index: 0,
    },
  });
}

// ============================================================
// Error Responses
// ============================================================

/**
 * Create error response for chunk fetch failure
 */
export function createChunkFetchError(): { error: string; status: number } {
  return {
    error: 'Failed to fetch document chunks',
    status: 500,
  };
}

/**
 * Create error response for document not found
 */
export function createDocumentNotFoundError(): { error: string; status: number } {
  return {
    error: 'Document not found',
    status: 404,
  };
}

/**
 * Create error response for content unavailable
 */
export function createContentUnavailableError(): { error: string; status: number } {
  return {
    error: 'Document content is not available',
    status: 410,
  };
}

/**
 * Create error response for unauthorized access
 */
export function createUnauthorizedError(): { error: string; status: number } {
  return {
    error: 'You do not have permission to view this document',
    status: 403,
  };
}

// ============================================================
// API Route Handlers (for MSW or similar)
// ============================================================

/**
 * Get standard API routes for mocking
 */
export function getChunkViewerApiRoutes(documentId: string) {
  return {
    getChunks: `/api/v1/knowledge-bases/*/documents/${documentId}/chunks`,
    getContent: `/api/v1/knowledge-bases/*/documents/${documentId}/content`,
    searchChunks: `/api/v1/knowledge-bases/*/documents/${documentId}/chunks/search`,
    getChunkById: `/api/v1/knowledge-bases/*/documents/${documentId}/chunks/*`,
  };
}
