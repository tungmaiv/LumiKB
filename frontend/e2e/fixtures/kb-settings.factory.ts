/**
 * KB Settings Factory - Story 7-14/7-15 ATDD
 * Generated: 2025-12-09 (Updated: 2025-12-10)
 *
 * Provides factory functions for KB Settings test data.
 * Mirrors backend schema from backend/app/schemas/kb_settings.py
 */

// =============================================================================
// Enum Types (mirror backend)
// =============================================================================

export type ChunkingStrategy = 'fixed' | 'recursive' | 'semantic';
export type RetrievalMethod = 'vector' | 'hybrid' | 'hyde';
export type CitationStyle = 'inline' | 'footnote' | 'none';
export type UncertaintyHandling = 'acknowledge' | 'refuse' | 'best_effort';

// =============================================================================
// Config Interfaces
// =============================================================================

export interface ChunkingConfig {
  strategy: ChunkingStrategy;
  chunk_size: number;
  chunk_overlap: number;
}

export interface RetrievalConfig {
  top_k: number;
  similarity_threshold: number;
  method: RetrievalMethod;
  mmr_enabled: boolean;
  mmr_lambda: number;
}

export interface GenerationConfig {
  temperature: number;
  top_p: number;
  max_tokens: number;
}

export interface PromptsConfig {
  system_prompt: string;
  context_template?: string;
  citation_style: CitationStyle;
  uncertainty_handling: UncertaintyHandling;
  response_language: string;
}

export interface KBSettings {
  chunking: ChunkingConfig;
  retrieval: RetrievalConfig;
  generation: GenerationConfig;
  prompts?: PromptsConfig;
  preset?: string;
}

// =============================================================================
// Default Values (from backend kb_settings.py)
// =============================================================================

export const DEFAULT_CHUNKING: ChunkingConfig = {
  strategy: 'recursive',
  chunk_size: 512,
  chunk_overlap: 50,
};

export const DEFAULT_RETRIEVAL: RetrievalConfig = {
  top_k: 10,
  similarity_threshold: 0.7,
  method: 'vector',
  mmr_enabled: false,
  mmr_lambda: 0.5,
};

export const DEFAULT_GENERATION: GenerationConfig = {
  temperature: 0.7,
  top_p: 1.0,
  max_tokens: 4096,
};

export const DEFAULT_PROMPTS: PromptsConfig = {
  system_prompt: 'You are a helpful assistant for {kb_name}. Use the provided context to answer questions accurately.',
  context_template: 'Context:\n{context}\n\nQuestion: {query}',
  citation_style: 'inline',
  uncertainty_handling: 'acknowledge',
  response_language: '',
};

// =============================================================================
// Factory Functions
// =============================================================================

export function createChunkingConfig(
  overrides?: Partial<ChunkingConfig>
): ChunkingConfig {
  return { ...DEFAULT_CHUNKING, ...overrides };
}

export function createRetrievalConfig(
  overrides?: Partial<RetrievalConfig>
): RetrievalConfig {
  return { ...DEFAULT_RETRIEVAL, ...overrides };
}

export function createGenerationConfig(
  overrides?: Partial<GenerationConfig>
): GenerationConfig {
  return { ...DEFAULT_GENERATION, ...overrides };
}

export function createPromptsConfig(
  overrides?: Partial<PromptsConfig>
): PromptsConfig {
  return { ...DEFAULT_PROMPTS, ...overrides };
}

export function createKBSettings(overrides?: {
  chunking?: Partial<ChunkingConfig>;
  retrieval?: Partial<RetrievalConfig>;
  generation?: Partial<GenerationConfig>;
  prompts?: Partial<PromptsConfig>;
}): KBSettings {
  return {
    chunking: createChunkingConfig(overrides?.chunking),
    retrieval: createRetrievalConfig(overrides?.retrieval),
    generation: createGenerationConfig(overrides?.generation),
    prompts: overrides?.prompts ? createPromptsConfig(overrides.prompts) : undefined,
  };
}

export function createKBSettingsWithPrompts(overrides?: {
  chunking?: Partial<ChunkingConfig>;
  retrieval?: Partial<RetrievalConfig>;
  generation?: Partial<GenerationConfig>;
  prompts?: Partial<PromptsConfig>;
}): KBSettings & { prompts: PromptsConfig } {
  return {
    chunking: createChunkingConfig(overrides?.chunking),
    retrieval: createRetrievalConfig(overrides?.retrieval),
    generation: createGenerationConfig(overrides?.generation),
    prompts: createPromptsConfig(overrides?.prompts),
  };
}

export function createInvalidSettings(): Record<string, unknown> {
  return {
    chunking: { chunk_size: 50 }, // below min 100
    retrieval: { similarity_threshold: 1.5 }, // above max 1.0
    generation: { temperature: 3.0 }, // above max 2.0
  };
}

export function createInvalidPromptsSettings(): Record<string, unknown> {
  return {
    prompts: {
      system_prompt: 'x'.repeat(5000), // exceeds max 4000 characters
      citation_style: 'invalid_style', // invalid enum value
      uncertainty_handling: 'invalid_handling', // invalid enum value
      response_language: 'this_is_way_too_long_for_a_language_code', // exceeds max 10 chars
    },
  };
}

// =============================================================================
// Template Factories (for AC-7.15.8)
// =============================================================================

export const PROMPT_TEMPLATES = {
  default_rag: {
    id: 'default_rag',
    name: 'Default RAG',
    system_prompt: 'You are a helpful assistant for {kb_name}. Use the provided context to answer questions accurately.',
    citation_style: 'inline' as CitationStyle,
    uncertainty_handling: 'acknowledge' as UncertaintyHandling,
  },
  strict_citations: {
    id: 'strict_citations',
    name: 'Strict Citations',
    system_prompt: 'You are a precise assistant. Only answer based on the provided context. Always cite sources using [1], [2] notation.',
    citation_style: 'inline' as CitationStyle,
    uncertainty_handling: 'refuse' as UncertaintyHandling,
  },
  conversational: {
    id: 'conversational',
    name: 'Conversational',
    system_prompt: 'You are a friendly assistant. Answer naturally while incorporating information from the context when relevant.',
    citation_style: 'none' as CitationStyle,
    uncertainty_handling: 'best_effort' as UncertaintyHandling,
  },
  technical_documentation: {
    id: 'technical_documentation',
    name: 'Technical Documentation',
    system_prompt: 'You are a technical documentation assistant. Provide detailed, accurate answers with references to source documents.',
    citation_style: 'footnote' as CitationStyle,
    uncertainty_handling: 'acknowledge' as UncertaintyHandling,
  },
};
