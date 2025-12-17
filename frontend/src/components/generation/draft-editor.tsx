/**
 * DraftEditor Component - Epic 4, Story 4.6, AC1-AC4
 * Rich text editor for drafts with citation preservation
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Save,
  X,
  Loader2,
  CheckCircle2,
  Undo2,
  Redo2,
  FileDown,
  MessageSquare,
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useDraftEditor } from '@/hooks/useDraftEditor';
import { useDraftUndo } from '@/hooks/useDraftUndo';
import { useExport, type ExportFormat } from '@/hooks/useExport';
import { useFeedback } from '@/hooks/useFeedback';
import { useCitationValidation, renumberCitations } from '@/hooks/useCitationValidation';
import { ExportModal } from '@/components/generation/export-modal';
import { FeedbackModal, type FeedbackType } from '@/components/generation/feedback-modal';
import { RecoveryModal } from '@/components/generation/recovery-modal';
import { VerificationDialog } from '@/components/generation/verification-dialog';
import { CitationWarningBanner } from '@/components/generation/citation-warning-banner';
import type { Draft } from '@/lib/api/drafts';

interface DraftEditorProps {
  /** Draft data */
  draft: Draft;
  /** Callback to close editor */
  onClose: () => void;
  /** Callback when save succeeds */
  onSaveSuccess?: () => void;
  /** Callback when save fails */
  onSaveError?: (error: Error) => void;
  /** Whether the draft is currently streaming (AC-7.20.5) */
  isStreaming?: boolean;
  /** Callback when a recovery action is selected (AC-7.20.5) */
  onRecoveryAction?: (action: string) => void;
}

/**
 * Renders a rich text editor for editing generated drafts.
 *
 * Features (AC1-AC4):
 * - contentEditable for markdown editing
 * - Citation markers as non-editable React components (AC2)
 * - Auto-save every 5s (AC4)
 * - Manual save with Ctrl+S (AC4)
 * - Word count display
 * - Save status indicator
 *
 * @example
 * <DraftEditor
 *   draft={draftData}
 *   onClose={handleClose}
 *   onSaveSuccess={() => toast('Saved!')}
 * />
 */
