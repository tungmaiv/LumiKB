/**
 * KB Settings TypeScript types - Story 7-14: KB Settings UI - General Panel
 *
 * Mirrors backend schemas from backend/app/schemas/kb_settings.py
 * for type-safe KB configuration management.
 */

// =============================================================================
// Enum Types (mirroring backend enums)
// =============================================================================

export enum ChunkingStrategy {
  FIXED = 'fixed',
  RECURSIVE = 'recursive',
  SEMANTIC = 'semantic',
}

export enum RetrievalMethod {
  VECTOR = 'vector',
  HYBRID = 'hybrid',
  HYDE = 'hyde',
}

export enum CitationStyle {
  INLINE = 'inline',
  FOOTNOTE = 'footnote',
  NONE = 'none',
}

export enum UncertaintyHandling {
  ACKNOWLEDGE = 'acknowledge',
  REFUSE = 'refuse',
  BEST_EFFORT = 'best_effort',
}

export enum TruncationStrategy {
  START = 'start',
  END = 'end',
  NONE = 'none',
}

export enum PoolingStrategy {
  MEAN = 'mean',
  CLS = 'cls',
  MAX = 'max',
  LAST = 'last',
}

/**
 * Document parser backend selection for all supported formats.
 * Story 7-32: Docling Document Parser Integration
 */
export enum DocumentParserBackend {
  UNSTRUCTURED = 'unstructured',
  DOCLING = 'docling',
  AUTO = 'auto',
}

// =============================================================================
// Sub-Config Interfaces (mirroring backend Pydantic models)
// =============================================================================

/**
 * Configuration for document chunking (AC-7.14.2)
 * Mirrors ChunkingConfig in backend
 */
export interface ChunkingConfig {
  strategy: ChunkingStrategy;
  chunk_size: number; // 100-2000, default 512
  chunk_overlap: number; // 0-500, default 50
  separators?: string[];
}

/**
 * Configuration for document retrieval (AC-7.14.3)
 * Mirrors RetrievalConfig in backend
 */
export interface RetrievalConfig {
  top_k: number; // 1-100, default 10
  similarity_threshold: number; // 0.0-1.0, default 0.7
  method: RetrievalMethod;
  mmr_enabled: boolean;
  mmr_lambda: number; // 0.0-1.0, default 0.5
  hybrid_alpha?: number; // 0.0-1.0, default 0.5
}

/**
 * Configuration for result reranking
 * Mirrors RerankingConfig in backend
 */
export interface RerankingConfig {
  enabled: boolean;
  model: string | null;
  top_n: number; // 1-50, default 10
}

/**
 * Configuration for text generation (AC-7.14.4)
 * Mirrors GenerationConfig in backend
 */
export interface GenerationConfig {
  temperature: number; // 0.0-2.0, default 0.7
  top_p: number; // 0.0-1.0, default 0.9
  top_k?: number; // 1-100, default 40
  max_tokens: number; // 100-16000, default 2048
  frequency_penalty?: number; // -2.0-2.0, default 0.0
  presence_penalty?: number; // -2.0-2.0, default 0.0
  stop_sequences?: string[];
}

/**
 * Configuration for Named Entity Recognition
 * Mirrors NERConfig in backend
 */
export interface NERConfig {
  enabled: boolean;
  confidence_threshold: number; // 0.0-1.0, default 0.8
  entity_types: string[];
  batch_size: number; // 1-100, default 32
}

/**
 * Configuration for document processing
 * Mirrors DocumentProcessingConfig in backend
 * Story 7-32: Added parser_backend field
 */
export interface DocumentProcessingConfig {
  ocr_enabled: boolean;
  language_detection: boolean;
  table_extraction: boolean;
  image_extraction: boolean;
  parser_backend: DocumentParserBackend;
}

/**
 * Configuration for KB-specific prompts
 * Mirrors KBPromptConfig in backend
 */
export interface KBPromptConfig {
  system_prompt: string; // max 4000 chars
  context_template: string;
  citation_style: CitationStyle;
  uncertainty_handling: UncertaintyHandling;
  response_language: string;
}

