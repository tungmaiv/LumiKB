'use client';

/**
 * Preset Selector Component - Story 7-16: KB Settings Presets (AC-7.16.1, AC-7.16.7, AC-7.16.8)
 *
 * Dropdown selector for quick KB configuration presets with:
 * - Preset dropdown with Custom, Legal, Technical, Creative, Code, General options
 * - Confirmation dialog when overwriting custom settings
 * - Automatic preset detection based on current settings
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Wand2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { PRESET_OPTIONS, getPresetSettings, detectPreset } from '@/lib/kb-presets';
import type { KBSettings } from '@/types/kb-settings';

// =============================================================================
// Types
// =============================================================================

interface PresetSelectorProps {
  /** The form instance to update when preset is applied */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  form: UseFormReturn<any>;
  /** Current KB settings to detect matching preset */
  currentSettings?: KBSettings | null;
  /** Whether the form has been modified from its initial state */
  hasCustomChanges?: boolean;
  /** Whether the selector is disabled */
  disabled?: boolean;
}

// =============================================================================
// Component
// =============================================================================

/**
 * Preset Selector Component
 *
 * AC-7.16.1: Quick Preset dropdown at top of KB settings
 * AC-7.16.7: Confirmation dialog when overwriting custom settings
 * AC-7.16.8: Automatic preset detection indicator
 */
export function PresetSelector({
  form,
  currentSettings,
  hasCustomChanges = false,
  disabled = false,
}: PresetSelectorProps): React.ReactElement {
  // Track form modifications for detecting custom state (AC-7.16.8)
  const [formModified, setFormModified] = useState(false);

  // Confirmation dialog state (AC-7.16.7)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingPreset, setPendingPreset] = useState<string | null>(null);
  // Track last applied preset for display
  const [appliedPreset, setAppliedPreset] = useState<string | null>(null);

  // Detect current preset based on initial settings (AC-7.16.8)
  const initialDetectedPreset = useMemo(() => {
    if (currentSettings) {
      return detectPreset(currentSettings);
    }
    return 'custom';
  }, [currentSettings]);

  // Compute the display preset: applied > form modified custom > initial detected
  const detectedPreset = useMemo(() => {
    if (appliedPreset) return appliedPreset;
    if (formModified) return 'custom';
    return initialDetectedPreset;
  }, [appliedPreset, formModified, initialDetectedPreset]);

  // Update form modified state when form values change (AC-7.16.8)
  useEffect(() => {
    const subscription = form.watch(() => {
      // When any form value changes manually, mark as modified
      setFormModified(true);
      // Clear applied preset when user makes manual changes
      setAppliedPreset(null);
    });
    return () => subscription.unsubscribe();
  }, [form]);

  // Apply preset to form (AC-7.16.2-6) - defined before handlePresetChange which uses it
  const applyPreset = useCallback(
    (presetId: string) => {
      const presetSettings = getPresetSettings(presetId);
      if (!presetSettings) return;

      // Apply chunking settings
      if (presetSettings.chunking) {
        form.setValue('chunking.strategy', presetSettings.chunking.strategy, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('chunking.chunk_size', presetSettings.chunking.chunk_size, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('chunking.chunk_overlap', presetSettings.chunking.chunk_overlap, {
          shouldDirty: true,
          shouldValidate: true,
        });
      }

      // Apply retrieval settings
      if (presetSettings.retrieval) {
        form.setValue('retrieval.top_k', presetSettings.retrieval.top_k, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue(
          'retrieval.similarity_threshold',
          presetSettings.retrieval.similarity_threshold,
          { shouldDirty: true, shouldValidate: true }
        );
        form.setValue('retrieval.method', presetSettings.retrieval.method, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('retrieval.mmr_enabled', presetSettings.retrieval.mmr_enabled, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('retrieval.mmr_lambda', presetSettings.retrieval.mmr_lambda, {
          shouldDirty: true,
          shouldValidate: true,
        });
      }

      // Apply generation settings
      if (presetSettings.generation) {
        form.setValue('generation.temperature', presetSettings.generation.temperature, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('generation.top_p', presetSettings.generation.top_p, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('generation.max_tokens', presetSettings.generation.max_tokens, {
          shouldDirty: true,
          shouldValidate: true,
        });
      }

      // Apply prompts settings
      if (presetSettings.prompts) {
        form.setValue('prompts.system_prompt', presetSettings.prompts.system_prompt, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('prompts.citation_style', presetSettings.prompts.citation_style, {
          shouldDirty: true,
          shouldValidate: true,
        });
        form.setValue('prompts.uncertainty_handling', presetSettings.prompts.uncertainty_handling, {
          shouldDirty: true,
          shouldValidate: true,
        });
      }

      // Update applied preset indicator and reset form modified flag
      setAppliedPreset(presetId);
      setFormModified(false);
    },
    [form]
  );

  // Handle preset selection (AC-7.16.7)
  const handlePresetChange = useCallback(
    (presetId: string) => {
      // 'custom' is just an indicator, not selectable
      if (presetId === 'custom') return;

      // Check if there are custom changes that would be overwritten
      if (hasCustomChanges && detectedPreset === 'custom') {
        setPendingPreset(presetId);
        setShowConfirmDialog(true);
        return;
      }

      // Apply preset directly
      applyPreset(presetId);
    },
    [hasCustomChanges, detectedPreset, applyPreset]
  );

  // Handle confirmation dialog actions (AC-7.16.7)
  const handleConfirmApply = useCallback(() => {
    if (pendingPreset) {
      applyPreset(pendingPreset);
    }
    setShowConfirmDialog(false);
    setPendingPreset(null);
  }, [pendingPreset, applyPreset]);

  const handleCancelApply = useCallback(() => {
    setShowConfirmDialog(false);
    setPendingPreset(null);
  }, []);

  // Get display label for current preset
  const getCurrentPresetLabel = () => {
    const option = PRESET_OPTIONS.find((opt) => opt.value === detectedPreset);
    return option?.label ?? 'Custom';
  };

  return (
    <>
      {/* Preset Selector (AC-7.16.1) */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <Wand2 className="h-5 w-5 text-muted-foreground" />
        <div className="flex-1">
          <Label htmlFor="preset-selector" className="text-sm font-medium">
            Quick Preset
          </Label>
          <p className="text-xs text-muted-foreground">
            Apply optimized settings for common use cases
          </p>
        </div>
        <Select value={detectedPreset} onValueChange={handlePresetChange} disabled={disabled}>
          <SelectTrigger id="preset-selector" className="w-[160px]">
            <SelectValue>{getCurrentPresetLabel()}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {PRESET_OPTIONS.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                disabled={option.value === 'custom'}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Confirmation Dialog (AC-7.16.7) */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Apply Preset?</AlertDialogTitle>
            <AlertDialogDescription>
              You have custom settings that will be overwritten by this preset. Are you sure you
              want to apply the{' '}
              <strong>{PRESET_OPTIONS.find((opt) => opt.value === pendingPreset)?.label}</strong>{' '}
              preset?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelApply}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmApply}>Apply Preset</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default PresetSelector;
