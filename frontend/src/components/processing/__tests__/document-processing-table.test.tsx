/**
 * Unit tests for DocumentProcessingTable component
 * Story 5-23 (AC-5.23.1): Document list with processing status
 *
 * Tests table rendering, status badges, pagination, and row click handling.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { DocumentProcessingTable } from '../document-processing-table';
import type { DocumentProcessingStatus } from '@/types/processing';

// Mock documents for testing
const mockDocuments: DocumentProcessingStatus[] = [
  {
    id: 'doc-1',
    original_filename: 'test-document.pdf',
    file_type: 'pdf',
    file_size: 1024000, // 1MB
    status: 'processing',
    current_step: 'parse',
    chunk_count: null,
    created_at: '2025-12-06T10:00:00Z',
    updated_at: '2025-12-06T10:00:05Z',
  },
  {
    id: 'doc-2',
    original_filename: 'completed-doc.pdf',
    file_type: 'pdf',
    file_size: 2048000, // 2MB
    status: 'ready',
    current_step: 'complete',
    chunk_count: 25,
    created_at: '2025-12-06T09:00:00Z',
    updated_at: '2025-12-06T09:05:00Z',
  },
  {
    id: 'doc-3',
    original_filename: 'failed-doc.docx',
    file_type: 'docx',
    file_size: 512000, // 512KB
    status: 'failed',
    current_step: 'embed',
    chunk_count: null,
    created_at: '2025-12-06T08:00:00Z',
    updated_at: '2025-12-06T08:01:00Z',
  },
  {
    id: 'doc-4',
    original_filename: 'pending-doc.txt',
    file_type: 'txt',
    file_size: 1024, // 1KB
    status: 'pending',
    current_step: 'upload',
    chunk_count: null,
    created_at: '2025-12-06T10:30:00Z',
    updated_at: '2025-12-06T10:30:00Z',
  },
];

describe('DocumentProcessingTable', () => {
  const mockOnPageChange = vi.fn();
  const mockOnDocumentClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should render table headers correctly - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    expect(screen.getByText('Document')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Size')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Progress')).toBeInTheDocument();
    expect(screen.getByText('Chunks')).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();
  });

  it('[P0] should render document rows with correct data - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('completed-doc.pdf')).toBeInTheDocument();
    expect(screen.getByText('failed-doc.docx')).toBeInTheDocument();
    expect(screen.getByText('pending-doc.txt')).toBeInTheDocument();
  });

  it('[P0] should display correct status badges - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - check status badges are present
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('[P0] should display file type badges - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    const pdfBadges = screen.getAllByText('PDF');
    expect(pdfBadges.length).toBe(2);
    expect(screen.getByText('DOCX')).toBeInTheDocument();
    expect(screen.getByText('TXT')).toBeInTheDocument();
  });

  it('[P0] should display chunk count or dash for incomplete documents - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - completed doc has chunk count
    expect(screen.getByText('25')).toBeInTheDocument();
    // Other docs show dash
    const dashes = screen.getAllByText('-');
    expect(dashes.length).toBeGreaterThanOrEqual(3);
  });

  it('[P0] should call onDocumentClick when row is clicked - AC-5.23.3', () => {
    // Arrange
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Act
    fireEvent.click(screen.getByText('test-document.pdf'));

    // Assert
    expect(mockOnDocumentClick).toHaveBeenCalledWith('doc-1');
  });

  it('[P0] should show loading state - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={[]}
        total={0}
        page={1}
        pageSize={20}
        isLoading={true}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - should not show table, just loading indicator
    expect(screen.queryByText('Document')).not.toBeInTheDocument();
  });

  it('[P0] should show empty state when no documents - AC-5.23.1', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={[]}
        total={0}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    expect(screen.getByText('No documents found')).toBeInTheDocument();
    expect(
      screen.getByText('Try adjusting your filters or upload some documents')
    ).toBeInTheDocument();
  });

  it('[P1] should show pagination info - AC-5.23.4', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={100}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - endItem is min(page * pageSize, total) = min(20, 100) = 20
    expect(screen.getByText('Showing 1 to 20 of 100 documents')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 5')).toBeInTheDocument();
  });

  it('[P1] should have Previous and Next buttons - AC-5.23.4', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={100}
        page={2}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('[P1] should disable Previous button on first page - AC-5.23.4', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={100}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('[P1] should disable Next button on last page - AC-5.23.4', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - only 4 items, 1 page
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  it('[P1] should call onPageChange when Next is clicked - AC-5.23.4', () => {
    // Arrange
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={100}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Act
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Assert
    expect(mockOnPageChange).toHaveBeenCalledWith(2);
  });

  it('[P1] should call onPageChange when Previous is clicked - AC-5.23.4', () => {
    // Arrange
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={100}
        page={3}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Act
    fireEvent.click(screen.getByRole('button', { name: /previous/i }));

    // Assert
    expect(mockOnPageChange).toHaveBeenCalledWith(2);
  });

  it('[P2] should format file size correctly', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - check formatted sizes
    expect(screen.getByText('1000.0 KB')).toBeInTheDocument(); // 1MB
    expect(screen.getByText('2.0 MB')).toBeInTheDocument(); // 2MB
    expect(screen.getByText('500.0 KB')).toBeInTheDocument(); // 512KB
    expect(screen.getByText('1.0 KB')).toBeInTheDocument(); // 1KB
  });

  it('[P2] should show progress indicator for processing step', () => {
    // Arrange & Act
    render(
      <DocumentProcessingTable
        documents={mockDocuments}
        total={4}
        page={1}
        pageSize={20}
        onPageChange={mockOnPageChange}
        onDocumentClick={mockOnDocumentClick}
      />
    );

    // Assert - check progress text
    expect(screen.getByText('Parse')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Failed at Embed')).toBeInTheDocument();
  });
});