/**
 * Configuration for embedding generation
 * Mirrors EmbeddingConfig in backend
 */
export interface EmbeddingConfig {
  model_id: string | null;
  batch_size: number; // 1-100, default 32
  normalize: boolean;
  truncation: TruncationStrategy;
  max_length: number; // 128-16384, default 512
  prefix_document: string; // max 100 chars
  prefix_query: string; // max 100 chars
  pooling_strategy: PoolingStrategy;
}

// =============================================================================
// Composite KBSettings Type (AC-7.14.6, AC-7.14.8)
// =============================================================================

/**
 * Complete KB-level configuration stored in settings JSONB
 * Mirrors KBSettings in backend
 */
export interface KBSettings {
  chunking: ChunkingConfig;
  retrieval: RetrievalConfig;
  reranking: RerankingConfig;
  generation: GenerationConfig;
  ner: NERConfig;
  processing: DocumentProcessingConfig;
  prompts: KBPromptConfig;
  embedding: EmbeddingConfig;
  preset: string | null;
  /**
   * Enable debug mode for RAG pipeline telemetry (AC-9.15.1).
   * When enabled, chat responses include detailed information about
   * retrieved chunks, similarity scores, KB parameters, and timing metrics.
   */
  debug_mode: boolean;
}

// =============================================================================
// Default Values (matching backend defaults)
// =============================================================================

export const DEFAULT_CHUNKING_CONFIG: ChunkingConfig = {
  strategy: ChunkingStrategy.RECURSIVE,
  chunk_size: 512,
  chunk_overlap: 50,
  separators: ['\n\n', '\n', ' ', ''],
};

export const DEFAULT_RETRIEVAL_CONFIG: RetrievalConfig = {
  top_k: 10,
  similarity_threshold: 0.7,
  method: RetrievalMethod.VECTOR,
  mmr_enabled: false,
  mmr_lambda: 0.5,
  hybrid_alpha: 0.5,
};

export const DEFAULT_RERANKING_CONFIG: RerankingConfig = {
  enabled: false,
  model: null,
  top_n: 10,
};

export const DEFAULT_GENERATION_CONFIG: GenerationConfig = {
  temperature: 0.7,
  top_p: 0.9,
  top_k: 40,
  max_tokens: 2048,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
  stop_sequences: [],
};

export const DEFAULT_NER_CONFIG: NERConfig = {
  enabled: false,
  confidence_threshold: 0.8,
  entity_types: [],
  batch_size: 32,
};

export const DEFAULT_PROCESSING_CONFIG: DocumentProcessingConfig = {
  ocr_enabled: false,
  language_detection: true,
  table_extraction: true,
  image_extraction: false,
  parser_backend: DocumentParserBackend.UNSTRUCTURED,
};

export const DEFAULT_PROMPT_CONFIG: KBPromptConfig = {
  system_prompt: '',
  context_template: '',
  citation_style: CitationStyle.INLINE,
  uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
  response_language: 'en',
};

export const DEFAULT_EMBEDDING_CONFIG: EmbeddingConfig = {
  model_id: null,
  batch_size: 32,
  normalize: true,
  truncation: TruncationStrategy.END,
  max_length: 512,
  prefix_document: '',
  prefix_query: '',
  pooling_strategy: PoolingStrategy.MEAN,
};

export const DEFAULT_KB_SETTINGS: KBSettings = {
  chunking: DEFAULT_CHUNKING_CONFIG,
  retrieval: DEFAULT_RETRIEVAL_CONFIG,
  reranking: DEFAULT_RERANKING_CONFIG,
  generation: DEFAULT_GENERATION_CONFIG,
  ner: DEFAULT_NER_CONFIG,
  processing: DEFAULT_PROCESSING_CONFIG,
  prompts: DEFAULT_PROMPT_CONFIG,
  embedding: DEFAULT_EMBEDDING_CONFIG,
  preset: null,
  debug_mode: false,
};

