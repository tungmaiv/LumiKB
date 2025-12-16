'use client';

import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import {
  archiveKnowledgeBase,
  restoreKnowledgeBase,
  deleteKnowledgeBase,
} from '@/lib/api/knowledge-bases';
import { useKBStore } from '@/lib/stores/kb-store';
import { ApiError } from '@/lib/api/client';

/**
 * Hook for KB lifecycle actions (archive, restore, delete).
 * Story 7-26: Provides mutation functions with success/error handling.
 */
export function useKBActions() {
  const [isArchiving, setIsArchiving] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const { fetchKbs, activeKb, setActiveKb } = useKBStore();

  const archive = useCallback(
    async (kbId: string, kbName: string) => {
      setIsArchiving(true);
      try {
        await archiveKnowledgeBase(kbId);
        toast.success(`"${kbName}" has been archived`);
        // Clear active KB if it was archived
        if (activeKb?.id === kbId) {
          setActiveKb(null);
        }
        // Refresh KB list
        await fetchKbs();
        return true;
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.detail || 'Failed to archive knowledge base'
            : error instanceof Error
              ? error.message
              : 'Failed to archive knowledge base';
        toast.error(message);
        return false;
      } finally {
        setIsArchiving(false);
      }
    },
    [activeKb?.id, fetchKbs, setActiveKb]
  );

  const restore = useCallback(
    async (kbId: string, kbName: string) => {
      setIsRestoring(true);
      try {
        await restoreKnowledgeBase(kbId);
        toast.success(`"${kbName}" has been restored`);
        // Refresh KB list
        await fetchKbs();
        return true;
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.detail || 'Failed to restore knowledge base'
            : error instanceof Error
              ? error.message
              : 'Failed to restore knowledge base';
        toast.error(message);
        return false;
      } finally {
        setIsRestoring(false);
      }
    },
    [fetchKbs]
  );

  const remove = useCallback(
    async (kbId: string, kbName: string) => {
      setIsDeleting(true);
      try {
        await deleteKnowledgeBase(kbId);
        toast.success(`"${kbName}" has been permanently deleted`);
        // Clear active KB if it was deleted
        if (activeKb?.id === kbId) {
          setActiveKb(null);
        }
        // Refresh KB list
        await fetchKbs();
        return true;
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.detail || 'Failed to delete knowledge base'
            : error instanceof Error
              ? error.message
              : 'Failed to delete knowledge base';
        toast.error(message);
        return false;
      } finally {
        setIsDeleting(false);
      }
    },
    [activeKb?.id, fetchKbs, setActiveKb]
  );

  return {
    archive,
    restore,
    remove,
    isArchiving,
    isRestoring,
    isDeleting,
    isPending: isArchiving || isRestoring || isDeleting,
  };
}
