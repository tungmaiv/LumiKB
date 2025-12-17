/**
 * Modal for creating and editing LLM models
 * Story 7-9: LLM Model Registry (AC-7.9.3, AC-7.9.5)
 */

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Info } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type {
  LLMModelResponse,
  LLMModelCreate,
  LLMModelUpdate,
  ModelType,
  ModelProvider,
  ModelStatus,
} from '@/types/llm-model';
import { PROVIDER_INFO, MODEL_TYPE_INFO, MODEL_STATUS_INFO } from '@/types/llm-model';
import { ProviderLogo, PROVIDER_COLORS } from './provider-logo';

interface ModelFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  model?: LLMModelResponse | null;
  onSubmit: (data: LLMModelCreate | LLMModelUpdate) => Promise<void>;
  isSubmitting: boolean;
}

interface FormData {
  name: string;
  model_id: string;
  type: ModelType;
  provider: ModelProvider;
  status: ModelStatus;
  api_endpoint: string;
  api_key: string;
  is_default: boolean;
  // Embedding config
  dimensions: number;
  max_tokens: number;
  normalize: boolean;
  distance_metric: 'cosine' | 'dot' | 'euclidean';
  batch_size: number;
  // Generation config
  context_window: number;
  max_output_tokens: number;
  supports_streaming: boolean;
  supports_json_mode: boolean;
  supports_vision: boolean;
  temperature_default: number;
  top_p_default: number;
  timeout_seconds: number;
  cost_per_1m_input: number;
  cost_per_1m_output: number;
  // NER config
  ner_max_tokens: number;
  ner_temperature_default: number;
  ner_top_p_default: number;
  ner_top_k_default: number;
  ner_response_format: 'json' | 'text';
  ner_logprobs_enabled: boolean;
  ner_stop_sequences: string;
  ner_timeout_seconds: number;
  ner_cost_per_1m_input: number;
  ner_cost_per_1m_output: number;
}

const MODEL_TYPES: ModelType[] = ['embedding', 'generation', 'ner'];
const MODEL_PROVIDERS: ModelProvider[] = [
  'openai',
  'anthropic',
  'azure',
  'gemini',
  'mistral',
  'deepseek',
  'qwen',
  'cohere',
  'ollama',
  'lmstudio',
];
const MODEL_STATUSES: ModelStatus[] = ['active', 'inactive', 'deprecated'];
const DISTANCE_METRICS: Array<'cosine' | 'dot' | 'euclidean'> = ['cosine', 'dot', 'euclidean'];

