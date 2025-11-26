import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadDropzone } from '../upload-dropzone';

// Mock the useFileUpload hook
vi.mock('@/lib/hooks/use-file-upload', () => ({
  useFileUpload: vi.fn(() => ({
    files: [],
    addFiles: vi.fn(),
    cancelUpload: vi.fn(),
    retryUpload: vi.fn(),
    clearCompleted: vi.fn(),
    isUploading: false,
  })),
}));

// Mock toast
vi.mock('@/lib/utils/document-toast', () => ({
  showDocumentStatusToast: vi.fn(),
}));

describe('UploadDropzone', () => {
  const defaultProps = {
    kbId: 'test-kb-id',
    userPermission: 'WRITE' as const,
    onUploadComplete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dropzone for WRITE permission users', () => {
    render(<UploadDropzone {...defaultProps} />);

    expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOCX, MD up to 50MB/i)).toBeInTheDocument();
  });

  it('renders dropzone for ADMIN permission users', () => {
    render(<UploadDropzone {...defaultProps} userPermission="ADMIN" />);

    expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument();
  });

  it('does not render for READ permission users', () => {
    const { container } = render(<UploadDropzone {...defaultProps} userPermission="READ" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('does not render when show prop is false', () => {
    const { container } = render(<UploadDropzone {...defaultProps} show={false} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('displays browse text for click-to-upload', () => {
    render(<UploadDropzone {...defaultProps} />);

    expect(screen.getByText('browse')).toBeInTheDocument();
  });

  it('has file input element for file picker', () => {
    render(<UploadDropzone {...defaultProps} />);

    const input = document.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
  });

  it('file input accepts multiple files', () => {
    render(<UploadDropzone {...defaultProps} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toHaveAttribute('multiple');
  });

  it('file input has correct accept attribute for supported formats', () => {
    render(<UploadDropzone {...defaultProps} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toHaveAttribute('accept');
    const accept = input.getAttribute('accept');
    expect(accept).toContain('application/pdf');
    expect(accept).toContain('.pdf');
    expect(accept).toContain('.docx');
    expect(accept).toContain('.md');
  });

  it('displays supported formats in helper text', () => {
    render(<UploadDropzone {...defaultProps} />);

    expect(screen.getByText(/PDF, DOCX, MD/)).toBeInTheDocument();
    expect(screen.getByText(/50MB/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<UploadDropzone {...defaultProps} className="custom-class" />);

    const wrapper = screen.getByText(/drag & drop/i).closest('.space-y-3');
    expect(wrapper).toHaveClass('custom-class');
  });
});

describe('UploadDropzone - Permission-based rendering', () => {
  it('is visible when userPermission is WRITE', () => {
    render(<UploadDropzone kbId="kb-1" userPermission="WRITE" />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('is visible when userPermission is ADMIN', () => {
    render(<UploadDropzone kbId="kb-1" userPermission="ADMIN" />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('is hidden when userPermission is READ', () => {
    const { container } = render(<UploadDropzone kbId="kb-1" userPermission="READ" />);
    expect(container).toBeEmptyDOMElement();
  });
});
