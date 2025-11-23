# Knowledge Base Management Guide

This guide covers everything you need to know about creating, organizing, and managing Knowledge Bases in LumiKB.

## Creating a Knowledge Base

To create a new Knowledge Base:

1. Click the "+" button in the Knowledge Bases sidebar
2. Enter a descriptive name (e.g., "Product Documentation Q4 2025")
3. Add an optional description explaining the KB's purpose
4. Set initial permissions for your team

### Naming Best Practices

Choose names that are:

- **Descriptive**: "Engineering Architecture Docs" not "Eng Docs"
- **Specific**: "Customer Support Scripts 2025" not "Support"
- **Consistent**: Follow your organization's naming conventions

## Uploading Documents

### Supported Formats

LumiKB accepts the following document types:

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | .pdf | Preserves page numbers for citations |
| Word | .docx | Converts to searchable text |
| Markdown | .md | Ideal for technical documentation |
| Plain Text | .txt | Simple but effective |

### Upload Process

1. Navigate to your Knowledge Base
2. Click "Upload Documents" or drag files to the upload zone
3. Wait for processing to complete
4. Verify documents appear in the document list

### Processing Status

Documents go through several stages:

- **Pending**: Upload received, waiting for processing
- **Processing**: Text extraction and embedding generation
- **Ready**: Fully indexed and searchable
- **Failed**: Processing error (check error message)

## Organizing Documents

### Using Multiple Knowledge Bases

Consider creating separate KBs for:

- Different departments (Engineering, Sales, HR)
- Different projects or products
- Different access levels (Public, Internal, Confidential)

### Document Metadata

Each document tracks:

- Original filename
- Upload date
- File size
- Chunk count (number of searchable segments)
- Processing status

## Managing Permissions

### Permission Levels

| Level | Can Search | Can Upload | Can Delete | Can Manage Users |
|-------|-----------|------------|------------|------------------|
| Read | Yes | No | No | No |
| Write | Yes | Yes | Own docs | No |
| Admin | Yes | Yes | All docs | Yes |

### Granting Access

As a KB Admin:

1. Open Knowledge Base settings
2. Navigate to "Permissions" tab
3. Search for users by email
4. Select permission level
5. Click "Grant Access"

### Revoking Access

To remove a user's access:

1. Find the user in the permissions list
2. Click the "Remove" button
3. Confirm the action

## Document Lifecycle

### Updating Documents

To update a document:

1. Delete the existing version
2. Upload the new version
3. Wait for reprocessing

Future versions will support in-place updates with version history.

### Deleting Documents

Deleting a document:

- Removes it from search results immediately
- Deletes stored file from object storage
- Removes all associated vector embeddings
- Cannot be undone

### Archiving Knowledge Bases

To archive a KB you no longer need:

1. Export important documents if needed
2. Remove all documents
3. Delete the Knowledge Base

## Performance Considerations

### Optimal Document Size

For best results:

- Keep documents under 100 pages each
- Split very large documents into logical sections
- Use clear headings and structure

### Chunk Quality

LumiKB automatically chunks documents into ~500 token segments. Well-structured documents with clear sections produce better chunks and more accurate search results.

## Troubleshooting

### Document Stuck in Processing

If a document remains in "Processing" status:

1. Check the system status page
2. Try deleting and re-uploading
3. Contact your administrator

### Search Not Finding Content

If expected content isn't found:

1. Verify the document is in "Ready" status
2. Check you have Read permission on the KB
3. Try rephrasing your search query

## Summary

Effective Knowledge Base management is the foundation of a successful LumiKB deployment. Organize your content thoughtfully, maintain clear permissions, and keep documents well-structured for the best experience.