// =============================================================================
// API Types for Settings Endpoints (AC-7.14.8)
// =============================================================================

/**
 * Response from GET /api/v1/knowledge-bases/{id}/settings
 */
export type KBSettingsResponse = KBSettings;

/**
 * Request body for PUT /api/v1/knowledge-bases/{id}/settings
 * All fields are optional for partial updates
 */
export interface KBSettingsUpdate {
  chunking?: Partial<ChunkingConfig>;
  retrieval?: Partial<RetrievalConfig>;
  reranking?: Partial<RerankingConfig>;
  generation?: Partial<GenerationConfig>;
  ner?: Partial<NERConfig>;
  processing?: Partial<DocumentProcessingConfig>;
  prompts?: Partial<KBPromptConfig>;
  embedding?: Partial<EmbeddingConfig>;
  preset?: string | null;
  debug_mode?: boolean;
}

// =============================================================================
// Validation Constraints (for form validation)
// =============================================================================

export const KB_SETTINGS_CONSTRAINTS = {
  chunking: {
    chunk_size: { min: 100, max: 2000 },
    chunk_overlap: { min: 0, max: 500 },
  },
  retrieval: {
    top_k: { min: 1, max: 100 },
    similarity_threshold: { min: 0.0, max: 1.0 },
    mmr_lambda: { min: 0.0, max: 1.0 },
    hybrid_alpha: { min: 0.0, max: 1.0 },
  },
  generation: {
    temperature: { min: 0.0, max: 2.0 },
    top_p: { min: 0.0, max: 1.0 },
    max_tokens: { min: 100, max: 16000 },
    frequency_penalty: { min: -2.0, max: 2.0 },
    presence_penalty: { min: -2.0, max: 2.0 },
  },
} as const;

// =============================================================================
// Display Labels for UI
// =============================================================================

export const CHUNKING_STRATEGY_LABELS: Record<ChunkingStrategy, string> = {
  [ChunkingStrategy.FIXED]: 'Fixed',
  [ChunkingStrategy.RECURSIVE]: 'Recursive',
  [ChunkingStrategy.SEMANTIC]: 'Semantic',
};

export const RETRIEVAL_METHOD_LABELS: Record<RetrievalMethod, string> = {
  [RetrievalMethod.VECTOR]: 'Vector',
  [RetrievalMethod.HYBRID]: 'Hybrid',
  [RetrievalMethod.HYDE]: 'HyDE',
};

export const CITATION_STYLE_LABELS: Record<CitationStyle, string> = {
  [CitationStyle.INLINE]: 'Inline',
  [CitationStyle.FOOTNOTE]: 'Footnote',
  [CitationStyle.NONE]: 'None',
};

export const UNCERTAINTY_HANDLING_LABELS: Record<UncertaintyHandling, string> = {
  [UncertaintyHandling.ACKNOWLEDGE]: 'Acknowledge Uncertainty',
  [UncertaintyHandling.REFUSE]: 'Refuse Response',
  [UncertaintyHandling.BEST_EFFORT]: 'Best Effort',
};

/**
 * Display labels for DocumentParserBackend enum
 * Story 7-32: Docling Document Parser Integration (AC-7.32.3)
 */
export const DOCUMENT_PARSER_BACKEND_LABELS: Record<DocumentParserBackend, string> = {
  [DocumentParserBackend.UNSTRUCTURED]: 'Unstructured (Default)',
  [DocumentParserBackend.DOCLING]: 'Docling',
  [DocumentParserBackend.AUTO]: 'Auto',
};

export const DOCUMENT_PARSER_BACKEND_DESCRIPTIONS: Record<DocumentParserBackend, string> = {
  [DocumentParserBackend.UNSTRUCTURED]: 'Standard parser for PDF, DOCX, Markdown',
  [DocumentParserBackend.DOCLING]: 'Advanced parser with better tables and layout analysis',
  [DocumentParserBackend.AUTO]: 'Try Docling first, fallback to Unstructured on failure',
};
