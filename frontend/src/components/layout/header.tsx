'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SearchBar } from '@/components/search/search-bar';
import { UserMenu } from '@/components/layout/user-menu';

interface HeaderProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

export function Header({ onMenuClick, showMenuButton = false }: HeaderProps): React.ReactElement {
  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-3">
        {showMenuButton && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="shrink-0"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <h1 className="text-xl font-bold text-primary">LumiKB</h1>
      </div>

      <div className="hidden flex-1 justify-center px-4 md:flex">
        <SearchBar disabled placeholder="Search knowledge bases..." />
      </div>

      <div className="flex items-center gap-2">
        <UserMenu />
      </div>
    </header>
  );
}
