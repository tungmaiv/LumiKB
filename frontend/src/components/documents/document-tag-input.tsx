'use client';

import { useState, KeyboardEvent } from 'react';
import { X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

/** Maximum number of tags allowed per document */
export const MAX_TAGS_PER_DOCUMENT = 10;
/** Maximum length of each tag */
export const MAX_TAG_LENGTH = 50;

interface DocumentTagInputProps {
  /** Current tags */
  tags: string[];
  /** Callback when tags change */
  onTagsChange: (tags: string[]) => void;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes for the container */
  className?: string;
  /** ID for the input element */
  id?: string;
}

/**
 * Normalize a tag by trimming whitespace, converting to lowercase,
 * and truncating to max length.
 */
function normalizeTag(tag: string): string {
  return tag.trim().toLowerCase().slice(0, MAX_TAG_LENGTH);
}

/**
 * DocumentTagInput provides a tag input field with chips display.
 *
 * Features:
 * - Enter/comma to add tags
 * - Backspace to remove last tag when input is empty
 * - Automatic normalization (lowercase, trim, truncate)
 * - Duplicate prevention
 * - Max 10 tags limit
 * - Tag chips with remove button
 *
 * @example
 * <DocumentTagInput
 *   tags={tags}
 *   onTagsChange={setTags}
 *   placeholder="Add tags..."
 * />
 */
export function DocumentTagInput({
  tags,
  onTagsChange,
  disabled = false,
  placeholder = 'Type a tag and press Enter',
  className,
  id = 'tag-input',
}: DocumentTagInputProps): React.ReactElement {
  const [inputValue, setInputValue] = useState('');

  const addTag = (tag: string) => {
    const normalizedTag = normalizeTag(tag);
    if (
      normalizedTag &&
      !tags.includes(normalizedTag) &&
      tags.length < MAX_TAGS_PER_DOCUMENT
    ) {
      onTagsChange([...tags, normalizedTag]);
    }
    setInputValue('');
  };

  const removeTag = (tagToRemove: string) => {
    onTagsChange(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      removeTag(tags[tags.length - 1]);
    }
  };

  const handleBlur = () => {
    if (inputValue) {
      addTag(inputValue);
    }
  };

  const isMaxTags = tags.length >= MAX_TAGS_PER_DOCUMENT;

  return (
    <div className={cn('space-y-2', className)}>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="rounded-full p-0.5 hover:bg-primary/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label={`Remove ${tag} tag`}
                disabled={disabled}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}
      <Input
        id={id}
        placeholder={isMaxTags ? 'Maximum tags reached' : placeholder}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        disabled={disabled || isMaxTags}
        aria-label="Add tags"
      />
      <p className="text-xs text-muted-foreground">
        Press Enter or comma to add a tag. Maximum {MAX_TAGS_PER_DOCUMENT} tags, {MAX_TAG_LENGTH} characters each.
      </p>
    </div>
  );
}

/**
 * DocumentTagsDisplay shows a read-only list of tags as chips.
 */
export function DocumentTagsDisplay({
  tags,
  className,
  maxVisible = 5,
}: {
  tags: string[];
  className?: string;
  maxVisible?: number;
}): React.ReactElement | null {
  if (!tags || tags.length === 0) {
    return null;
  }

  const visibleTags = tags.slice(0, maxVisible);
  const remainingCount = tags.length - maxVisible;

  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {visibleTags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground"
        >
          {tag}
        </span>
      ))}
      {remainingCount > 0 && (
        <span className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
          +{remainingCount} more
        </span>
      )}
    </div>
  );
}
