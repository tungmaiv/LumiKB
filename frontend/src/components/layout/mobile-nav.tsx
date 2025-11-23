'use client';

import { Database, FileText, Home, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MobileNavProps {
  onSidebarOpen?: () => void;
  onCitationsOpen?: () => void;
}

export function MobileNav({ onSidebarOpen, onCitationsOpen }: MobileNavProps): React.ReactElement {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t bg-background px-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={onSidebarOpen}
        className={cn('flex flex-col gap-1 h-auto py-2')}
      >
        <Database className="h-5 w-5" />
        <span className="text-[10px]">KBs</span>
      </Button>

      <Button variant="ghost" size="sm" className={cn('flex flex-col gap-1 h-auto py-2')} disabled>
        <Search className="h-5 w-5" />
        <span className="text-[10px]">Search</span>
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className={cn('flex flex-col gap-1 h-auto py-2 text-primary')}
      >
        <Home className="h-5 w-5" />
        <span className="text-[10px]">Home</span>
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={onCitationsOpen}
        className={cn('flex flex-col gap-1 h-auto py-2')}
      >
        <FileText className="h-5 w-5" />
        <span className="text-[10px]">Citations</span>
      </Button>
    </nav>
  );
}
