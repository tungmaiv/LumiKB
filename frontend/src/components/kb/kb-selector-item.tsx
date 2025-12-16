'use client';

import { Eye, Pencil, Settings, Archive } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';

export type PermissionLevel = 'READ' | 'WRITE' | 'ADMIN';

interface KbSelectorItemProps {
  name: string;
  documentCount: number;
  permissionLevel: PermissionLevel;
  tags?: string[];
  isActive?: boolean;
  isArchived?: boolean;
  onClick?: () => void;
  actionSlot?: React.ReactNode;
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
  tags = [],
  isActive = false,
  isArchived = false,
  onClick,
  actionSlot,
}: KbSelectorItemProps): React.ReactElement {
  const config = permissionConfig[permissionLevel];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'group flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        isActive && 'bg-accent text-accent-foreground',
        isArchived && 'opacity-60'
      )}
    >
      <button
        onClick={onClick}
        className="flex flex-1 items-center gap-3 min-w-0"
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
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="truncate font-medium" title={name}>
              {name}
            </span>
            {isArchived && (
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 shrink-0">
                <Archive className="h-2.5 w-2.5 mr-0.5" />
                Archived
              </Badge>
            )}
          </div>
          {tags.length > 0 && !isArchived && (
            <div className="flex gap-1 mt-0.5 overflow-hidden">
              {tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="inline-block truncate max-w-[60px] rounded bg-muted/80 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                  title={tag}
                >
                  {tag}
                </span>
              ))}
              {tags.length > 2 && (
                <span className="text-[10px] text-muted-foreground">+{tags.length - 2}</span>
              )}
            </div>
          )}
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
      {actionSlot && (
        <div className="shrink-0 opacity-50 group-hover:opacity-100 transition-opacity">
          {actionSlot}
        </div>
      )}
    </div>
  );
}
