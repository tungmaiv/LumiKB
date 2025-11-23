'use client';

import { Eye, Pencil, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KbSelectorItemProps {
  name: string;
  documentCount: number;
  permission: 'viewer' | 'editor' | 'admin';
  isActive?: boolean;
  onClick?: () => void;
}

const permissionIcons = {
  viewer: Eye,
  editor: Pencil,
  admin: Settings,
};

export function KbSelectorItem({
  name,
  documentCount,
  permission,
  isActive = false,
  onClick,
}: KbSelectorItemProps): React.ReactElement {
  const Icon = permissionIcons[permission];

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        isActive && 'bg-accent text-accent-foreground'
      )}
    >
      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="flex-1 truncate">
        <span className="font-medium">{name}</span>
      </div>
      <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
        {documentCount}
      </span>
    </button>
  );
}