export function ModelFormModal({
  open,
  onOpenChange,
  model,
  onSubmit,
  isSubmitting,
}: ModelFormModalProps) {
  const isEditing = !!model;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      name: '',
      model_id: '',
      type: 'generation',
      provider: 'openai',
      status: 'active',
      api_endpoint: '',
      api_key: '',
      is_default: false,
      // Embedding defaults
      dimensions: 1536,
      max_tokens: 8192,
      normalize: true,
      distance_metric: 'cosine',
      batch_size: 32,
      // Generation defaults
      context_window: 128000,
      max_output_tokens: 4096,
      supports_streaming: true,
      supports_json_mode: false,
      supports_vision: false,
      temperature_default: 0.7,
      top_p_default: 1.0,
      timeout_seconds: 120,
      cost_per_1m_input: 0,
      cost_per_1m_output: 0,
      // NER defaults
      ner_max_tokens: 4096,
      ner_temperature_default: 0,
      ner_top_p_default: 0.15,
      ner_top_k_default: 30,
      ner_response_format: 'json',
      ner_logprobs_enabled: true,
      ner_stop_sequences: '\\n\\n,<END>,</json>',
      ner_timeout_seconds: 30,
      ner_cost_per_1m_input: 0,
      ner_cost_per_1m_output: 0,
    },
  });

  // eslint-disable-next-line react-hooks/incompatible-library -- react-hook-form's watch() is designed this way
  const selectedType = watch('type');

  // Reset form when model changes
  useEffect(() => {
    if (model) {
      const config = model.config as Record<string, unknown>;
      // Handle stop_sequences array to string conversion
      const stopSeqArray = (config?.stop_sequences as string[]) || ['\n\n', '<END>', '</json>'];
      const stopSeqString = stopSeqArray.join(',');

      reset({
        name: model.name,
        model_id: model.model_id,
        type: model.type,
        provider: model.provider,
        status: model.status,
        api_endpoint: model.api_endpoint || '',
        api_key: '', // Never pre-fill API key
        is_default: model.is_default,
        // Embedding config
        dimensions: (config?.dimensions as number) || 1536,
        max_tokens: (config?.max_tokens as number) || 8192,
        normalize: (config?.normalize as boolean) ?? true,
        distance_metric: (config?.distance_metric as 'cosine' | 'dot' | 'euclidean') || 'cosine',
        batch_size: (config?.batch_size as number) || 32,
        // Generation config
        context_window: (config?.context_window as number) || 128000,
        max_output_tokens: (config?.max_output_tokens as number) || 4096,
        supports_streaming: (config?.supports_streaming as boolean) ?? true,
        supports_json_mode: (config?.supports_json_mode as boolean) ?? false,
        supports_vision: (config?.supports_vision as boolean) ?? false,
        temperature_default: (config?.temperature_default as number) || 0.7,
        top_p_default: (config?.top_p_default as number) || 1.0,
        timeout_seconds: (config?.timeout_seconds as number) || 120,
        cost_per_1m_input:
          (config?.cost_per_1m_input as number) || (config?.cost_per_1k_input as number) || 0,
        cost_per_1m_output:
          (config?.cost_per_1m_output as number) || (config?.cost_per_1k_output as number) || 0,
        // NER config
        ner_max_tokens: (config?.max_tokens as number) || 4096,
        ner_temperature_default: (config?.temperature_default as number) ?? 0,
        ner_top_p_default: (config?.top_p_default as number) ?? 0.15,
        ner_top_k_default: (config?.top_k_default as number) ?? 30,
        ner_response_format: (config?.response_format as 'json' | 'text') || 'json',
        ner_logprobs_enabled: (config?.logprobs_enabled as boolean) ?? true,
        ner_stop_sequences: stopSeqString,
        ner_timeout_seconds: (config?.timeout_seconds as number) || 30,
        ner_cost_per_1m_input: (config?.cost_per_1m_input as number) || 0,
        ner_cost_per_1m_output: (config?.cost_per_1m_output as number) || 0,
      });
    } else {
      reset({
        name: '',
        model_id: '',
        type: 'generation',
        provider: 'openai',
        status: 'active',
        api_endpoint: '',
        api_key: '',
        is_default: false,
        dimensions: 1536,
        max_tokens: 8192,
        normalize: true,
        distance_metric: 'cosine',
        batch_size: 32,
        context_window: 128000,
        max_output_tokens: 4096,
        supports_streaming: true,
        supports_json_mode: false,
        supports_vision: false,
        temperature_default: 0.7,
        top_p_default: 1.0,
        timeout_seconds: 120,
        cost_per_1m_input: 0,
        cost_per_1m_output: 0,
        // NER defaults
        ner_max_tokens: 4096,
        ner_temperature_default: 0,
        ner_top_p_default: 0.15,
        ner_top_k_default: 30,
        ner_response_format: 'json',
        ner_logprobs_enabled: true,
        ner_stop_sequences: '\\n\\n,<END>,</json>',
        ner_timeout_seconds: 30,
        ner_cost_per_1m_input: 0,
        ner_cost_per_1m_output: 0,
      });
    }
  }, [model, reset]);

  const onFormSubmit = async (data: FormData) => {
    // Trim string fields to prevent whitespace issues
    const trimmedApiEndpoint = data.api_endpoint?.trim() || '';
    const trimmedApiKey = data.api_key?.trim() || '';
    const trimmedName = data.name?.trim() || '';
    const trimmedModelId = data.model_id?.trim() || '';

    // Build config based on type
    let config;
    if (data.type === 'embedding') {
      config = {
        dimensions: data.dimensions,
        max_tokens: data.max_tokens,
        normalize: data.normalize,
        distance_metric: data.distance_metric,
        batch_size: data.batch_size,
        tags: [],
      };
    } else if (data.type === 'ner') {
      // Parse stop_sequences from comma-separated string
      const stopSequences = data.ner_stop_sequences
        .split(',')
        .map((s) => s.trim().replace(/\\n/g, '\n'))
        .filter((s) => s.length > 0);
      config = {
        max_tokens: data.ner_max_tokens,
        temperature_default: data.ner_temperature_default,
        top_p_default: data.ner_top_p_default,
        top_k_default: data.ner_top_k_default,
        response_format: data.ner_response_format,
        logprobs_enabled: data.ner_logprobs_enabled,
        stop_sequences: stopSequences,
        timeout_seconds: data.ner_timeout_seconds,
        cost_per_1m_input: data.ner_cost_per_1m_input,
        cost_per_1m_output: data.ner_cost_per_1m_output,
        tags: [],
      };
    } else {
      // Generation config
      config = {
        context_window: data.context_window,
        max_output_tokens: data.max_output_tokens,
        supports_streaming: data.supports_streaming,
        supports_json_mode: data.supports_json_mode,
        supports_vision: data.supports_vision,
        temperature_default: data.temperature_default,
        temperature_range: [0.0, 2.0] as [number, number],
        top_p_default: data.top_p_default,
        timeout_seconds: data.timeout_seconds,
        cost_per_1m_input: data.cost_per_1m_input,
        cost_per_1m_output: data.cost_per_1m_output,
        tags: [],
      };
    }

    if (isEditing) {
      const updateData: LLMModelUpdate = {
        name: trimmedName,
        model_id: trimmedModelId,
        config,
        api_endpoint: trimmedApiEndpoint || null,
        status: data.status,
        is_default: data.is_default,
      };
      // Only include api_key if it was provided
      if (trimmedApiKey) {
        updateData.api_key = trimmedApiKey;
      }
      await onSubmit(updateData);
    } else {
      const createData: LLMModelCreate = {
        type: data.type,
        provider: data.provider,
        name: trimmedName,
        model_id: trimmedModelId,
        config,
        api_endpoint: trimmedApiEndpoint || null,
        api_key: trimmedApiKey || null,
        is_default: data.is_default,
      };
      await onSubmit(createData);
    }

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Model' : 'Add Model'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the model configuration.'
              : 'Register a new LLM model for embedding or generation.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Display Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Display Name</Label>
            <Input
              id="name"
              {...register('name', { required: 'Name is required' })}
              placeholder="GPT-4 Turbo"
            />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>

          {/* Provider */}
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select
              value={watch('provider')}
              onValueChange={(value) => setValue('provider', value as ModelProvider)}
              disabled={isEditing}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select provider">
                  {watch('provider') && (
                    <span className="flex items-center gap-2">
                      <ProviderLogo
                        provider={watch('provider')}
                        size={18}
                        className={PROVIDER_COLORS[watch('provider')]}
                      />
                      {PROVIDER_INFO[watch('provider')].name}
                    </span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {MODEL_PROVIDERS.map((provider) => (
                  <SelectItem key={provider} value={provider}>
                    <span className="flex items-center gap-2">
                      <ProviderLogo
                        provider={provider}
                        size={18}
                        className={PROVIDER_COLORS[provider]}
                      />
                      <span className="flex flex-col">
                        <span className="font-medium">{PROVIDER_INFO[provider].name}</span>
                        <span className="text-xs text-muted-foreground">
                          {PROVIDER_INFO[provider].description}
                        </span>
                      </span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* API Configuration */}
          <div className="space-y-4">
            <h4 className="font-medium">API Configuration</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="api_endpoint">API Endpoint (Optional)</Label>
                <Input
                  id="api_endpoint"
                  {...register('api_endpoint')}
                  placeholder="https://api.example.com/v1"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="api_key">
                  API Key {isEditing && '(Leave blank to keep current)'}
                </Label>
                <Input id="api_key" type="password" {...register('api_key')} placeholder="sk-..." />
              </div>
            </div>
          </div>

          {/* Model ID and Type */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="model_id">Model ID</Label>
              <Input
                id="model_id"
                {...register('model_id', { required: 'Model ID is required' })}
                placeholder="gpt-4-turbo"
              />
              {errors.model_id && (
                <p className="text-sm text-destructive">{errors.model_id.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="type">Type</Label>
              <Select
                value={watch('type')}
                onValueChange={(value) => setValue('type', value as ModelType)}
                disabled={isEditing}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {MODEL_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {MODEL_TYPE_INFO[type].name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {isEditing && (
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={watch('status')}
                onValueChange={(value) => setValue('status', value as ModelStatus)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {MODEL_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {MODEL_STATUS_INFO[status].name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Type-Specific Config */}
          <Tabs value={selectedType} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="embedding" disabled>
                Embedding
              </TabsTrigger>
              <TabsTrigger value="generation" disabled>
                Generation
              </TabsTrigger>
              <TabsTrigger value="ner" disabled>
                NER
              </TabsTrigger>
            </TabsList>

            <TabsContent value="embedding" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="dimensions">Dimensions</Label>
                  <Input
                    id="dimensions"
                    type="number"
                    {...register('dimensions', { valueAsNumber: true, min: 1, max: 8192 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_tokens">Max Tokens</Label>
                  <Input
                    id="max_tokens"
                    type="number"
                    {...register('max_tokens', { valueAsNumber: true, min: 1 })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="distance_metric">Distance Metric</Label>
                  <Select
                    value={watch('distance_metric')}
                    onValueChange={(value) =>
                      setValue('distance_metric', value as 'cosine' | 'dot' | 'euclidean')
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DISTANCE_METRICS.map((metric) => (
                        <SelectItem key={metric} value={metric}>
                          {metric.charAt(0).toUpperCase() + metric.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="batch_size">Batch Size</Label>
                  <Input
                    id="batch_size"
                    type="number"
                    {...register('batch_size', { valueAsNumber: true, min: 1, max: 1000 })}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="normalize"
                  checked={watch('normalize')}
                  onCheckedChange={(checked) => setValue('normalize', checked)}
                />
                <Label htmlFor="normalize">Normalize Vectors</Label>
              </div>
            </TabsContent>

            <TabsContent value="generation" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="context_window">Context Window</Label>
                  <Input
                    id="context_window"
                    type="number"
                    {...register('context_window', { valueAsNumber: true, min: 1024 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_output_tokens">Max Output Tokens</Label>
                  <Input
                    id="max_output_tokens"
                    type="number"
                    {...register('max_output_tokens', { valueAsNumber: true, min: 1 })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="temperature_default" className="flex items-center gap-1">
                    Temperature
                    <Tooltip>
                      <TooltipTrigger type="button" className="cursor-help">
                        <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="font-medium mb-1">Temperature (Default: 0.7)</p>
                        <p>Controls randomness in responses.</p>
                        <p className="mt-1">
                          <strong>Low (0-0.3):</strong> Deterministic, focused output
                        </p>
                        <p>
                          <strong>Medium (0.4-0.7):</strong> Balanced creativity
                        </p>
                        <p>
                          <strong>High (0.8-2.0):</strong> More creative, varied responses
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Input
                    id="temperature_default"
                    type="number"
                    step="0.1"
                    {...register('temperature_default', {
                      valueAsNumber: true,
                      min: 0,
                      max: 2,
                    })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="top_p_default" className="flex items-center gap-1">
                    Top P
                    <Tooltip>
                      <TooltipTrigger type="button" className="cursor-help">
                        <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="font-medium mb-1">Top P / Nucleus Sampling (Default: 1.0)</p>
                        <p>Controls token selection threshold.</p>
                        <p className="mt-1">
                          <strong>1.0:</strong> Consider all tokens (recommended)
                        </p>
                        <p>
                          <strong>0.9:</strong> Top 90% probable tokens
                        </p>
                        <p>
                          <strong>Lower:</strong> More focused, less diverse output
                        </p>
                        <p className="mt-1 text-xs italic">
                          Tip: Usually keep at 1.0 and adjust Temperature instead.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Input
                    id="top_p_default"
                    type="number"
                    step="0.1"
                    {...register('top_p_default', { valueAsNumber: true, min: 0, max: 1 })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="timeout_seconds" className="flex items-center gap-1">
                    Timeout (seconds)
                    <Tooltip>
                      <TooltipTrigger type="button" className="cursor-help">
                        <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="font-medium mb-1">Request Timeout (Default: 120s)</p>
                        <p>Maximum time to wait for LLM response.</p>
                        <p className="mt-1">
                          <strong>Range:</strong> 1-600 seconds (10 min max)
                        </p>
                        <p className="mt-1 text-xs italic">
                          Tip: Set lower for fast models like query rewriters.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Input
                    id="timeout_seconds"
                    type="number"
                    step="1"
                    {...register('timeout_seconds', {
                      valueAsNumber: true,
                      min: 1,
                      max: 600,
                    })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cost_per_1m_input">Cost per 1M Input Tokens ($)</Label>
                  <Input
                    id="cost_per_1m_input"
                    type="number"
                    step="0.01"
                    {...register('cost_per_1m_input', { valueAsNumber: true, min: 0 })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cost_per_1m_output">Cost per 1M Output Tokens ($)</Label>
                <Input
                  id="cost_per_1m_output"
                  type="number"
                  step="0.01"
                  {...register('cost_per_1m_output', { valueAsNumber: true, min: 0 })}
                />
              </div>

              <div className="space-y-2">
                <Label>Capabilities</Label>
                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="supports_streaming"
                      checked={watch('supports_streaming')}
                      onCheckedChange={(checked) => setValue('supports_streaming', checked)}
                    />
                    <Label htmlFor="supports_streaming">Streaming</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="supports_json_mode"
                      checked={watch('supports_json_mode')}
                      onCheckedChange={(checked) => setValue('supports_json_mode', checked)}
                    />
                    <Label htmlFor="supports_json_mode">JSON Mode</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="supports_vision"
                      checked={watch('supports_vision')}
                      onCheckedChange={(checked) => setValue('supports_vision', checked)}
                    />
                    <Label htmlFor="supports_vision">Vision</Label>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* NER Configuration Tab */}
            <TabsContent value="ner" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ner_max_tokens">Max Tokens</Label>
                  <Input
                    id="ner_max_tokens"
                    type="number"
                    {...register('ner_max_tokens', { valueAsNumber: true, min: 1, max: 100000 })}
                  />
                  <p className="text-xs text-muted-foreground">Maximum output tokens</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ner_temperature_default">Temperature (Default: 0)</Label>
                  <Input
                    id="ner_temperature_default"
                    type="number"
                    step="0.1"
                    {...register('ner_temperature_default', {
                      valueAsNumber: true,
                      min: 0,
                      max: 2,
                    })}
                  />
                  <p className="text-xs text-muted-foreground">0 for deterministic output</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ner_top_p_default">Top P (Default: 0.15)</Label>
                  <Input
                    id="ner_top_p_default"
                    type="number"
                    step="0.05"
                    {...register('ner_top_p_default', { valueAsNumber: true, min: 0, max: 1 })}
                  />
                  <p className="text-xs text-muted-foreground">Recommended: 0.1-0.2</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ner_top_k_default">Top K (Default: 30)</Label>
                  <Input
                    id="ner_top_k_default"
                    type="number"
                    {...register('ner_top_k_default', { valueAsNumber: true, min: 1, max: 100 })}
                  />
                  <p className="text-xs text-muted-foreground">Recommended: 20-40</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ner_response_format">Response Format</Label>
                  <Select
                    value={watch('ner_response_format')}
                    onValueChange={(value) =>
                      setValue('ner_response_format', value as 'json' | 'text')
                    }
                  >
                    <SelectTrigger id="ner_response_format">
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="json">JSON (Strict)</SelectItem>
                      <SelectItem value="text">Text</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Use JSON for structured entity output
                  </p>
                </div>

                <div className="space-y-2 flex flex-col justify-center">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="ner_logprobs_enabled"
                      checked={watch('ner_logprobs_enabled')}
                      onCheckedChange={(checked) => setValue('ner_logprobs_enabled', checked)}
                    />
                    <Label htmlFor="ner_logprobs_enabled">Enable Logprobs</Label>
                  </div>
                  <p className="text-xs text-muted-foreground">Token probability tracking</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ner_stop_sequences">Stop Sequences</Label>
                  <Input
                    id="ner_stop_sequences"
                    placeholder="e.g., \n\n, <END>, </json>"
                    {...register('ner_stop_sequences')}
                  />
                  <p className="text-xs text-muted-foreground">Comma-separated stop sequences</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ner_timeout_seconds" className="flex items-center gap-1">
                    Timeout (seconds)
                    <Tooltip>
                      <TooltipTrigger type="button" className="cursor-help">
                        <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="font-medium mb-1">Request Timeout (Default: 30s)</p>
                        <p>Maximum time to wait for NER response.</p>
                        <p className="mt-1">
                          <strong>Range:</strong> 1-300 seconds (5 min max)
                        </p>
                        <p className="mt-1 text-xs italic">
                          NER models are typically fast - 30s is usually sufficient.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Input
                    id="ner_timeout_seconds"
                    type="number"
                    step="1"
                    {...register('ner_timeout_seconds', {
                      valueAsNumber: true,
                      min: 1,
                      max: 300,
                    })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ner_cost_per_1m_input">Cost per 1M Input Tokens ($)</Label>
                  <Input
                    id="ner_cost_per_1m_input"
                    type="number"
                    step="0.01"
                    {...register('ner_cost_per_1m_input', { valueAsNumber: true, min: 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ner_cost_per_1m_output">Cost per 1M Output Tokens ($)</Label>
                  <Input
                    id="ner_cost_per_1m_output"
                    type="number"
                    step="0.01"
                    {...register('ner_cost_per_1m_output', { valueAsNumber: true, min: 0 })}
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {/* Default Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="is_default"
              checked={watch('is_default')}
              onCheckedChange={(checked) => setValue('is_default', checked)}
            />
            <Label htmlFor="is_default">Set as default {selectedType} model</Label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : isEditing ? 'Update Model' : 'Add Model'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
