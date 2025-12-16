/**
 * Preset Selector Component Tests
 * Story 7.16: KB Settings Presets
 *
 * Tests for the PresetSelector component:
 * - AC-7.16.1: Quick Preset dropdown at top of KB settings
 * - AC-7.16.7: Confirmation dialog when overwriting custom settings
 * - AC-7.16.8: Automatic preset detection indicator
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import { PresetSelector } from '../preset-selector';
import { PRESET_OPTIONS, getPresetSettings } from '@/lib/kb-presets';
import type { KBSettings } from '@/types/kb-settings';

// Helper component to wrap PresetSelector with form context
function TestWrapper({
  currentSettings,
  hasCustomChanges = false,
  disabled = false,
}: {
  currentSettings?: KBSettings | null;
  hasCustomChanges?: boolean;
  disabled?: boolean;
}) {
  const form = useForm({
    defaultValues: {
      chunking: {
        strategy: 'recursive',
        chunk_size: 500,
        chunk_overlap: 50,
      },
      retrieval: {
        top_k: 10,
        similarity_threshold: 0.7,
        method: 'vector',
        mmr_enabled: false,
        mmr_lambda: 0.5,
      },
      generation: {
        temperature: 0.7,
        top_p: 0.9,
        max_tokens: 4096,
      },
      prompts: {
        system_prompt: 'Test prompt',
        citation_style: 'inline',
        uncertainty_handling: 'acknowledge',
        response_language: '',
      },
    },
  });

  return (
    <FormProvider {...form}>
      <PresetSelector
        form={form}
        currentSettings={currentSettings}
        hasCustomChanges={hasCustomChanges}
        disabled={disabled}
      />
    </FormProvider>
  );
}

describe('PresetSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering (AC-7.16.1)', () => {
    it('[P0] renders preset dropdown with label', () => {
      render(<TestWrapper />);

      expect(screen.getByText('Quick Preset')).toBeInTheDocument();
      expect(screen.getByText('Apply optimized settings for common use cases')).toBeInTheDocument();
    });

    it('[P0] renders with magic wand icon', () => {
      render(<TestWrapper />);

      // The Wand2 icon should be present (lucide-react renders as SVG)
      const icon = document.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('[P0] renders select trigger with current preset label', () => {
      render(<TestWrapper />);

      // Should show "Custom" by default when no preset matches
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('[P1] renders with all preset options in dropdown', async () => {
      render(<TestWrapper />);

      // Open the dropdown
      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      // Check all preset options are visible
      for (const option of PRESET_OPTIONS) {
        expect(screen.getByRole('option', { name: option.label })).toBeInTheDocument();
      }
    });

    it('[P1] disables Custom option in dropdown', async () => {
      render(<TestWrapper />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const customOption = screen.getByRole('option', { name: 'Custom' });
      // shadcn/ui SelectItem sets data-disabled attribute (empty string is truthy for disabled)
      expect(customOption).toHaveAttribute('data-disabled');
    });
  });

  describe('Preset Selection without Custom Changes (AC-7.16.7)', () => {
    it('[P0] applies preset directly when no custom changes', async () => {
      render(<TestWrapper hasCustomChanges={false} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const legalOption = screen.getByRole('option', { name: 'Legal' });
      await userEvent.click(legalOption);

      // No confirmation dialog should appear
      expect(screen.queryByText('Apply Preset?')).not.toBeInTheDocument();
    });

    it('[P1] updates displayed preset after selection', async () => {
      render(<TestWrapper hasCustomChanges={false} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const technicalOption = screen.getByRole('option', { name: 'Technical' });
      await userEvent.click(technicalOption);

      // After applying, the trigger should show the new preset
      await waitFor(() => {
        expect(trigger).toHaveTextContent('Technical');
      });
    });
  });

  describe('Confirmation Dialog (AC-7.16.7)', () => {
    it('[P0] shows confirmation dialog when hasCustomChanges is true', async () => {
      render(<TestWrapper hasCustomChanges={true} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const creativeOption = screen.getByRole('option', { name: 'Creative' });
      await userEvent.click(creativeOption);

      // Confirmation dialog should appear
      expect(screen.getByText('Apply Preset?')).toBeInTheDocument();
      expect(
        screen.getByText(/You have custom settings that will be overwritten/)
      ).toBeInTheDocument();
    });

    it('[P0] shows preset name in confirmation dialog', async () => {
      render(<TestWrapper hasCustomChanges={true} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const codeOption = screen.getByRole('option', { name: 'Code' });
      await userEvent.click(codeOption);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      expect(screen.getByText('Code')).toBeInTheDocument();
    });

    it('[P0] applies preset when confirm button clicked', async () => {
      render(<TestWrapper hasCustomChanges={true} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const legalOption = screen.getByRole('option', { name: 'Legal' });
      await userEvent.click(legalOption);

      // Click Apply Preset button in dialog
      const applyButton = screen.getByRole('button', { name: 'Apply Preset' });
      await userEvent.click(applyButton);

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByText('Apply Preset?')).not.toBeInTheDocument();
      });
    });

    it('[P0] cancels preset application when cancel clicked', async () => {
      render(<TestWrapper hasCustomChanges={true} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const technicalOption = screen.getByRole('option', { name: 'Technical' });
      await userEvent.click(technicalOption);

      // Click Cancel button
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      await userEvent.click(cancelButton);

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByText('Apply Preset?')).not.toBeInTheDocument();
      });

      // Preset should not have changed (still Custom)
      expect(trigger).toHaveTextContent('Custom');
    });
  });

  describe('Preset Detection (AC-7.16.8)', () => {
    it('[P0] detects legal preset from currentSettings', () => {
      const legalSettings = getPresetSettings('legal') as KBSettings | null;
      render(<TestWrapper currentSettings={legalSettings} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveTextContent('Legal');
    });

    it('[P0] detects technical preset from currentSettings', () => {
      const technicalSettings = getPresetSettings('technical') as KBSettings | null;
      render(<TestWrapper currentSettings={technicalSettings} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveTextContent('Technical');
    });

    it('[P1] shows Custom for non-matching settings', () => {
      const customSettings = {
        chunking: {
          strategy: 'recursive',
          chunk_size: 999,
          chunk_overlap: 123,
        },
        retrieval: {
          top_k: 7,
          similarity_threshold: 0.65,
          method: 'vector',
          mmr_enabled: false,
          mmr_lambda: 0.5,
        },
        generation: {
          temperature: 0.42,
          top_p: 0.88,
          max_tokens: 2048,
        },
        prompts: {
          system_prompt: 'Custom prompt',
          citation_style: 'inline',
          uncertainty_handling: 'acknowledge',
          response_language: '',
        },
        preset: 'custom',
      } as KBSettings;

      render(<TestWrapper currentSettings={customSettings} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveTextContent('Custom');
    });

    it('[P1] shows Custom when no currentSettings provided', () => {
      render(<TestWrapper currentSettings={null} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveTextContent('Custom');
    });
  });

  describe('Disabled State', () => {
    it('[P1] disables select when disabled prop is true', () => {
      render(<TestWrapper disabled={true} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeDisabled();
    });

    it('[P1] enables select when disabled prop is false', () => {
      render(<TestWrapper disabled={false} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).not.toBeDisabled();
    });
  });

  describe('Form Integration', () => {
    it('[P0] does not apply preset when Custom is selected', async () => {
      render(<TestWrapper hasCustomChanges={false} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const customOption = screen.getByRole('option', { name: 'Custom' });
      await userEvent.click(customOption);

      // Custom is disabled and should not trigger any changes
      // The select should not close with Custom as the value
    });
  });
});
