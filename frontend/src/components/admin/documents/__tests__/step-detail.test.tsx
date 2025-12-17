/**
 * Step Detail Component Tests
 *
 * Story 9-10: Document Timeline UI
 * AC10: Unit tests for timeline rendering and interactions
 * AC5: Click step to see detailed metrics
 * AC6: Error steps show error type and full error message
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StepDetail } from '../step-detail';

describe('StepDetail', () => {
  describe('Error message display (AC6)', () => {
    it('displays error message for failed steps', () => {
      render(
        <StepDetail
          stepName="parse"
          status="failed"
          metrics={null}
          errorMessage="Failed to parse document: Invalid PDF format"
        />
      );

      const errorMessage = screen.getByTestId('step-error-message');
      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveTextContent('Error:');
      expect(errorMessage).toHaveTextContent('Failed to parse document: Invalid PDF format');
    });

    it('does not display error message for completed steps', () => {
      render(
        <StepDetail
          stepName="parse"
          status="completed"
          metrics={{ pages_extracted: 5 }}
          errorMessage={null}
        />
      );

      expect(screen.queryByTestId('step-error-message')).not.toBeInTheDocument();
    });
  });

  describe('Upload step metrics', () => {
    it('displays file size and MIME type', () => {
      render(
        <StepDetail
          stepName="upload"
          status="completed"
          metrics={{ file_size: 1048576, mime_type: 'application/pdf' }}
          errorMessage={null}
        />
      );

      expect(screen.getByText('File Size')).toBeInTheDocument();
      expect(screen.getByText('1 MB')).toBeInTheDocument();
      expect(screen.getByText('MIME Type')).toBeInTheDocument();
      expect(screen.getByText('application/pdf')).toBeInTheDocument();
    });
  });

  describe('Parse step metrics', () => {
    it('displays pages, text length, and parser', () => {
      render(
        <StepDetail
          stepName="parse"
          status="completed"
          metrics={{
            pages_extracted: 10,
            text_length: 50000,
            parser_used: 'PyPDF2',
          }}
          errorMessage={null}
        />
      );

      expect(screen.getByText('Pages Extracted')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Text Length')).toBeInTheDocument();
      expect(screen.getByText('50,000')).toBeInTheDocument();
      expect(screen.getByText('Parser')).toBeInTheDocument();
      expect(screen.getByText('PyPDF2')).toBeInTheDocument();
    });
  });

  describe('Chunk step metrics', () => {
    it('displays chunks created and average size', () => {
      render(
        <StepDetail
          stepName="chunk"
          status="completed"
          metrics={{
            chunks_created: 25,
            avg_chunk_size: 500,
          }}
          errorMessage={null}
        />
      );

      expect(screen.getByText('Chunks Created')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('Avg Chunk Size')).toBeInTheDocument();
      expect(screen.getByText('500')).toBeInTheDocument();
    });
  });

  describe('Embed step metrics', () => {
    it('displays vectors generated and model', () => {
      render(
        <StepDetail
          stepName="embed"
          status="completed"
          metrics={{
            vectors_generated: 100,
            embedding_model: 'text-embedding-3-small',
          }}
          errorMessage={null}
        />
      );

      expect(screen.getByText('Vectors Generated')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('Embedding Model')).toBeInTheDocument();
      expect(screen.getByText('text-embedding-3-small')).toBeInTheDocument();
    });
  });

  describe('Index step metrics', () => {
    it('displays points indexed and collection', () => {
      render(
        <StepDetail
          stepName="index"
          status="completed"
          metrics={{
            points_indexed: 50,
            collection_name: 'kb_documents',
          }}
          errorMessage={null}
        />
      );

      expect(screen.getByText('Points Indexed')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('Collection')).toBeInTheDocument();
      expect(screen.getByText('kb_documents')).toBeInTheDocument();
    });
  });

  describe('No metrics', () => {
    it('shows no metrics message when metrics is null', () => {
      render(<StepDetail stepName="parse" status="completed" metrics={null} errorMessage={null} />);

      expect(screen.getByText('No metrics available')).toBeInTheDocument();
    });
  });
});
