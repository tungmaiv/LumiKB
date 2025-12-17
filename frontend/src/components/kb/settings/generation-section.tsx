'use client';

/**
 * Generation Section Component - Story 7-14: KB Settings UI - General Panel (AC-7.14.4)
 *
 * Provides UI controls for generation configuration:
 * - Temperature slider (0.0-2.0, default 0.7)
 * - Top P slider (0.0-1.0, default 1.0)
 * - Max tokens input (100-16000)
 */

import { UseFormReturn } from 'react-hook-form';
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { KB_SETTINGS_CONSTRAINTS } from '@/types/kb-settings';
import type { KBSettingsFormData } from './general-panel';

interface GenerationSectionProps {
  form: UseFormReturn<KBSettingsFormData>;
  disabled?: boolean;
}

export function GenerationSection({
  form,
  disabled = false,
}: GenerationSectionProps): React.ReactElement {
  const { generation } = KB_SETTINGS_CONSTRAINTS;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Generation</h3>
      <p className="text-xs text-muted-foreground">
        Configure parameters for AI response generation.
      </p>

      {/* Temperature Slider (AC-7.14.4) */}
      <FormField
        control={form.control}
        name="generation.temperature"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Temperature</FormLabel>
              <span className="text-sm font-medium">{field.value.toFixed(2)}</span>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={generation.temperature.min}
                max={generation.temperature.max}
                step={0.05}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Controls randomness in responses. Lower values are more focused, higher values are
              more creative (0.0-2.0).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Top P Slider (AC-7.14.4) */}
      <FormField
        control={form.control}
        name="generation.top_p"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Top P (Nucleus Sampling)</FormLabel>
              <span className="text-sm font-medium">{field.value.toFixed(2)}</span>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={generation.top_p.min}
                max={generation.top_p.max}
                step={0.05}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Limits token selection to top probability mass (0.0-1.0). Lower values are more
              focused.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Max Tokens Input (AC-7.14.4) */}
      <FormField
        control={form.control}
        name="generation.max_tokens"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Max Tokens</FormLabel>
            <FormControl>
              <Input
                type="number"
                value={field.value}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  if (!isNaN(val)) {
                    field.onChange(val);
                  }
                }}
                min={generation.max_tokens.min}
                max={generation.max_tokens.max}
                disabled={disabled}
                className="w-full"
              />
            </FormControl>
            <FormDescription>
              Maximum number of tokens in generated responses (
              {generation.max_tokens.min.toLocaleString()}-
              {generation.max_tokens.max.toLocaleString()}).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
