/**
 * Types for LLM Configuration (Story 7-2)
 * Centralized LLM configuration with hot-reload capability.
 */

/**
 * Information about a configured LLM model.
 */
export interface LLMConfigModelInfo {
  model_id: string | null;
  name: string;
  provider: string;
  model_identifier: string;
  api_endpoint: string | null;
  is_default: boolean;
  status: string;
}

/**
 * LLM generation settings for temperature, tokens, etc.
 */
export interface LLMConfigSettings {
  temperature: number;
  max_tokens: number;
  top_p: number;
}

/**
 * Centralized LLM configuration response.
 * AC-7.2.1: Displays current LLM model settings including provider,
 * model name, base URL, and key parameters.
 */
export interface LLMConfig {
  embedding_model: LLMConfigModelInfo | null;
  generation_model: LLMConfigModelInfo | null;
  generation_settings: LLMConfigSettings;
  litellm_base_url: string;
  last_modified: string | null;
  last_modified_by: string | null;
}

/**
 * Request to update LLM configuration.
 * AC-7.2.2: Model switching applies without service restart.
 */
export interface LLMConfigUpdateRequest {
  embedding_model_id?: string | null;
  generation_model_id?: string | null;
  generation_settings?: Partial<LLMConfigSettings> | null;
}

/**
 * Warning about embedding dimension mismatch.
 * AC-7.2.3: Triggered when selected model dimensions differ from existing KB collections.
 */
export interface DimensionMismatchWarning {
  has_mismatch: boolean;
  current_dimensions: number | null;
  new_dimensions: number | null;
  affected_kbs: string[];
  warning_message: string | null;
}

/**
 * Response after updating LLM configuration.
 */
export interface LLMConfigUpdateResponse {
  config: LLMConfig;
  hot_reload_applied: boolean;
  dimension_warning: DimensionMismatchWarning | null;
}

/**
 * Health status for a configured model.
 * AC-7.2.4: Health status shown for each configured model.
 */
export interface ModelHealthStatus {
  model_type: string;
  model_name: string;
  is_healthy: boolean;
  latency_ms: number | null;
  error_message: string | null;
  last_checked: string;
}

/**
 * Health status response for all configured models.
 */
export interface LLMHealthResponse {
  embedding_health: ModelHealthStatus | null;
  generation_health: ModelHealthStatus | null;
  overall_healthy: boolean;
}

/**
 * Response for query rewriter model configuration.
 * Story 8-0: History-Aware Query Rewriting
 */
export interface RewriterModelResponse {
  model_id: string | null;
}

/**
 * Request to update query rewriter model configuration.
 * Story 8-0: History-Aware Query Rewriting
 */
export interface RewriterModelUpdateRequest {
  model_id: string | null;
}
