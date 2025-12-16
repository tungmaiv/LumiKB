'use client';

import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { DocumentTagInput } from './document-tag-input';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DocumentEditTagsModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Callback when open state changes */
  onOpenChange: (open: boolean) => void;
  /** Knowledge base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
  /** Document name for display */
  documentName: string;
  /** Current tags on the document */
  currentTags: string[];
  /** Callback when tags are successfully updated */
  onTagsUpdated?: (newTags: string[]) => void;
}

/**
 * DocumentEditTagsModal provides a modal dialog for editing document tags.
 *
 * Features:
 * - Tag input with chips display
 * - Save/Cancel actions
 * - Change detection (only enables save when tags have changed)
 * - Error handling with display
 * - Loading state during save
 *
 * @example
 * <DocumentEditTagsModal
 *   open={showTagsModal}
 *   onOpenChange={setShowTagsModal}
 *   kbId={kbId}
 *   documentId={doc.id}
 *   documentName={doc.name}
 *   currentTags={doc.tags || []}
 *   onTagsUpdated={(tags) => handleTagsUpdate(doc.id, tags)}
 * />
 */
export function DocumentEditTagsModal({
  open,
  onOpenChange,
  kbId,
  documentId,
  documentName,
  currentTags,
  onTagsUpdated,
}: DocumentEditTagsModalProps): React.ReactElement {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [tags, setTags] = useState<string[]>(currentTags);

  // Reset tags when modal opens with new current tags
  useEffect(() => {
    if (open) {
      setTags(currentTags);
      setSubmitError(null);
    }
  }, [open, currentTags]);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/tags`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ tags }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          errorData.detail?.message ||
          errorData.detail ||
          `Failed to update tags (${response.status})`;
        throw new Error(errorMessage);
      }

      const result = await response.json();
      onTagsUpdated?.(result.tags || []);
      onOpenChange(false);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to update tags';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      // Reset to current tags when closing without saving
      setTags(currentTags);
      setSubmitError(null);
    }
    onOpenChange(newOpen);
  };

  // Check if tags have changed
  const hasChanges =
    tags.length !== currentTags.length ||
    tags.some((tag) => !currentTags.includes(tag)) ||
    currentTags.some((tag) => !tags.includes(tag));

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Document Tags</DialogTitle>
          <DialogDescription>
            Manage tags for &quot;{documentName}&quot;. Tags help organize and filter
            documents.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="doc-tags-input">Tags</Label>
            <DocumentTagInput
              id="doc-tags-input"
              tags={tags}
              onTagsChange={setTags}
              disabled={isSubmitting}
            />
          </div>

          {submitError && (
            <p className="text-sm text-destructive">{submitError}</p>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !hasChanges}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
