'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface SearchBarProps {
  disabled?: boolean;
  placeholder?: string;
}

export function SearchBar({
  disabled = true,
  placeholder = 'Search coming soon...',
}: SearchBarProps): React.ReactElement {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder={placeholder}
              disabled={disabled}
              className="w-full pl-9 pr-12"
            />
            <kbd className="pointer-events-none absolute right-3 top-1/2 hidden h-5 -translate-y-1/2 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
              <span className="text-xs">&#8984;</span>K
            </kbd>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Search coming soon in Epic 3</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
