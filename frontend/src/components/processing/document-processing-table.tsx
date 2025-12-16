/**
 * Document processing table component
 * Story 5-23 (AC-5.23.1): Shows step-level progress for each document
 */

"use client";

import {
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  XCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type {
  DocumentProcessingStatus,
  ProcessingStep,
  DocumentStatus,
} from "@/types/processing";
import {
  STEP_LABELS,
  DOC_STATUS_LABELS,
  PROCESSING_STEPS_ORDER,
} from "@/types/processing";

export interface DocumentProcessingTableProps {
  documents: DocumentProcessingStatus[];
  total: number;
  page: number;
  pageSize: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onDocumentClick: (docId: string) => void;
  /** Hide the built-in pagination (when parent handles it) */
  hidePagination?: boolean;
}

/**
 * Get progress percentage based on current step
 */
function getProgressPercentage(
  status: DocumentStatus,
  currentStep: ProcessingStep
): number {
  // Normalize status to lowercase for comparison (backend returns uppercase)
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "ready" || normalizedStatus === "archived") return 100;
  if (normalizedStatus === "failed" || normalizedStatus === "pending") {
    // For failed/pending, show progress up to current step
    const stepIndex = PROCESSING_STEPS_ORDER.indexOf(currentStep);
    return Math.round((stepIndex / (PROCESSING_STEPS_ORDER.length - 1)) * 100);
  }

  const stepIndex = PROCESSING_STEPS_ORDER.indexOf(currentStep);
  // Add half step for in-progress
  return Math.round(
    ((stepIndex + 0.5) / (PROCESSING_STEPS_ORDER.length - 1)) * 100
  );
}

/**
 * Get status icon and color
 */
function getStatusBadge(status: DocumentStatus) {
  // Normalize status to lowercase for comparison (backend returns uppercase)
  const normalizedStatus = status.toLowerCase();

  switch (normalizedStatus) {
    case "ready":
      return (
        <Badge variant="default" className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          {DOC_STATUS_LABELS.ready}
        </Badge>
      );
    case "processing":
      return (
        <Badge variant="secondary" className="bg-blue-100 text-blue-800">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          {DOC_STATUS_LABELS.processing}
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="destructive">
          <XCircle className="mr-1 h-3 w-3" />
          {DOC_STATUS_LABELS.failed}
        </Badge>
      );
    case "pending":
      return (
        <Badge variant="outline">
          <Clock className="mr-1 h-3 w-3" />
          {DOC_STATUS_LABELS.pending}
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function DocumentProcessingTable({
  documents,
  total,
  page,
  pageSize,
  isLoading,
  onPageChange,
  onDocumentClick,
  hidePagination = false,
}: DocumentProcessingTableProps) {
  const totalPages = Math.ceil(total / pageSize);
  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4" />
        <p className="text-lg">No documents found</p>
        <p className="text-sm">
          Try adjusting your filters or upload some documents
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Document</TableHead>
              <TableHead className="w-[100px]">Type</TableHead>
              <TableHead className="w-[100px]">Size</TableHead>
              <TableHead className="w-[120px]">Status</TableHead>
              <TableHead className="w-[200px]">Progress</TableHead>
              <TableHead className="w-[100px]">Chunks</TableHead>
              <TableHead className="w-[120px]">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow
                key={doc.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => onDocumentClick(doc.id)}
              >
                <TableCell>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span
                      className="font-medium truncate max-w-[250px]"
                      title={doc.original_filename}
                    >
                      {doc.original_filename}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="font-mono text-xs">
                    {doc.file_type.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatFileSize(doc.file_size)}
                </TableCell>
                <TableCell>{getStatusBadge(doc.status)}</TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <Progress
                      value={getProgressPercentage(doc.status, doc.current_step)}
                      className="h-2"
                    />
                    <span className="text-xs text-muted-foreground">
                      {doc.status.toLowerCase() === "ready"
                        ? "Complete"
                        : doc.status.toLowerCase() === "failed"
                        ? `Failed at ${STEP_LABELS[doc.current_step]}`
                        : `${STEP_LABELS[doc.current_step]}`}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.chunk_count !== null ? doc.chunk_count : "-"}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {formatDate(doc.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination - only show if not hidden */}
      {!hidePagination && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {startItem} to {endItem} of {total} documents
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