export function DraftEditor({
  draft,
  onClose,
  onSaveSuccess,
  onSaveError,
  isStreaming = false,
  onRecoveryAction,
}: DraftEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showVerificationDialog, setShowVerificationDialog] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat | null>(null);

  // Feedback modal state (Story 7-20, AC-7.20.1)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);

  const { content, setContent, citations, setCitations, isSaving, lastSaved, saveNow, isDirty } =
    useDraftEditor({
      draftId: draft.id,
      initialContent: draft.content,
      initialCitations: draft.citations,
      autoSaveInterval: 5000, // AC4: 5s auto-save
      onSaveSuccess,
      onSaveError,
    });

  const { handleExport, isExporting } = useExport({
    draftId: draft.id,
    onSuccess: () => {
      setShowVerificationDialog(false);
      setShowExportModal(false);
      setSelectedFormat(null);
    },
    onError: (error) => {
      console.error('Export failed:', error);
    },
  });

  // Feedback hook (Story 7-20, AC-7.20.3)
  const {
    handleSubmit: submitFeedback,
    isSubmitting: isSubmittingFeedback,
    alternatives,
    resetAlternatives,
  } = useFeedback(draft.id);

  // Undo/redo management (AC5)
  const { snapshot, canUndo, canRedo, undo, redo, recordSnapshot } = useDraftUndo(
    draft.content,
    draft.citations
  );

  // Citation validation (Story 7-21, AC-7.21.1 - AC-7.21.5)
  const { warnings, hasWarnings, dismissWarning } = useCitationValidation(content, citations, {
    debounceMs: 500,
  });

  // Handle auto-fix for unused citations (Story 7-21, AC-7.21.5)
  const handleAutoFixCitations = useCallback(
    (numbersToRemove: number[]) => {
      const result = renumberCitations(content, citations, numbersToRemove);
      setContent(result.content);
      setCitations(result.citations);
    },
    [content, citations, setContent, setCitations]
  );

  // Track previous values for snapshot recording
  const prevContentRef = useRef(content);
  const prevCitationsRef = useRef(citations);

  // Sync undo snapshot with current state when user makes edits
  // Use deep equality check for citations to avoid excessive snapshots
  useEffect(() => {
    const contentChanged = content !== prevContentRef.current;
    const citationsChanged = JSON.stringify(citations) !== JSON.stringify(prevCitationsRef.current);

    if (contentChanged || citationsChanged) {
      recordSnapshot(content, citations);
      prevContentRef.current = content;
      prevCitationsRef.current = citations;
    }
  }, [content, citations, recordSnapshot]);

  // Keyboard shortcuts (AC4: Ctrl+S, AC5: Ctrl+Z/Y)
  // Use refs to avoid recreating handler on every snapshot change
  const snapshotRef = useRef(snapshot);

  // Update ref in effect to avoid render-time side effects
  useEffect(() => {
    snapshotRef.current = snapshot;
  }, [snapshot]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S: Save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        void saveNow();
      }
      // Ctrl+Z: Undo
      else if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo) {
          undo();
          // Apply undo snapshot to editor (use ref to avoid stale closure)
          const currentSnapshot = snapshotRef.current;
          setContent(currentSnapshot.content);
          setCitations(currentSnapshot.citations);
        }
      }
      // Ctrl+Shift+Z or Ctrl+Y: Redo
      else if (
        ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) ||
        ((e.ctrlKey || e.metaKey) && e.key === 'y')
      ) {
        e.preventDefault();
        if (canRedo) {
          redo();
          // Apply redo snapshot to editor (use ref to avoid stale closure)
          const currentSnapshot = snapshotRef.current;
          setContent(currentSnapshot.content);
          setCitations(currentSnapshot.citations);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [saveNow, canUndo, canRedo, undo, redo, setContent, setCitations]);

  // Convert content with [n] markers to HTML with styled spans
  const renderContentAsHTML = useCallback(() => {
    if (!content) return '';

    // Replace [n] markers with styled HTML spans
    // This preserves markers during contentEditable changes
    const htmlWithMarkers = content.replace(/\[(\d+)\]/g, (match, num) => {
      const citationNum = parseInt(num, 10);
      const citation = citations.find((c) => c.number === citationNum);
      const exists = citation !== undefined;

      // Return styled span that looks like CitationMarker but is just HTML
      return `<span
        class="citation-marker ${exists ? 'citation-exists' : 'citation-missing'}"
        data-citation-number="${citationNum}"
        contenteditable="false"
        style="display: inline-flex; align-items: center; gap: 0.125rem; padding: 0.25rem; margin: 0 0.125rem; font-size: 0.75rem; font-weight: 500; border-radius: 0.25rem; cursor: pointer; user-select: none; background-color: ${exists ? 'rgb(219 234 254)' : 'rgb(254 226 226)'}; color: ${exists ? 'rgb(29 78 216)' : 'rgb(153 27 27)'};"
      >${match}</span>`;
    });

    // Sanitize HTML to prevent XSS attacks
    return DOMPurify.sanitize(htmlWithMarkers, {
      ALLOWED_TAGS: [
        'span',
        'br',
        'p',
        'div',
        'strong',
        'em',
        'u',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'ul',
        'ol',
        'li',
      ],
      ALLOWED_ATTR: ['class', 'data-citation-number', 'contenteditable', 'style'],
      KEEP_CONTENT: true,
    });
  }, [content, citations]);

  // Export flow handlers
  const handleExportClick = () => {
    setShowExportModal(true);
  };

  const handleFormatSelected = (format: ExportFormat) => {
    setSelectedFormat(format);
    setShowExportModal(false);
    setShowVerificationDialog(true);
  };

  const handleExportConfirm = async () => {
    if (selectedFormat) {
      await handleExport(selectedFormat);
    }
  };

  // Feedback flow handlers (Story 7-20, AC-7.20.2 - AC-7.20.5)
  const handleFeedbackClick = () => {
    setShowFeedbackModal(true);
  };

  const handleFeedbackSubmit = async (feedbackType: FeedbackType, comments?: string) => {
    const success = await submitFeedback(feedbackType, comments);
    if (success) {
      setShowFeedbackModal(false);
      // Show recovery modal if alternatives are available (AC-7.20.4)
      // The alternatives will be populated by useFeedback hook after submission
      setShowRecoveryModal(true);
    }
  };

  const handleRecoveryClose = () => {
    setShowRecoveryModal(false);
    resetAlternatives();
  };

  const handleRecoveryAction = (action: string) => {
    setShowRecoveryModal(false);
    resetAlternatives();
    // Trigger parent's recovery action handler (AC-7.20.5)
    onRecoveryAction?.(action);
  };

  // Handle content edits from contentEditable
  const handleContentChange = useCallback(() => {
    if (!editorRef.current) return;

    // Extract content from innerHTML to preserve citation markers
    const innerHTML = editorRef.current.innerHTML;

    // Parse HTML to extract text with [n] markers preserved
    const parser = new DOMParser();
    const doc = parser.parseFromString(innerHTML, 'text/html');

    // Walk through nodes and reconstruct text with markers
    const extractText = (node: Node): string => {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.textContent || '';
      }

      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as HTMLElement;

        // If this is a citation marker span, extract [n] format
        if (element.classList.contains('citation-marker')) {
          const citationNum = element.getAttribute('data-citation-number');
          return `[${citationNum}]`;
        }

        // For other elements, recursively extract text from children
        let text = '';
        for (const child of Array.from(node.childNodes)) {
          text += extractText(child);
        }

        // Add newlines for block elements
        if (['DIV', 'P', 'BR'].includes(element.tagName)) {
          text += '\n';
        }

        return text;
      }

      return '';
    };

    const newContent = extractText(doc.body).trim();
    setContent(newContent);
  }, [setContent]);

  // Render save status badge
  const renderSaveStatus = () => {
    if (isSaving) {
      return (
        <Badge variant="secondary" className="flex items-center gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Saving...
        </Badge>
      );
    }

    if (lastSaved && !isDirty) {
      return (
        <Badge variant="default" className="flex items-center gap-1">
          <CheckCircle2 className="h-3 w-3" />
          Saved {new Date(lastSaved).toLocaleTimeString()}
        </Badge>
      );
    }

    if (isDirty) {
      return <Badge variant="outline">Unsaved changes</Badge>;
    }

    return null;
  };

  return (
    <div className="fixed inset-0 z-50 bg-background" data-testid="draft-editor">
      {/* Header Bar */}
      <div className="border-b p-4 flex items-center gap-4">
        <div className="flex-1">
          <h2 className="text-lg font-semibold" data-testid="draft-title">
            {draft.title}
          </h2>
          <p className="text-sm text-muted-foreground">
            {draft.word_count} words • {citations.length} citations
          </p>
        </div>

        {renderSaveStatus()}

        <div className="flex gap-2">
          {/* Undo/Redo buttons (AC5) */}
          <Button
            variant="ghost"
            size="sm"
            onClick={undo}
            disabled={!canUndo}
            title="Undo (Ctrl+Z)"
            data-testid="undo-button"
          >
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={redo}
            disabled={!canRedo}
            title="Redo (Ctrl+Shift+Z)"
            data-testid="redo-button"
          >
            <Redo2 className="h-4 w-4" />
          </Button>

          {/* Save button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => void saveNow()}
            disabled={isSaving || !isDirty}
            data-testid="save-button"
          >
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>

          {/* Export button - Story 4.7, AC1 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportClick}
            disabled={isExporting || (draft.status !== 'complete' && draft.status !== 'editing')}
            data-testid="export-button"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Export
          </Button>

          {/* Feedback button - Story 7-20, AC-7.20.1 */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleFeedbackClick}
                    disabled={isStreaming || isSubmittingFeedback}
                    data-testid="feedback-button"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Feedback
                  </Button>
                </span>
              </TooltipTrigger>
              {isStreaming && (
                <TooltipContent>
                  <p>Wait for generation to complete before providing feedback</p>
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>

          {/* Close button */}
          <Button variant="ghost" size="icon" onClick={onClose} data-testid="close-button">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Export Modal - Story 4.7, AC1 */}
      <ExportModal
        open={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleFormatSelected}
        citationCount={citations.length}
        isExporting={isExporting}
      />

      {/* Verification Dialog - Story 4.7, AC2 */}
      <VerificationDialog
        open={showVerificationDialog}
        citationCount={citations.length}
        documentCount={new Set(citations.map((c) => c.document_id)).size}
        draftId={draft.id}
        onConfirm={handleExportConfirm}
        onCancel={() => {
          setShowVerificationDialog(false);
          setSelectedFormat(null);
        }}
      />

      {/* Feedback Modal - Story 7-20, AC-7.20.2 */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackSubmit}
        isSubmitting={isSubmittingFeedback}
      />

      {/* Recovery Modal - Story 7-20, AC-7.20.4 */}
      <RecoveryModal
        isOpen={showRecoveryModal && alternatives.length > 0}
        onClose={handleRecoveryClose}
        alternatives={alternatives}
        onActionSelect={handleRecoveryAction}
      />

      {/* 2-Panel Layout */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Panel: Editable Content */}
        <div className="flex-1 border-r flex flex-col">
          {/* Citation Validation Warnings - Story 7-21, AC-7.21.4 */}
          {hasWarnings && (
            <div className="p-4 pb-0">
              <CitationWarningBanner
                warnings={warnings}
                onDismiss={dismissWarning}
                onAutoFix={handleAutoFixCitations}
                showAutoFix={true}
              />
            </div>
          )}
          <ScrollArea className="flex-1">
            <div
              ref={editorRef}
              contentEditable
              suppressContentEditableWarning
              onInput={handleContentChange}
              className="p-6 prose prose-sm max-w-none focus:outline-none"
              data-testid="draft-content"
              dangerouslySetInnerHTML={{ __html: renderContentAsHTML() }}
            />
          </ScrollArea>
        </div>

        {/* Right Panel: Citations */}
        <div className="w-80 border-l bg-muted/30">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-sm">Citations ({citations.length})</h3>
          </div>
          <ScrollArea className="h-[calc(100vh-140px)]">
            <div className="p-4 space-y-3">
              {citations.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No citations in this draft.</p>
              ) : (
                citations.map((citation) => (
                  <Card
                    key={citation.number}
                    className="cursor-pointer hover:bg-accent"
                    data-testid={`citation-card-${citation.number}`}
                  >
                    <CardHeader className="p-3 pb-2">
                      <CardTitle className="text-xs font-medium flex items-center gap-2">
                        <Badge variant="outline">[{citation.number}]</Badge>
                        {citation.document_name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 pt-0">
                      <p className="text-xs text-muted-foreground line-clamp-3">
                        {citation.excerpt}
                      </p>
                      {(citation.page_number || citation.section_header) && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {citation.page_number && `Page ${citation.page_number}`}
                          {citation.page_number && citation.section_header && ' • '}
                          {citation.section_header}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
