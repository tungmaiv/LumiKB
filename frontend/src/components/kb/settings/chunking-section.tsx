'use client';

/**
 * Chunking Section Component - Story 7-14: KB Settings UI - General Panel (AC-7.14.2)
 *
 * Provides UI controls for chunking configuration:
 * - Strategy dropdown (Fixed, Recursive, Semantic)
 * - Chunk size slider (100-2000, default 512)
 * - Chunk overlap slider (0-500, default 50)
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import {
  ChunkingStrategy,
  CHUNKING_STRATEGY_LABELS,
  KB_SETTINGS_CONSTRAINTS,
} from '@/types/kb-settings';
import type { KBSettingsFormData } from './general-panel';

interface ChunkingSectionProps {
  form: UseFormReturn<KBSettingsFormData>;
  disabled?: boolean;
}

export function ChunkingSection({
  form,
  disabled = false,
}: ChunkingSectionProps): React.ReactElement {
  const { chunking } = KB_SETTINGS_CONSTRAINTS;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Chunking</h3>
      <p className="text-xs text-muted-foreground">
        Configure how documents are split into chunks for processing.
      </p>

      {/* Strategy Dropdown (AC-7.14.2) */}
      <FormField
        control={form.control}
        name="chunking.strategy"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Strategy</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select chunking strategy" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(ChunkingStrategy).map((strategy) => (
                  <SelectItem key={strategy} value={strategy}>
                    {CHUNKING_STRATEGY_LABELS[strategy]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              Method used to split documents into chunks.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Chunk Size Slider (AC-7.14.2) */}
      <FormField
        control={form.control}
        name="chunking.chunk_size"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Chunk Size</FormLabel>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={field.value}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    if (!isNaN(val)) {
                      field.onChange(
                        Math.max(chunking.chunk_size.min, Math.min(chunking.chunk_size.max, val))
                      );
                    }
                  }}
                  className="w-20 h-8 text-sm"
                  min={chunking.chunk_size.min}
                  max={chunking.chunk_size.max}
                  disabled={disabled}
                />
                <span className="text-xs text-muted-foreground">tokens</span>
              </div>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={chunking.chunk_size.min}
                max={chunking.chunk_size.max}
                step={10}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Target size for each document chunk ({chunking.chunk_size.min}-{chunking.chunk_size.max} tokens).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Chunk Overlap Slider (AC-7.14.2) */}
      <FormField
        control={form.control}
        name="chunking.chunk_overlap"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Chunk Overlap</FormLabel>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={field.value}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    if (!isNaN(val)) {
                      field.onChange(
                        Math.max(chunking.chunk_overlap.min, Math.min(chunking.chunk_overlap.max, val))
                      );
                    }
                  }}
                  className="w-20 h-8 text-sm"
                  min={chunking.chunk_overlap.min}
                  max={chunking.chunk_overlap.max}
                  disabled={disabled}
                />
                <span className="text-xs text-muted-foreground">tokens</span>
              </div>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={chunking.chunk_overlap.min}
                max={chunking.chunk_overlap.max}
                step={5}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Number of overlapping tokens between adjacent chunks ({chunking.chunk_overlap.min}-{chunking.chunk_overlap.max}).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
