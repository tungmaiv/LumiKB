/**
 * Types for LLM Model Registry.
 * Story 7-9: LLM Model Registry
 */

export type ModelType = 'embedding' | 'generation' | 'ner';
export type ModelProvider = 'ollama' | 'openai' | 'azure' | 'gemini' | 'anthropic' | 'cohere' | 'deepseek' | 'qwen' | 'mistral' | 'lmstudio';
export type ModelStatus = 'active' | 'inactive' | 'deprecated';
export type DistanceMetric = 'cosine' | 'dot' | 'euclidean';
export type ResponseFormat = 'json' | 'text';

export interface EmbeddingModelConfig {
  dimensions: number;
  max_tokens: number;
  normalize: boolean;
  distance_metric: DistanceMetric;
  batch_size: number;
  tags: string[];
}

export interface GenerationModelConfig {
  context_window: number;
  max_output_tokens: number;
  supports_streaming: boolean;
  supports_json_mode: boolean;
  supports_vision: boolean;
  temperature_default: number;
  temperature_range: [number, number];
  top_p_default: number;
  cost_per_1m_input: number;
  cost_per_1m_output: number;
  tags: string[];
}

export interface NERModelConfig {
  max_tokens: number;
  temperature_default: number;
  top_p_default: number;
  top_k_default: number;
  response_format: ResponseFormat;
  logprobs_enabled: boolean;
  stop_sequences: string[];
  cost_per_1m_input: number;
  cost_per_1m_output: number;
  tags: string[];
}

export interface LLMModelSummary {
  id: string;
  type: ModelType;
  provider: ModelProvider;
  name: string;
  model_id: string;
  status: ModelStatus;
  is_default: boolean;
  has_api_key: boolean;
}

export interface LLMModelResponse extends LLMModelSummary {
  config: EmbeddingModelConfig | GenerationModelConfig | NERModelConfig | Record<string, unknown>;
  api_endpoint: string | null;
  created_at: string;
  updated_at: string;
}

export interface LLMModelCreate {
  type: ModelType;
  provider: ModelProvider;
  name: string;
  model_id: string;
  config: Partial<EmbeddingModelConfig | GenerationModelConfig | NERModelConfig>;
  api_endpoint?: string | null;
  api_key?: string | null;
  is_default?: boolean;
}

export interface LLMModelUpdate {
  name?: string;
  model_id?: string;
  config?: Partial<EmbeddingModelConfig | GenerationModelConfig | NERModelConfig>;
  api_endpoint?: string | null;
  api_key?: string | null;
  status?: ModelStatus;
  is_default?: boolean;
}

export interface LLMModelList {
  models: LLMModelSummary[];
  total: number;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
  details: Record<string, unknown> | null;
}

export interface ModelAvailableResponse {
  embedding_models: LLMModelSummary[];
  generation_models: LLMModelSummary[];
  ner_models: LLMModelSummary[];
}

export interface ModelPublicInfo {
  id: string;
  name: string;
  provider: ModelProvider;
  model_id: string;
  config: Record<string, unknown>;
}

// Provider display names and metadata
export const PROVIDER_INFO: Record<ModelProvider, { name: string; icon: string; description: string }> = {
  ollama: { name: 'Ollama', icon: 'ollama', description: 'Local models via Ollama' },
  openai: { name: 'OpenAI', icon: 'openai', description: 'GPT models' },
  azure: { name: 'Azure OpenAI', icon: 'azure', description: 'Azure-hosted OpenAI models' },
  gemini: { name: 'Google Gemini', icon: 'gemini', description: 'Google Gemini models' },
  anthropic: { name: 'Anthropic', icon: 'anthropic', description: 'Claude models' },
  cohere: { name: 'Cohere', icon: 'cohere', description: 'Cohere models' },
  deepseek: { name: 'DeepSeek', icon: 'deepseek', description: 'DeepSeek AI models' },
  qwen: { name: 'Qwen', icon: 'qwen', description: 'Alibaba Qwen models' },
  mistral: { name: 'Mistral AI', icon: 'mistral', description: 'Mistral AI models' },
  lmstudio: { name: 'LM Studio', icon: 'lmstudio', description: 'Local models via LM Studio' },
};

export const MODEL_TYPE_INFO: Record<ModelType, { name: string; description: string }> = {
  embedding: { name: 'Embedding', description: 'Vector embeddings for semantic search' },
  generation: { name: 'Generation', description: 'Text generation and completion' },
  ner: { name: 'NER', description: 'Named Entity Recognition for GraphRAG' },
};

export const MODEL_STATUS_INFO: Record<ModelStatus, { name: string; color: string }> = {
  active: { name: 'Active', color: 'green' },
  inactive: { name: 'Inactive', color: 'gray' },
  deprecated: { name: 'Deprecated', color: 'amber' },
};
