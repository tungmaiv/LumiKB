'use client';

import { Eye, Pencil, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

export type PermissionLevel = 'READ' | 'WRITE' | 'ADMIN';

interface KbSelectorItemProps {
  name: string;
  documentCount: number;
  permissionLevel: PermissionLevel;
  isActive?: boolean;
  onClick?: () => void;
}

const permissionConfig = {
  READ: {
    icon: Eye,
    tooltip: 'Read access',
    colorClass: 'text-muted-foreground',
  },
  WRITE: {
    icon: Pencil,
    tooltip: 'Write access',
    colorClass: 'text-blue-500',
  },
  ADMIN: {
    icon: Settings,
    tooltip: 'Admin access',
    colorClass: 'text-amber-500',
  },
};

export function KbSelectorItem({
  name,
  documentCount,
  permissionLevel,
  isActive = false,
  onClick,
}: KbSelectorItemProps): React.ReactElement {
  const config = permissionConfig[permissionLevel];
  const Icon = config.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        isActive && 'bg-accent text-accent-foreground'
      )}
      aria-current={isActive ? 'true' : undefined}
    >
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="shrink-0">
            <Icon className={cn('h-4 w-4', config.colorClass)} aria-label={config.tooltip} />
          </span>
        </TooltipTrigger>
        <TooltipContent side="right">
          <p>{config.tooltip}</p>
        </TooltipContent>
      </Tooltip>
      <div className="flex-1 truncate">
        <span className="font-medium" title={name}>
          {name}
        </span>
      </div>
      <span
        className={cn(
          'shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs',
          documentCount === 0 ? 'text-muted-foreground/60' : 'text-muted-foreground'
        )}
      >
        {documentCount} {documentCount === 1 ? 'doc' : 'docs'}
      </span>
    </button>
  );
}
