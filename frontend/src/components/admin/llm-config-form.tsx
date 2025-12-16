/**
 * LLM Configuration Form Component
 * Story 7-2: Centralized LLM Configuration (AC-7.2.1, AC-7.2.2)
 *
 * Displays and edits current LLM model settings including:
 * - Embedding model selection
 * - Generation model selection
 * - Generation parameters (temperature, max_tokens, top_p)
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Info, RefreshCw, Server } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LLMConfig, LLMConfigUpdateRequest, LLMConfigSettings } from '@/types/llm-config';
import type { LLMModelSummary } from '@/types/llm-model';
import { useAvailableModels } from '@/hooks/useAvailableModels';

interface LLMConfigFormProps {
  config: LLMConfig;
  onSubmit: (request: LLMConfigUpdateRequest) => Promise<void>;
  isSubmitting: boolean;
  onRefetch: () => void;
  lastFetched: Date | null;
}

interface FormData {
  embedding_model_id: string;
  generation_model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
}

export function LLMConfigForm({
  config,
  onSubmit,
  isSubmitting,
  onRefetch,
  lastFetched,
}: LLMConfigFormProps) {
  const { embeddingModels, generationModels, isLoading: modelsLoading } = useAvailableModels();
  const [hasChanges, setHasChanges] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      embedding_model_id: config.embedding_model?.model_id || '',
      generation_model_id: config.generation_model?.model_id || '',
      temperature: config.generation_settings.temperature,
      max_tokens: config.generation_settings.max_tokens,
      top_p: config.generation_settings.top_p,
    },
  });

  // Update form when config changes
  useEffect(() => {
    reset({
      embedding_model_id: config.embedding_model?.model_id || '',
      generation_model_id: config.generation_model?.model_id || '',
      temperature: config.generation_settings.temperature,
      max_tokens: config.generation_settings.max_tokens,
      top_p: config.generation_settings.top_p,
    });
    setHasChanges(false);
  }, [config, reset]);

  // Track changes
  const watchedValues = watch();
  useEffect(() => {
    const changed =
      watchedValues.embedding_model_id !== (config.embedding_model?.model_id || '') ||
      watchedValues.generation_model_id !== (config.generation_model?.model_id || '') ||
      watchedValues.temperature !== config.generation_settings.temperature ||
      watchedValues.max_tokens !== config.generation_settings.max_tokens ||
      watchedValues.top_p !== config.generation_settings.top_p;
    setHasChanges(changed);
  }, [watchedValues, config]);

  const onFormSubmit = async (data: FormData) => {
    const request: LLMConfigUpdateRequest = {};

    // Only include changed model IDs
    if (data.embedding_model_id !== (config.embedding_model?.model_id || '')) {
      request.embedding_model_id = data.embedding_model_id || null;
    }
    if (data.generation_model_id !== (config.generation_model?.model_id || '')) {
      request.generation_model_id = data.generation_model_id || null;
    }

    // Include settings if any changed
    const settingsChanged =
      data.temperature !== config.generation_settings.temperature ||
      data.max_tokens !== config.generation_settings.max_tokens ||
      data.top_p !== config.generation_settings.top_p;

    if (settingsChanged) {
      request.generation_settings = {
        temperature: data.temperature,
        max_tokens: data.max_tokens,
        top_p: data.top_p,
      };
    }

    await onSubmit(request);
  };

  const formatLastFetched = () => {
    if (!lastFetched) return 'Never';
    const now = new Date();
    const diff = Math.floor((now.getTime() - lastFetched.getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return lastFetched.toLocaleTimeString();
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      {/* LiteLLM Proxy Info */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">LiteLLM Proxy</CardTitle>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Updated {formatLastFetched()}</span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onRefetch}
                className="h-8 w-8 p-0"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <code className="rounded bg-muted px-2 py-1 text-sm">
              {config.litellm_base_url}
            </code>
            <span className="text-sm text-muted-foreground">
              All LLM requests route through this proxy
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Active Models</CardTitle>
          <CardDescription>
            Select the default models for embedding and generation tasks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Embedding Model */}
          <div className="space-y-2">
            <Label htmlFor="embedding_model_id" className="flex items-center gap-1">
              Embedding Model
              <Tooltip>
                <TooltipTrigger type="button" className="cursor-help">
                  <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p>Used for converting documents and queries into vector embeddings for semantic search.</p>
                </TooltipContent>
              </Tooltip>
            </Label>
            <Select
              value={watch('embedding_model_id')}
              onValueChange={(value) => setValue('embedding_model_id', value)}
              disabled={modelsLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={modelsLoading ? 'Loading models...' : 'Select embedding model'} />
              </SelectTrigger>
              <SelectContent>
                {embeddingModels.map((model: LLMModelSummary) => (
                  <SelectItem key={model.id} value={model.id}>
                    <span className="flex items-center gap-2">
                      <span>{model.name}</span>
                      {model.is_default && (
                        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">
                          Default
                        </span>
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {config.embedding_model && (
              <p className="text-xs text-muted-foreground">
                Current: {config.embedding_model.name} ({config.embedding_model.provider})
              </p>
            )}
          </div>

          {/* Generation Model */}
          <div className="space-y-2">
            <Label htmlFor="generation_model_id" className="flex items-center gap-1">
              Generation Model
              <Tooltip>
                <TooltipTrigger type="button" className="cursor-help">
                  <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p>Used for generating answers, synthesizing content, and chat responses.</p>
                </TooltipContent>
              </Tooltip>
            </Label>
            <Select
              value={watch('generation_model_id')}
              onValueChange={(value) => setValue('generation_model_id', value)}
              disabled={modelsLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={modelsLoading ? 'Loading models...' : 'Select generation model'} />
              </SelectTrigger>
              <SelectContent>
                {generationModels.map((model: LLMModelSummary) => (
                  <SelectItem key={model.id} value={model.id}>
                    <span className="flex items-center gap-2">
                      <span>{model.name}</span>
                      {model.is_default && (
                        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">
                          Default
                        </span>
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {config.generation_model && (
              <p className="text-xs text-muted-foreground">
                Current: {config.generation_model.name} ({config.generation_model.provider})
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Generation Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Generation Parameters</CardTitle>
          <CardDescription>
            Default parameters for text generation (can be overridden per-request)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Temperature */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="temperature" className="flex items-center gap-1">
                Temperature
                <Tooltip>
                  <TooltipTrigger type="button" className="cursor-help">
                    <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="font-medium mb-1">Controls randomness in responses</p>
                    <p><strong>Low (0-0.3):</strong> Deterministic, focused</p>
                    <p><strong>Medium (0.4-0.7):</strong> Balanced</p>
                    <p><strong>High (0.8-2.0):</strong> Creative, varied</p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <span className="text-sm font-medium">{watch('temperature').toFixed(1)}</span>
            </div>
            <Slider
              id="temperature"
              value={[watch('temperature')]}
              onValueChange={([value]) => setValue('temperature', value)}
              min={0}
              max={2}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Precise (0)</span>
              <span>Creative (2)</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div className="space-y-2">
            <Label htmlFor="max_tokens" className="flex items-center gap-1">
              Max Output Tokens
              <Tooltip>
                <TooltipTrigger type="button" className="cursor-help">
                  <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p>Maximum number of tokens in generated responses. Higher values allow longer responses but use more resources.</p>
                </TooltipContent>
              </Tooltip>
            </Label>
            <Input
              id="max_tokens"
              type="number"
              {...register('max_tokens', {
                valueAsNumber: true,
                min: { value: 1, message: 'Must be at least 1' },
                max: { value: 100000, message: 'Must be at most 100,000' },
              })}
              className="w-full"
            />
            {errors.max_tokens && (
              <p className="text-sm text-destructive">{errors.max_tokens.message}</p>
            )}
          </div>

          {/* Top P */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="top_p" className="flex items-center gap-1">
                Top P (Nucleus Sampling)
                <Tooltip>
                  <TooltipTrigger type="button" className="cursor-help">
                    <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="font-medium mb-1">Controls token selection threshold</p>
                    <p><strong>1.0:</strong> Consider all tokens (recommended)</p>
                    <p><strong>0.9:</strong> Top 90% probable tokens</p>
                    <p className="mt-1 text-xs italic">Usually keep at 1.0 and adjust Temperature instead.</p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <span className="text-sm font-medium">{watch('top_p').toFixed(2)}</span>
            </div>
            <Slider
              id="top_p"
              value={[watch('top_p')]}
              onValueChange={([value]) => setValue('top_p', value)}
              min={0}
              max={1}
              step={0.05}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Focused (0)</span>
              <span>All tokens (1)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Last Modified Info */}
      {config.last_modified && (
        <p className="text-sm text-muted-foreground">
          Last modified: {new Date(config.last_modified).toLocaleString()}
          {config.last_modified_by && ` by ${config.last_modified_by}`}
        </p>
      )}

      {/* Submit Button */}
      <div className="flex justify-end gap-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => reset()}
          disabled={!hasChanges || isSubmitting}
        >
          Reset
        </Button>
        <Button type="submit" disabled={!hasChanges || isSubmitting}>
          {isSubmitting ? 'Applying Changes...' : 'Apply Changes'}
        </Button>
      </div>
    </form>
  );
}
