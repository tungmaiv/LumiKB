/**
 * AdditionalPromptInput Component - Epic 4, Story 4.4
 * Optional context textarea for refining generation prompts
 */

import { Textarea } from '@/components/ui/textarea';
import { Info } from 'lucide-react';

export interface AdditionalPromptInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Textarea for adding additional context to document generation
 * Supports multi-line input with character count
 */
export function AdditionalPromptInput({
  value,
  onChange,
  disabled = false,
  placeholder = 'Add specific instructions or context for the generation (optional)',
}: AdditionalPromptInputProps) {
  const charCount = value.length;
  const maxChars = 500;
  const isNearLimit = charCount > maxChars * 0.8;

  return (
    <div className="flex flex-col gap-2" data-testid="additional-prompt-input">
      <label htmlFor="additional-prompt" className="text-sm font-medium">
        Additional Context
        <span className="text-muted-foreground font-normal ml-2">(Optional)</span>
      </label>

      <div className="relative">
        <Textarea
          id="additional-prompt"
          data-testid="additional-prompt-textarea"
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= maxChars) {
              onChange(e.target.value);
            }
          }}
          disabled={disabled}
          placeholder={placeholder}
          rows={3}
          className="resize-none pr-16"
        />

        {/* Character Counter */}
        <div
          className="absolute bottom-2 right-2 text-xs text-muted-foreground"
          data-testid="char-count"
        >
          <span className={isNearLimit ? 'text-amber-600 font-medium' : ''}>{charCount}</span>/
          {maxChars}
        </div>
      </div>

      {/* Help Text */}
      <div className="flex items-start gap-2 text-xs text-muted-foreground">
        <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
        <p>
          Provide specific requirements, tone, or sections to focus on. This will refine the
          generated content.
        </p>
      </div>
    </div>
  );
}
