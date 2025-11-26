'use client';

import { useCallback, useState } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { UploadCloudIcon, FileIcon, AlertCircleIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { showDocumentStatusToast } from '@/lib/utils/document-toast';
import { UploadProgress } from './upload-progress';
import { DuplicateDialog, type DuplicateInfo } from './duplicate-dialog';
import { useFileUpload, type UploadFile } from '@/lib/hooks/use-file-upload';

/** Maximum file size in bytes (50MB) */
const MAX_FILE_SIZE = 52428800;

/** Accepted MIME types for document upload */
const ACCEPTED_MIME_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/markdown': ['.md'],
  'text/x-markdown': ['.md'],
};

/** Supported file extensions display string */
const SUPPORTED_FORMATS = 'PDF, DOCX, MD';

interface UploadDropzoneProps {
  /** Knowledge Base ID to upload documents to */
  kbId: string;
  /** User's permission level on the KB */
  userPermission?: 'READ' | 'WRITE' | 'ADMIN';
  /** Callback when an upload completes successfully */
  onUploadComplete?: () => void;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show the dropzone (false hides it entirely) */
  show?: boolean;
}

/**
 * UploadDropzone provides drag-and-drop file upload functionality.
 *
 * Features:
 * - Drag-and-drop visual feedback (isDragActive state)
 * - Click to open file picker
 * - Multi-file selection support
 * - Client-side file type validation (PDF, DOCX, MD)
 * - Client-side file size validation (50MB max)
 * - Upload progress tracking
 * - Toast notifications for success/error
 * - Hidden/disabled for READ-only users
 *
 * @example
 * <UploadDropzone
 *   kbId="kb-uuid"
 *   userPermission="WRITE"
 *   onUploadComplete={() => refetchDocuments()}
 * />
 */
export function UploadDropzone({
  kbId,
  userPermission = 'READ',
  onUploadComplete,
  className,
  show = true,
}: UploadDropzoneProps) {
  const canUpload = userPermission === 'WRITE' || userPermission === 'ADMIN';

  // State for duplicate dialog
  const [duplicateFile, setDuplicateFile] = useState<UploadFile | null>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);

  // Initialize file upload hook
  const { files, addFiles, cancelUpload, retryUpload, replaceFile, skipDuplicate, isUploading } =
    useFileUpload({
      kbId,
      onUploadComplete: (file) => {
        showDocumentStatusToast(file.file.name, 'upload-success');
        onUploadComplete?.();
      },
      onUploadError: (file, error) => {
        showDocumentStatusToast(file.file.name, 'upload-error', error);
      },
      onDuplicateDetected: (file, info) => {
        setDuplicateFile(file);
        setDuplicateInfo(info);
      },
    });

  // Handle file rejections (validation errors)
  const handleDropRejected = useCallback((rejections: FileRejection[]) => {
    rejections.forEach((rejection) => {
      const { file, errors } = rejection;
      const errorMessages = errors.map((e) => {
        if (e.code === 'file-too-large') {
          return 'Maximum file size is 50MB';
        }
        if (e.code === 'file-invalid-type') {
          return `Supported formats: ${SUPPORTED_FORMATS}`;
        }
        return e.message;
      });

      showDocumentStatusToast(file.name, 'upload-error', errorMessages.join('. '));
    });
  }, []);

  // Handle accepted files
  const handleDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        addFiles(acceptedFiles);
      }
    },
    [addFiles]
  );

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: handleDrop,
    onDropRejected: handleDropRejected,
    accept: ACCEPTED_MIME_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    disabled: !canUpload,
  });

  // Handlers for duplicate dialog
  const handleDuplicateReplace = useCallback(() => {
    if (duplicateFile) {
      replaceFile(duplicateFile.id);
      setDuplicateFile(null);
      setDuplicateInfo(null);
    }
  }, [duplicateFile, replaceFile]);

  const handleDuplicateSkip = useCallback(() => {
    if (duplicateFile) {
      skipDuplicate(duplicateFile.id);
      setDuplicateFile(null);
      setDuplicateInfo(null);
    }
  }, [duplicateFile, skipDuplicate]);

  const handleDuplicateCancel = useCallback(() => {
    // Cancel is same as skip for now
    handleDuplicateSkip();
  }, [handleDuplicateSkip]);

  // Don't render if explicitly hidden or no permission
  if (!show || !canUpload) {
    return null;
  }

  // Show uploads that are not yet completed (pending, uploading, failed, or duplicate)
  const activeUploads = files.filter((f) => f.status !== 'completed');

  return (
    <div className={cn('space-y-3', className)}>
      {/* Dropzone Area */}
      <div
        {...getRootProps()}
        className={cn(
          'relative flex flex-col items-center justify-center gap-2',
          'rounded-lg border-2 border-dashed p-6 cursor-pointer',
          'transition-all duration-200 ease-in-out',
          // Default state
          'border-muted-foreground/25 bg-muted/30',
          'hover:border-primary/50 hover:bg-muted/50',
          // Drag active state
          isDragActive && !isDragReject && 'border-primary bg-primary/10 scale-[1.02]',
          // Drag reject state (invalid file type)
          isDragReject && 'border-destructive bg-destructive/10',
          // Uploading state
          isUploading && 'opacity-75'
        )}
      >
        <input {...getInputProps()} />

        {/* Icon */}
        <div
          className={cn(
            'rounded-full p-3 transition-colors duration-200',
            isDragActive && !isDragReject && 'bg-primary/20',
            isDragReject && 'bg-destructive/20',
            !isDragActive && 'bg-muted'
          )}
        >
          {isDragReject ? (
            <AlertCircleIcon className="size-6 text-destructive" />
          ) : isDragActive ? (
            <FileIcon className="size-6 text-primary" />
          ) : (
            <UploadCloudIcon className="size-6 text-muted-foreground" />
          )}
        </div>

        {/* Text */}
        <div className="text-center">
          {isDragReject ? (
            <>
              <p className="text-sm font-medium text-destructive">Invalid file type</p>
              <p className="text-xs text-muted-foreground mt-1">
                Supported formats: {SUPPORTED_FORMATS}
              </p>
            </>
          ) : isDragActive ? (
            <p className="text-sm font-medium text-primary">Drop files to upload</p>
          ) : (
            <>
              <p className="text-sm font-medium">
                Drag & drop files here, or <span className="text-primary">browse</span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">{SUPPORTED_FORMATS} up to 50MB</p>
            </>
          )}
        </div>
      </div>

      {/* Upload Progress List */}
      {activeUploads.length > 0 && (
        <UploadProgress files={activeUploads} onCancel={cancelUpload} onRetry={retryUpload} />
      )}

      {/* Duplicate File Dialog */}
      <DuplicateDialog
        isOpen={!!duplicateFile}
        onCancel={handleDuplicateCancel}
        onReplace={handleDuplicateReplace}
        onSkip={handleDuplicateSkip}
        filename={duplicateFile?.file.name || ''}
        duplicateInfo={duplicateInfo}
      />
    </div>
  );
}
