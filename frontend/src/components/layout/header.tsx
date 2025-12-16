'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SearchBar } from '@/components/search/search-bar';
import { UserMenu } from '@/components/layout/user-menu';
import { MainNav } from '@/components/layout/main-nav';
import { CommandPalette } from '@/components/search/command-palette';

interface HeaderProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

/**
 * Header - Application header with search and global keyboard shortcut (Story 3.7, AC1, AC6)
 */
export function Header({ onMenuClick, showMenuButton = false }: HeaderProps): React.ReactElement {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global keyboard shortcut ⌘K/Ctrl+K (AC1 - Story 3.7)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true); // AC1
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-50 flex h-20 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
          <Link href="/dashboard" className="flex items-center gap-2">
            <Image
              src="/logo.png"
              alt="LumiKB"
              width={1260}
              height={140}
              className="h-[70px] w-auto"
              priority
            />
          </Link>
        </div>

        <div className="hidden flex-1 justify-center px-4 md:flex">
          <SearchBar
            placeholder="Search knowledge bases... (Press ⌘K)"
            onClick={() => setCommandPaletteOpen(true)} // AC6: clicking opens palette
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Main Navigation - hidden on mobile */}
          <div className="hidden md:flex">
            <MainNav />
          </div>
          <UserMenu />
        </div>
      </header>

      {/* CommandPalette (AC1-AC7 - Story 3.7) */}
      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
    </>
  );
}
