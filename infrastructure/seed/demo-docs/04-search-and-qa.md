# Search and Q&A Features

LumiKB's search capabilities go far beyond traditional keyword matching. This guide explains how to get the most out of semantic search and AI-powered question answering.

## Semantic Search

### How It Works

Traditional search looks for exact word matches. Semantic search understands meaning. When you search for "authentication process", LumiKB also finds content about:

- Login procedures
- Sign-in workflows
- User verification steps
- Access control mechanisms

This happens because LumiKB converts text into mathematical vectors that capture semantic meaning. Similar concepts have similar vectors, enabling intelligent matching.

### Search Tips

#### Be Specific

Instead of: "security"
Try: "how do we handle password reset requests"

#### Use Natural Language

Instead of: "API rate limit config"
Try: "what are our API rate limiting settings"

#### Ask Questions

The best searches are often phrased as questions:

- "What is our refund policy?"
- "How do I deploy to production?"
- "What are the system requirements?"

## Question Answering

### Single Knowledge Base Q&A

Select a Knowledge Base and ask your question. LumiKB will:

1. Search for relevant content
2. Read and understand the passages
3. Synthesize a coherent answer
4. Add citations to source documents

### Cross-KB Search

For broader questions, enable cross-KB search to query multiple Knowledge Bases simultaneously. This is useful when:

- Information spans multiple departments
- You're not sure which KB contains the answer
- You want a comprehensive overview

## Advanced Features

### Quick Search

Press `Cmd+K` (Mac) or `Ctrl+K` (Windows) to open Quick Search from anywhere in LumiKB. Type your query and see instant results without navigating away from your current view.

### Search Filters

Narrow your search with filters:

- **Date Range**: Find content from specific time periods
- **Document Type**: Limit to PDFs, Markdown, etc.
- **Status**: Search only Ready documents

### Search History

LumiKB remembers your recent searches. Access them by clicking the search input to see suggestions based on your history.

## Understanding Results

### Relevance Ranking

Results are ordered by semantic similarity to your query. The most relevant content appears first, even if it doesn't contain your exact keywords.

### Result Previews

Each result shows:

- Document name and Knowledge Base
- Relevant text snippet with query terms highlighted
- Relevance score indicator
- Quick action buttons

### Citations in Answers

AI-generated answers include numbered citations like [1], [2], etc. Click any citation to:

- See the source document
- View the exact passage
- Navigate to that location in the full document

## Chat Interface

### Conversational Q&A

Beyond single questions, LumiKB supports conversational interactions:

**You**: What is our authentication flow?

**LumiKB**: Users authenticate via OAuth 2.0 with JWT tokens... [1]

**You**: What about refresh tokens?

**LumiKB**: Building on the authentication flow, refresh tokens are issued... [2]

The system maintains context, so follow-up questions reference the previous discussion.

### Conversation Management

- **New Chat**: Start fresh with `Cmd+N`
- **Save Chat**: Bookmark important conversations
- **Share Chat**: Send conversation links to colleagues
- **Export Chat**: Download as Markdown or PDF

## Best Practices

### Formulating Queries

1. **Start broad, then narrow**: Begin with a general question, then ask follow-ups for details
2. **One topic per question**: Complex questions with multiple parts may get incomplete answers
3. **Provide context**: "For the mobile app, how do we handle..." is better than "how do we handle..."

### Evaluating Answers

1. **Check citation count**: More citations often mean more comprehensive answers
2. **Verify key claims**: Click through to sources for important information
3. **Consider recency**: Check document dates for time-sensitive topics

### Improving Results

If answers aren't satisfactory:

1. Rephrase your question
2. Check if relevant documents exist in the KB
3. Try searching a different Knowledge Base
4. Ask a more specific question

## Limitations

### What LumiKB Cannot Do

- Answer questions about content not in your Knowledge Bases
- Access real-time external information
- Remember conversations across sessions (without saving)
- Guarantee 100% accuracy (always verify with citations)

### When to Use Traditional Search

Sometimes keyword search is more appropriate:

- Looking for a specific document by name
- Searching for exact phrases or codes
- Finding all occurrences of a term

## Summary

LumiKB's search and Q&A capabilities transform how you interact with your organization's knowledge. By understanding semantic search and following best practices, you can find information faster and make better-informed decisions.
