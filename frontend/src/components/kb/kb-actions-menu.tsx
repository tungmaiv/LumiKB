'use client';

import { useState } from 'react';
import { MoreVertical, Archive, Trash2, ArchiveRestore, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ArchiveKBDialog } from './dialogs/archive-kb-dialog';
import { DeleteKBDialog } from './dialogs/delete-kb-dialog';
import { RestoreKBDialog } from './dialogs/restore-kb-dialog';
import { useKBActions } from '@/hooks/useKBActions';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

interface KBActionsMenuProps {
  kb: KnowledgeBase;
  onSettingsClick?: () => void;
}

/**
 * Actions menu for Knowledge Base lifecycle management.
 * Story 7-26: AC-7.26.1 - KB actions menu with archive/delete/restore options.
 */
export function KBActionsMenu({ kb, onSettingsClick }: KBActionsMenuProps) {
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);

  const { archive, restore, remove, isArchiving, isRestoring, isDeleting } = useKBActions();

  const isArchived = kb.archived_at !== null;
  const hasDocuments = kb.document_count > 0;
  const isAdmin = kb.permission_level === 'ADMIN';

  const handleArchiveConfirm = async () => {
    const success = await archive(kb.id, kb.name);
    if (success) {
      setArchiveDialogOpen(false);
    }
  };

  const handleDeleteConfirm = async () => {
    const success = await remove(kb.id, kb.name);
    if (success) {
      setDeleteDialogOpen(false);
    }
  };

  const handleRestoreConfirm = async () => {
    const success = await restore(kb.id, kb.name);
    if (success) {
      setRestoreDialogOpen(false);
    }
  };

  // Only show menu for admins
  if (!isAdmin) {
    return null;
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            aria-label="KB actions"
            data-testid="kb-actions-menu-trigger"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {/* Settings option */}
          {onSettingsClick && (
            <>
              <DropdownMenuItem onClick={onSettingsClick} data-testid="kb-settings-option">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
            </>
          )}

          {/* Active KB options */}
          {!isArchived && (
            <>
              <DropdownMenuItem
                onClick={() => setArchiveDialogOpen(true)}
                data-testid="kb-archive-option"
              >
                <Archive className="mr-2 h-4 w-4" />
                Archive KB
              </DropdownMenuItem>

              {/* Delete option with tooltip for disabled state */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div>
                    <DropdownMenuItem
                      onClick={() => !hasDocuments && setDeleteDialogOpen(true)}
                      disabled={hasDocuments}
                      className={hasDocuments ? 'opacity-50 cursor-not-allowed' : ''}
                      data-testid="kb-delete-option"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete KB
                    </DropdownMenuItem>
                  </div>
                </TooltipTrigger>
                {hasDocuments && (
                  <TooltipContent side="left">
                    <p>Remove all documents before deleting</p>
                  </TooltipContent>
                )}
              </Tooltip>
            </>
          )}

          {/* Archived KB options */}
          {isArchived && (
            <DropdownMenuItem
              onClick={() => setRestoreDialogOpen(true)}
              data-testid="kb-restore-option"
            >
              <ArchiveRestore className="mr-2 h-4 w-4" />
              Restore KB
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Dialogs */}
      <ArchiveKBDialog
        kb={kb}
        open={archiveDialogOpen}
        onOpenChange={setArchiveDialogOpen}
        onConfirm={handleArchiveConfirm}
        isLoading={isArchiving}
      />

      <DeleteKBDialog
        kb={kb}
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDeleteConfirm}
        isLoading={isDeleting}
      />

      <RestoreKBDialog
        kb={kb}
        open={restoreDialogOpen}
        onOpenChange={setRestoreDialogOpen}
        onConfirm={handleRestoreConfirm}
        isLoading={isRestoring}
      />
    </>
  );
}
