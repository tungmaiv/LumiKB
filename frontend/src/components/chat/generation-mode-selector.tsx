/**
 * GenerationModeSelector Component - Epic 4, Story 4.4
 * Dropdown selector for document generation modes with predefined and custom options
 */

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText } from 'lucide-react';

export type GenerationMode =
  | 'rfp_response'
  | 'technical_checklist'
  | 'requirements_summary'
  | 'custom';

export interface GenerationModeOption {
  value: GenerationMode;
  label: string;
  description: string;
}

export const GENERATION_MODES: GenerationModeOption[] = [
  {
    value: 'rfp_response',
    label: 'RFP Response Section',
    description: 'Generate a professional RFP response using relevant sources',
  },
  {
    value: 'technical_checklist',
    label: 'Technical Checklist',
    description: 'Create a structured checklist from technical requirements',
  },
  {
    value: 'requirements_summary',
    label: 'Requirements Summary',
    description: 'Summarize requirements and key points with citations',
  },
  {
    value: 'custom',
    label: 'Custom Prompt',
    description: 'Use a custom generation prompt',
  },
];

export interface GenerationModeSelectorProps {
  value: GenerationMode;
  onChange: (mode: GenerationMode) => void;
  disabled?: boolean;
}

/**
 * Dropdown selector for choosing document generation mode
 * Uses shadcn Select with FileText icon
 */
export function GenerationModeSelector({
  value,
  onChange,
  disabled = false,
}: GenerationModeSelectorProps) {
  const selectedMode = GENERATION_MODES.find((m) => m.value === value);

  return (
    <div className="flex flex-col gap-2" data-testid="generation-mode-selector">
      <label htmlFor="generation-mode" className="text-sm font-medium">
        Generation Mode
      </label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          id="generation-mode"
          className="w-full"
          data-testid="generation-mode-trigger"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <SelectValue placeholder="Select generation mode">{selectedMode?.label}</SelectValue>
          </div>
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Document Types</SelectLabel>
            {GENERATION_MODES.map((mode) => (
              <SelectItem
                key={mode.value}
                value={mode.value}
                data-testid={`generation-mode-${mode.value}`}
              >
                <div className="flex flex-col">
                  <span className="font-medium">{mode.label}</span>
                  <span className="text-xs text-muted-foreground">{mode.description}</span>
                </div>
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  );
}
