'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

interface SearchBarProps {
  /**
   * Whether the search bar is disabled
   */
  disabled?: boolean;
  /**
   * Placeholder text
   */
  placeholder?: string;
  /**
   * Callback when the search bar is clicked (AC6 - Story 3.7)
   */
  onClick?: () => void;
}

/**
 * SearchBar - Always-visible search trigger in header (Story 3.7, AC6)
 * Clicking opens the command palette (⌘K shortcut)
 */
export function SearchBar({
  disabled = false,
  placeholder = 'Search...',
  onClick,
}: SearchBarProps): React.ReactElement {
  return (
    <div
      className="relative w-full max-w-md cursor-pointer"
      onClick={disabled ? undefined : onClick} // AC6: clicking opens palette
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick?.();
        }
      }}
      title="Press ⌘K or Ctrl+K to search"
    >
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="search"
        placeholder={placeholder}
        disabled={disabled}
        className="w-full pl-9 pr-12 cursor-pointer"
        readOnly // Prevent direct typing - opens palette instead
      />
      <kbd className="pointer-events-none absolute right-3 top-1/2 hidden h-5 -translate-y-1/2 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
        <span className="text-xs">⌘</span>K
      </kbd>
    </div>
  );
}
