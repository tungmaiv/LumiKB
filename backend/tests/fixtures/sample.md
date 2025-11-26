# Sample Markdown Document

This is a sample markdown document used for testing document parsing functionality in LumiKB.

## Introduction

LumiKB is an enterprise RAG-powered knowledge management system. This document serves as a test fixture for the document processing pipeline.

## Features

The system provides the following key features:

### Document Management

- Upload and store documents in MinIO
- Parse PDF, DOCX, and Markdown files
- Extract text and metadata for indexing

### Semantic Search

The semantic search feature allows users to find relevant information across their knowledge bases using natural language queries.

## Technical Details

The document processing pipeline consists of several stages:

1. **Upload**: Files are uploaded via the API and stored in MinIO
2. **Parse**: Text is extracted using the unstructured library
3. **Chunk**: Content is split into semantic chunks
4. **Embed**: Chunks are converted to vector embeddings
5. **Index**: Vectors are stored in Qdrant for search

## Conclusion

This sample document contains sufficient text content (well over 100 characters) to pass the minimum content validation check during parsing tests.

The document also has multiple heading levels to test heading extraction functionality.
