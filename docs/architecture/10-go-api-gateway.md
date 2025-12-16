# Go API Gateway Architecture

> **Status:** Proposed
> **Author:** Architecture Team (Party Mode Session)
> **Date:** 2025-12-09
> **Related:** [System Overview](01-system-overview.md), [LLM Configuration](03-llm-configuration.md)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Motivation & Goals](#motivation--goals)
3. [Architecture Overview](#architecture-overview)
4. [Service Boundaries](#service-boundaries)
5. [Technology Stack](#technology-stack)
6. [Go Project Structure](#go-project-structure)
7. [gRPC Integration](#grpc-integration)
8. [Authentication & Authorization](#authentication--authorization)
9. [API Endpoints Migration](#api-endpoints-migration)
10. [Streaming Implementation](#streaming-implementation)
11. [Database Access](#database-access)
12. [Docker Deployment](#docker-deployment)
13. [Migration Strategy](#migration-strategy)
14. [Testing Strategy](#testing-strategy)
15. [Risk Assessment](#risk-assessment)
16. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document outlines the architecture for migrating LumiKB's API layer from Python/FastAPI to Go, while keeping AI-critical services (Search, Generation, Embedding) in Python. The hybrid architecture uses gRPC for inter-service communication and maintains full API compatibility with the existing frontend.

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Go for API Gateway | High concurrency, low latency, strong typing |
| Python for AI Services | LangChain/LangGraph ecosystem, no Go alternatives |
| gRPC for communication | Binary protocol, streaming support, type safety |
| Shared PostgreSQL | Single source of truth, transactional consistency |

### What Moves to Go (~40% of backend)

- User Management & Authentication
- Audit Service
- Knowledge Base CRUD
- System Configuration
- Queue Status Monitoring
- API Gateway (routing, rate limiting, metrics)

### What Stays in Python (~60% of backend)

- Search Service (LangChain RAG)
- Generation Service (LangGraph)
- Embedding Service (sentence-transformers)
- Document Processing Workers (Celery + unstructured)

---

## Motivation & Goals

### Why Migrate to Go?

1. **Performance**: Go handles 10x more concurrent connections with lower memory
2. **Type Safety**: Compile-time error detection vs runtime
3. **Deployment**: Single binary, fast startup, small container images
4. **Maintainability**: Explicit error handling, no magic decorators

### Non-Goals

- Rewriting AI/ML logic in Go (no ecosystem)
- Changing the frontend API contract
- Migrating Celery workers (Python-bound)

---

## Architecture Overview

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                           (Next.js + React)                             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP/SSE
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          GO API GATEWAY                                  │
│                              :8080                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │    Auth     │ │    Users    │ │   Audit     │ │   KB CRUD       │   │
│  │  Middleware │ │   Handler   │ │   Handler   │ │   Handler       │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   Config    │ │    Queue    │ │   Search    │ │   Generation    │   │
│  │   Handler   │ │   Handler   │ │   Proxy     │ │   Proxy         │   │
│  └─────────────┘ └─────────────┘ └──────┬──────┘ └────────┬────────┘   │
└─────────────────────────────────────────┼─────────────────┼─────────────┘
                                          │ gRPC            │ gRPC
                                          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PYTHON AI SERVICES                                 │
│                           :50051 (gRPC)                                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │
│  │  SearchService  │ │ GenerationSvc   │ │   EmbeddingService      │   │
│  │  (LangChain)    │ │ (LangGraph)     │ │   (sentence-transformers)│   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                    │                │                │
          ┌─────────┴────────┐ ┌─────┴─────┐ ┌───────┴───────┐
          ▼                  ▼ ▼           ▼ ▼               ▼
    ┌──────────┐      ┌──────────┐   ┌──────────┐     ┌──────────┐
    │PostgreSQL│      │  Redis   │   │  Qdrant  │     │ LiteLLM  │
    │  :5432   │      │  :6379   │   │  :6333   │     │  :4000   │
    └──────────┘      └──────────┘   └──────────┘     └──────────┘
```

### Data Flow Examples

#### User Login Flow
```
Frontend → Go Gateway → Go Auth Service → PostgreSQL → JWT issued → Frontend
```

#### Search Flow (Streaming)
```
Frontend → Go Gateway (SSE) → gRPC Stream → Python Search → Qdrant →
         ← gRPC Stream results ← Go converts to SSE ← Frontend
```

#### Document Upload Flow
```
Frontend → Go Gateway → Go KB Handler → PostgreSQL (metadata)
                                      → MinIO (file storage)
                                      → Redis (Celery task) → Python Worker
```

---

## Service Boundaries

### Go API Gateway Responsibilities

| Responsibility | Implementation |
|---------------|----------------|
| TLS Termination | Go native TLS or nginx sidecar |
| Authentication | JWT validation, session management |
| Authorization | Permission checks (RBAC) |
| Rate Limiting | Token bucket per user/IP |
| Request Routing | chi router with middleware |
| Request Validation | go-playground/validator |
| Response Caching | Redis with TTL |
| Metrics Collection | Prometheus client |
| Error Handling | Structured JSON errors |
| SSE Streaming | Native http.Flusher |

### Python AI Services Responsibilities

| Responsibility | Implementation |
|---------------|----------------|
| Semantic Search | LangChain + Qdrant |
| Answer Synthesis | LangGraph chains |
| Citation Extraction | Custom LangChain tools |
| Document Generation | LangGraph + templates |
| Text Embedding | sentence-transformers |
| Document Parsing | unstructured library |
| Background Jobs | Celery workers |

### Shared Resources

| Resource | Access Pattern |
|----------|---------------|
| PostgreSQL | Both services (users, KBs, documents, audit) |
| Redis | Go (sessions, cache), Python (Celery broker) |
| Qdrant | Python only (vectors) |
| MinIO | Go (upload), Python (download for processing) |

---

## Technology Stack

### Go Services

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| HTTP Router | go-chi/chi | v5 | REST API routing |
| gRPC Client | google.golang.org/grpc | v1.60+ | Python communication |
| Database | jackc/pgx | v5 | PostgreSQL driver |
| SQL Generation | sqlc | v1.25+ | Type-safe queries |
| JWT | golang-jwt/jwt | v5 | Token handling |
| Password Hash | golang.org/x/crypto | latest | bcrypt |
| Validation | go-playground/validator | v10 | Request validation |
| Config | spf13/viper | v1 | Configuration |
| Logging | rs/zerolog | latest | Structured logging |
| Metrics | prometheus/client_golang | latest | Prometheus metrics |
| Testing | stretchr/testify | latest | Assertions |

### Python Services

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| gRPC Server | grpcio | 1.60+ | Service exposure |
| Proto Generation | grpcio-tools | 1.60+ | Code generation |
| AI Framework | langchain | 0.1+ | RAG orchestration |
| Graph Chains | langgraph | 0.0.40+ | Document generation |
| Embeddings | sentence-transformers | 2.2+ | Vector generation |
| LLM Gateway | litellm | 1.0+ | Multi-provider LLM |

---

## Go Project Structure

```
go-api/
├── cmd/
│   └── api/
│       └── main.go                 # Application entry point
├── internal/
│   ├── config/
│   │   ├── config.go               # Viper configuration
│   │   └── config_test.go
│   ├── database/
│   │   ├── db.go                   # Connection pool management
│   │   ├── migrations/             # golang-migrate files
│   │   │   ├── 001_initial.up.sql
│   │   │   └── 001_initial.down.sql
│   │   └── queries/                # sqlc generated code
│   │       ├── models.go
│   │       ├── users.sql.go
│   │       ├── knowledge_bases.sql.go
│   │       └── audit.sql.go
│   ├── auth/
│   │   ├── jwt.go                  # JWT issue/validate
│   │   ├── jwt_test.go
│   │   ├── password.go             # bcrypt hashing
│   │   ├── password_test.go
│   │   ├── middleware.go           # Auth middleware
│   │   ├── middleware_test.go
│   │   └── context.go              # User context helpers
│   ├── handlers/
│   │   ├── auth.go                 # Login/register/logout
│   │   ├── auth_test.go
│   │   ├── users.go                # User CRUD
│   │   ├── users_test.go
│   │   ├── knowledge_bases.go      # KB CRUD
│   │   ├── knowledge_bases_test.go
│   │   ├── audit.go                # Audit logs
│   │   ├── audit_test.go
│   │   ├── config.go               # System config
│   │   ├── config_test.go
│   │   ├── queue.go                # Queue status
│   │   ├── queue_test.go
│   │   ├── search.go               # Search proxy (gRPC → SSE)
│   │   ├── search_test.go
│   │   ├── generation.go           # Generation proxy
│   │   └── generation_test.go
│   ├── services/
│   │   ├── user_service.go         # User business logic
│   │   ├── user_service_test.go
│   │   ├── kb_service.go           # KB business logic
│   │   ├── kb_service_test.go
│   │   ├── audit_service.go        # Audit logging
│   │   ├── audit_service_test.go
│   │   ├── ai_client.go            # gRPC client to Python
│   │   └── ai_client_test.go
│   ├── middleware/
│   │   ├── logging.go              # Request logging
│   │   ├── cors.go                 # CORS handling
│   │   ├── ratelimit.go            # Rate limiting
│   │   ├── metrics.go              # Prometheus metrics
│   │   └── recovery.go             # Panic recovery
│   └── models/
│       ├── user.go                 # Domain models
│       ├── knowledge_base.go
│       ├── document.go
│       └── audit.go
├── api/
│   └── proto/
│       ├── ai_services.proto       # gRPC service definitions
│       └── gen/                    # Generated Go code
│           ├── ai_services.pb.go
│           └── ai_services_grpc.pb.go
├── migrations/
│   └── *.sql                       # Database migrations
├── scripts/
│   ├── generate-proto.sh           # Proto code generation
│   └── generate-sqlc.sh            # SQL code generation
├── Dockerfile
├── Makefile
├── go.mod
├── go.sum
├── sqlc.yaml                       # sqlc configuration
└── .air.toml                       # Hot reload config
```

---

## gRPC Integration

### Protocol Buffer Definitions

**`api/proto/ai_services.proto`:**

```protobuf
syntax = "proto3";

package lumikb.ai;

option go_package = "lumikb/api/gen";

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

// ============================================================================
// SEARCH SERVICE
// ============================================================================

service SearchService {
  // Streaming semantic search
  rpc Search(SearchRequest) returns (stream SearchResult);

  // Synchronous search (for simple queries)
  rpc SearchSync(SearchRequest) returns (SearchResponse);

  // Similar document search
  rpc FindSimilar(SimilarRequest) returns (SearchResponse);
}

message SearchRequest {
  string query = 1;
  repeated string kb_ids = 2;
  int32 limit = 3;
  float min_score = 4;
  string user_id = 5;
  SearchOptions options = 6;
}

message SearchOptions {
  bool include_content = 1;
  bool include_metadata = 2;
  bool hybrid_search = 3;
  float keyword_weight = 4;
}

message SearchResult {
  string chunk_id = 1;
  string document_id = 2;
  string document_name = 3;
  string content = 4;
  float score = 5;
  map<string, string> metadata = 6;
  int32 chunk_index = 7;
  int32 total_chunks = 8;
}

message SearchResponse {
  repeated SearchResult results = 1;
  int32 total_count = 2;
  float search_time_ms = 3;
}

message SimilarRequest {
  string document_id = 1;
  string chunk_id = 2;
  int32 limit = 3;
  repeated string kb_ids = 4;
}

// ============================================================================
// GENERATION SERVICE
// ============================================================================

service GenerationService {
  // Streaming answer synthesis with citations
  rpc GenerateAnswer(GenerateAnswerRequest) returns (stream GenerateChunk);

  // Streaming document generation
  rpc GenerateDocument(GenerateDocumentRequest) returns (stream GenerateChunk);

  // Get available templates
  rpc ListTemplates(ListTemplatesRequest) returns (ListTemplatesResponse);
}

message GenerateAnswerRequest {
  string query = 1;
  repeated SearchResult context = 2;
  string model_id = 3;
  string user_id = 4;
  string conversation_id = 5;
  GenerationParams params = 6;
}

message GenerateDocumentRequest {
  string template_id = 1;
  string topic = 2;
  string additional_instructions = 3;
  repeated string kb_ids = 4;
  string model_id = 5;
  string user_id = 6;
  GenerationParams params = 7;
}

message GenerationParams {
  float temperature = 1;
  int32 max_tokens = 2;
  float top_p = 3;
  bool stream = 4;
}

message GenerateChunk {
  string content = 1;
  bool is_final = 2;
  repeated Citation citations = 3;
  ChunkType type = 4;
  string error = 5;
}

enum ChunkType {
  CHUNK_TYPE_UNSPECIFIED = 0;
  CHUNK_TYPE_TEXT = 1;
  CHUNK_TYPE_THINKING = 2;
  CHUNK_TYPE_CITATION = 3;
  CHUNK_TYPE_ERROR = 4;
  CHUNK_TYPE_DONE = 5;
}

message Citation {
  string document_id = 1;
  string document_name = 2;
  string chunk_id = 3;
  string quoted_text = 4;
  int32 start_offset = 5;
  int32 end_offset = 6;
  float relevance_score = 7;
}

message ListTemplatesRequest {
  string category = 1;
}

message ListTemplatesResponse {
  repeated Template templates = 1;
}

message Template {
  string id = 1;
  string name = 2;
  string description = 3;
  string category = 4;
  repeated string required_fields = 5;
}

// ============================================================================
// EMBEDDING SERVICE
// ============================================================================

service EmbeddingService {
  // Single text embedding
  rpc Embed(EmbedRequest) returns (EmbedResponse);

  // Batch embedding
  rpc EmbedBatch(EmbedBatchRequest) returns (EmbedBatchResponse);

  // Get model info
  rpc GetModelInfo(GetModelInfoRequest) returns (ModelInfo);
}

message EmbedRequest {
  string text = 1;
  string model_id = 2;
}

message EmbedResponse {
  repeated float embedding = 1;
  int32 dimensions = 2;
  int32 token_count = 3;
}

message EmbedBatchRequest {
  repeated string texts = 1;
  string model_id = 2;
}

message EmbedBatchResponse {
  repeated EmbedResponse embeddings = 1;
  int32 total_tokens = 2;
}

message GetModelInfoRequest {
  string model_id = 1;
}

message ModelInfo {
  string model_id = 1;
  string provider = 2;
  int32 dimensions = 3;
  int32 max_tokens = 4;
}

// ============================================================================
// CONVERSATION SERVICE
// ============================================================================

service ConversationService {
  // Get conversation history
  rpc GetHistory(GetHistoryRequest) returns (GetHistoryResponse);

  // Clear conversation
  rpc ClearHistory(ClearHistoryRequest) returns (ClearHistoryResponse);
}

message GetHistoryRequest {
  string conversation_id = 1;
  string user_id = 2;
  int32 limit = 3;
}

message GetHistoryResponse {
  repeated ConversationMessage messages = 1;
  string conversation_id = 2;
}

message ConversationMessage {
  string role = 1;
  string content = 2;
  google.protobuf.Timestamp timestamp = 3;
  repeated Citation citations = 4;
}

message ClearHistoryRequest {
  string conversation_id = 1;
  string user_id = 2;
}

message ClearHistoryResponse {
  bool success = 1;
}
```

### Go gRPC Client Implementation

**`internal/services/ai_client.go`:**

```go
package services

import (
    "context"
    "fmt"
    "io"
    "sync"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc/keepalive"

    pb "lumikb/api/gen"
)

// AIClient manages gRPC connections to Python AI services
type AIClient struct {
    conn          *grpc.ClientConn
    searchClient  pb.SearchServiceClient
    genClient     pb.GenerationServiceClient
    embedClient   pb.EmbeddingServiceClient
    convClient    pb.ConversationServiceClient

    mu            sync.RWMutex
    healthy       bool
}

// AIClientConfig holds connection configuration
type AIClientConfig struct {
    Address          string
    MaxRetries       int
    RetryBackoff     time.Duration
    KeepAliveTime    time.Duration
    KeepAliveTimeout time.Duration
    MaxRecvMsgSize   int
}

// DefaultAIClientConfig returns sensible defaults
func DefaultAIClientConfig() AIClientConfig {
    return AIClientConfig{
        Address:          "localhost:50051",
        MaxRetries:       3,
        RetryBackoff:     100 * time.Millisecond,
        KeepAliveTime:    10 * time.Second,
        KeepAliveTimeout: 3 * time.Second,
        MaxRecvMsgSize:   10 * 1024 * 1024, // 10MB
    }
}

// NewAIClient creates a new gRPC client connection
func NewAIClient(cfg AIClientConfig) (*AIClient, error) {
    opts := []grpc.DialOption{
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithDefaultCallOptions(
            grpc.MaxCallRecvMsgSize(cfg.MaxRecvMsgSize),
        ),
        grpc.WithKeepaliveParams(keepalive.ClientParameters{
            Time:                cfg.KeepAliveTime,
            Timeout:             cfg.KeepAliveTimeout,
            PermitWithoutStream: true,
        }),
    }

    conn, err := grpc.Dial(cfg.Address, opts...)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to AI service: %w", err)
    }

    return &AIClient{
        conn:         conn,
        searchClient: pb.NewSearchServiceClient(conn),
        genClient:    pb.NewGenerationServiceClient(conn),
        embedClient:  pb.NewEmbeddingServiceClient(conn),
        convClient:   pb.NewConversationServiceClient(conn),
        healthy:      true,
    }, nil
}

// Close closes the gRPC connection
func (c *AIClient) Close() error {
    return c.conn.Close()
}

// IsHealthy returns the health status
func (c *AIClient) IsHealthy() bool {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.healthy
}

// SearchSync performs a synchronous search
func (c *AIClient) SearchSync(ctx context.Context, req *pb.SearchRequest) (*pb.SearchResponse, error) {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    return c.searchClient.SearchSync(ctx, req)
}

// SearchResult represents a single search result for the channel
type SearchResultEvent struct {
    Result *pb.SearchResult
    Error  error
    Done   bool
}

// SearchStream returns a channel of streaming search results
func (c *AIClient) SearchStream(ctx context.Context, req *pb.SearchRequest) <-chan SearchResultEvent {
    events := make(chan SearchResultEvent, 100)

    go func() {
        defer close(events)

        stream, err := c.searchClient.Search(ctx, req)
        if err != nil {
            events <- SearchResultEvent{Error: err}
            return
        }

        for {
            result, err := stream.Recv()
            if err == io.EOF {
                events <- SearchResultEvent{Done: true}
                return
            }
            if err != nil {
                events <- SearchResultEvent{Error: err}
                return
            }
            events <- SearchResultEvent{Result: result}
        }
    }()

    return events
}

// GenerateChunkEvent represents a generation event for the channel
type GenerateChunkEvent struct {
    Chunk *pb.GenerateChunk
    Error error
    Done  bool
}

// GenerateAnswerStream returns streaming generation chunks
func (c *AIClient) GenerateAnswerStream(ctx context.Context, req *pb.GenerateAnswerRequest) <-chan GenerateChunkEvent {
    events := make(chan GenerateChunkEvent, 100)

    go func() {
        defer close(events)

        stream, err := c.genClient.GenerateAnswer(ctx, req)
        if err != nil {
            events <- GenerateChunkEvent{Error: err}
            return
        }

        for {
            chunk, err := stream.Recv()
            if err == io.EOF {
                events <- GenerateChunkEvent{Done: true}
                return
            }
            if err != nil {
                events <- GenerateChunkEvent{Error: err}
                return
            }
            events <- GenerateChunkEvent{Chunk: chunk}
        }
    }()

    return events
}

// GenerateDocumentStream returns streaming document generation
func (c *AIClient) GenerateDocumentStream(ctx context.Context, req *pb.GenerateDocumentRequest) <-chan GenerateChunkEvent {
    events := make(chan GenerateChunkEvent, 100)

    go func() {
        defer close(events)

        stream, err := c.genClient.GenerateDocument(ctx, req)
        if err != nil {
            events <- GenerateChunkEvent{Error: err}
            return
        }

        for {
            chunk, err := stream.Recv()
            if err == io.EOF {
                events <- GenerateChunkEvent{Done: true}
                return
            }
            if err != nil {
                events <- GenerateChunkEvent{Error: err}
                return
            }
            events <- GenerateChunkEvent{Chunk: chunk}
        }
    }()

    return events
}

// Embed generates embedding for a single text
func (c *AIClient) Embed(ctx context.Context, text, modelID string) (*pb.EmbedResponse, error) {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    return c.embedClient.Embed(ctx, &pb.EmbedRequest{
        Text:    text,
        ModelId: modelID,
    })
}

// EmbedBatch generates embeddings for multiple texts
func (c *AIClient) EmbedBatch(ctx context.Context, texts []string, modelID string) (*pb.EmbedBatchResponse, error) {
    ctx, cancel := context.WithTimeout(ctx, 60*time.Second)
    defer cancel()

    return c.embedClient.EmbedBatch(ctx, &pb.EmbedBatchRequest{
        Texts:   texts,
        ModelId: modelID,
    })
}

// ListTemplates returns available generation templates
func (c *AIClient) ListTemplates(ctx context.Context, category string) (*pb.ListTemplatesResponse, error) {
    ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
    defer cancel()

    return c.genClient.ListTemplates(ctx, &pb.ListTemplatesRequest{
        Category: category,
    })
}
```

### Python gRPC Server Implementation

**`backend/app/grpc/server.py`:**

```python
"""
Python gRPC Server for AI Services

Exposes SearchService, GenerationService, EmbeddingService, and ConversationService
for consumption by the Go API Gateway.
"""

import asyncio
import logging
from concurrent import futures
from typing import AsyncIterator

import grpc
from grpc import aio

from app.grpc import ai_services_pb2 as pb2
from app.grpc import ai_services_pb2_grpc as pb2_grpc
from app.services.search_service import SearchService
from app.services.generation_service import GenerationService
from app.services.conversation_service import ConversationService
from app.integrations.litellm_client import get_embedding
from app.core.config import settings
from app.core.database import get_async_session

logger = logging.getLogger(__name__)


class SearchServicer(pb2_grpc.SearchServiceServicer):
    """Implements the SearchService gRPC interface."""

    def __init__(self, search_service: SearchService):
        self.search_service = search_service

    async def Search(
        self,
        request: pb2.SearchRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[pb2.SearchResult]:
        """Streaming semantic search."""
        try:
            async for result in self.search_service.search_stream(
                query=request.query,
                kb_ids=list(request.kb_ids),
                limit=request.limit or 20,
                min_score=request.min_score or 0.0,
                include_content=request.options.include_content if request.options else True,
            ):
                yield pb2.SearchResult(
                    chunk_id=str(result.chunk_id),
                    document_id=str(result.document_id),
                    document_name=result.document_name or "",
                    content=result.content or "",
                    score=result.score,
                    metadata=result.metadata or {},
                    chunk_index=result.chunk_index or 0,
                    total_chunks=result.total_chunks or 0,
                )
        except Exception as e:
            logger.exception("Search stream error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

    async def SearchSync(
        self,
        request: pb2.SearchRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.SearchResponse:
        """Synchronous search returning all results at once."""
        try:
            import time
            start = time.time()

            results = await self.search_service.search(
                query=request.query,
                kb_ids=list(request.kb_ids),
                limit=request.limit or 20,
                min_score=request.min_score or 0.0,
            )

            elapsed_ms = (time.time() - start) * 1000

            return pb2.SearchResponse(
                results=[
                    pb2.SearchResult(
                        chunk_id=str(r.chunk_id),
                        document_id=str(r.document_id),
                        document_name=r.document_name or "",
                        content=r.content or "",
                        score=r.score,
                    )
                    for r in results
                ],
                total_count=len(results),
                search_time_ms=elapsed_ms,
            )
        except Exception as e:
            logger.exception("SearchSync error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.SearchResponse()

    async def FindSimilar(
        self,
        request: pb2.SimilarRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.SearchResponse:
        """Find documents similar to a given chunk."""
        try:
            results = await self.search_service.find_similar(
                document_id=request.document_id,
                chunk_id=request.chunk_id,
                limit=request.limit or 10,
                kb_ids=list(request.kb_ids) if request.kb_ids else None,
            )

            return pb2.SearchResponse(
                results=[
                    pb2.SearchResult(
                        chunk_id=str(r.chunk_id),
                        document_id=str(r.document_id),
                        content=r.content or "",
                        score=r.score,
                    )
                    for r in results
                ],
                total_count=len(results),
            )
        except Exception as e:
            logger.exception("FindSimilar error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.SearchResponse()


class GenerationServicer(pb2_grpc.GenerationServiceServicer):
    """Implements the GenerationService gRPC interface."""

    def __init__(self, gen_service: GenerationService):
        self.gen_service = gen_service

    async def GenerateAnswer(
        self,
        request: pb2.GenerateAnswerRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[pb2.GenerateChunk]:
        """Streaming answer generation with citations."""
        try:
            # Convert protobuf context to Python objects
            search_context = [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "document_name": r.document_name,
                    "content": r.content,
                    "score": r.score,
                }
                for r in request.context
            ]

            async for chunk in self.gen_service.generate_answer_stream(
                query=request.query,
                context=search_context,
                model_id=request.model_id,
                user_id=request.user_id,
                conversation_id=request.conversation_id or None,
                temperature=request.params.temperature if request.params else 0.7,
                max_tokens=request.params.max_tokens if request.params else 2048,
            ):
                yield pb2.GenerateChunk(
                    content=chunk.text,
                    is_final=chunk.is_final,
                    type=self._map_chunk_type(chunk.type),
                    citations=[
                        pb2.Citation(
                            document_id=c.document_id,
                            document_name=c.document_name,
                            chunk_id=c.chunk_id,
                            quoted_text=c.quoted_text,
                            relevance_score=c.relevance_score,
                        )
                        for c in (chunk.citations or [])
                    ],
                )
        except Exception as e:
            logger.exception("GenerateAnswer error")
            yield pb2.GenerateChunk(
                type=pb2.CHUNK_TYPE_ERROR,
                error=str(e),
                is_final=True,
            )

    async def GenerateDocument(
        self,
        request: pb2.GenerateDocumentRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[pb2.GenerateChunk]:
        """Streaming document generation."""
        try:
            async for chunk in self.gen_service.generate_document_stream(
                template_id=request.template_id,
                topic=request.topic,
                additional_instructions=request.additional_instructions,
                kb_ids=list(request.kb_ids),
                model_id=request.model_id,
                user_id=request.user_id,
            ):
                yield pb2.GenerateChunk(
                    content=chunk.text,
                    is_final=chunk.is_final,
                    type=self._map_chunk_type(chunk.type),
                    citations=[
                        pb2.Citation(
                            document_id=c.document_id,
                            document_name=c.document_name,
                            chunk_id=c.chunk_id,
                            quoted_text=c.quoted_text,
                        )
                        for c in (chunk.citations or [])
                    ],
                )
        except Exception as e:
            logger.exception("GenerateDocument error")
            yield pb2.GenerateChunk(
                type=pb2.CHUNK_TYPE_ERROR,
                error=str(e),
                is_final=True,
            )

    async def ListTemplates(
        self,
        request: pb2.ListTemplatesRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.ListTemplatesResponse:
        """List available generation templates."""
        try:
            templates = await self.gen_service.list_templates(
                category=request.category or None
            )

            return pb2.ListTemplatesResponse(
                templates=[
                    pb2.Template(
                        id=t.id,
                        name=t.name,
                        description=t.description,
                        category=t.category,
                        required_fields=t.required_fields,
                    )
                    for t in templates
                ]
            )
        except Exception as e:
            logger.exception("ListTemplates error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.ListTemplatesResponse()

    def _map_chunk_type(self, chunk_type: str) -> int:
        """Map internal chunk type to protobuf enum."""
        mapping = {
            "text": pb2.CHUNK_TYPE_TEXT,
            "thinking": pb2.CHUNK_TYPE_THINKING,
            "citation": pb2.CHUNK_TYPE_CITATION,
            "error": pb2.CHUNK_TYPE_ERROR,
            "done": pb2.CHUNK_TYPE_DONE,
        }
        return mapping.get(chunk_type, pb2.CHUNK_TYPE_UNSPECIFIED)


class EmbeddingServicer(pb2_grpc.EmbeddingServiceServicer):
    """Implements the EmbeddingService gRPC interface."""

    async def Embed(
        self,
        request: pb2.EmbedRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.EmbedResponse:
        """Generate embedding for a single text."""
        try:
            embedding = await get_embedding(
                text=request.text,
                model_id=request.model_id,
            )

            return pb2.EmbedResponse(
                embedding=embedding.vector,
                dimensions=len(embedding.vector),
                token_count=embedding.token_count,
            )
        except Exception as e:
            logger.exception("Embed error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.EmbedResponse()

    async def EmbedBatch(
        self,
        request: pb2.EmbedBatchRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.EmbedBatchResponse:
        """Generate embeddings for multiple texts."""
        try:
            embeddings = await get_embedding_batch(
                texts=list(request.texts),
                model_id=request.model_id,
            )

            total_tokens = sum(e.token_count for e in embeddings)

            return pb2.EmbedBatchResponse(
                embeddings=[
                    pb2.EmbedResponse(
                        embedding=e.vector,
                        dimensions=len(e.vector),
                        token_count=e.token_count,
                    )
                    for e in embeddings
                ],
                total_tokens=total_tokens,
            )
        except Exception as e:
            logger.exception("EmbedBatch error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.EmbedBatchResponse()

    async def GetModelInfo(
        self,
        request: pb2.GetModelInfoRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.ModelInfo:
        """Get embedding model information."""
        try:
            info = await get_model_info(request.model_id)

            return pb2.ModelInfo(
                model_id=info.model_id,
                provider=info.provider,
                dimensions=info.dimensions,
                max_tokens=info.max_tokens,
            )
        except Exception as e:
            logger.exception("GetModelInfo error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.ModelInfo()


class ConversationServicer(pb2_grpc.ConversationServiceServicer):
    """Implements the ConversationService gRPC interface."""

    def __init__(self, conv_service: ConversationService):
        self.conv_service = conv_service

    async def GetHistory(
        self,
        request: pb2.GetHistoryRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.GetHistoryResponse:
        """Get conversation history."""
        try:
            history = await self.conv_service.get_history(
                conversation_id=request.conversation_id,
                user_id=request.user_id,
                limit=request.limit or 50,
            )

            return pb2.GetHistoryResponse(
                messages=[
                    pb2.ConversationMessage(
                        role=m.role,
                        content=m.content,
                        # timestamp=... (protobuf timestamp conversion)
                    )
                    for m in history.messages
                ],
                conversation_id=history.conversation_id,
            )
        except Exception as e:
            logger.exception("GetHistory error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.GetHistoryResponse()

    async def ClearHistory(
        self,
        request: pb2.ClearHistoryRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.ClearHistoryResponse:
        """Clear conversation history."""
        try:
            await self.conv_service.clear_history(
                conversation_id=request.conversation_id,
                user_id=request.user_id,
            )

            return pb2.ClearHistoryResponse(success=True)
        except Exception as e:
            logger.exception("ClearHistory error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.ClearHistoryResponse(success=False)


async def serve(port: int = 50051):
    """Start the gRPC server."""
    server = aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10MB
            ('grpc.max_send_message_length', 10 * 1024 * 1024),
        ],
    )

    # Initialize services
    search_service = SearchService()
    gen_service = GenerationService()
    conv_service = ConversationService()

    # Register servicers
    pb2_grpc.add_SearchServiceServicer_to_server(
        SearchServicer(search_service), server
    )
    pb2_grpc.add_GenerationServiceServicer_to_server(
        GenerationServicer(gen_service), server
    )
    pb2_grpc.add_EmbeddingServiceServicer_to_server(
        EmbeddingServicer(), server
    )
    pb2_grpc.add_ConversationServiceServicer_to_server(
        ConversationServicer(conv_service), server
    )

    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(grace=5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
```

---

## Authentication & Authorization

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "is_superuser": false,
  "permission_level": 2,
  "groups": ["operators", "users"],
  "iat": 1702123456,
  "exp": 1702209856,
  "aud": ["lumikb-api"]
}
```

### Go Auth Implementation

**`internal/auth/jwt.go`:**

```go
package auth

import (
    "errors"
    "time"

    "github.com/golang-jwt/jwt/v5"
)

var (
    ErrInvalidToken = errors.New("invalid token")
    ErrExpiredToken = errors.New("token expired")
)

type Claims struct {
    UserID          string   `json:"sub"`
    Email           string   `json:"email"`
    IsSuperuser     bool     `json:"is_superuser"`
    PermissionLevel int      `json:"permission_level"`
    Groups          []string `json:"groups"`
    jwt.RegisteredClaims
}

type JWTService struct {
    secretKey     []byte
    tokenDuration time.Duration
    issuer        string
    audience      []string
}

func NewJWTService(secret string, duration time.Duration) *JWTService {
    return &JWTService{
        secretKey:     []byte(secret),
        tokenDuration: duration,
        issuer:        "lumikb",
        audience:      []string{"lumikb-api"},
    }
}

func (s *JWTService) GenerateToken(user *User) (string, error) {
    now := time.Now()

    claims := Claims{
        UserID:          user.ID.String(),
        Email:           user.Email,
        IsSuperuser:     user.IsSuperuser,
        PermissionLevel: user.PermissionLevel,
        Groups:          user.Groups,
        RegisteredClaims: jwt.RegisteredClaims{
            Issuer:    s.issuer,
            Subject:   user.ID.String(),
            Audience:  s.audience,
            ExpiresAt: jwt.NewNumericDate(now.Add(s.tokenDuration)),
            IssuedAt:  jwt.NewNumericDate(now),
            NotBefore: jwt.NewNumericDate(now),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secretKey)
}

func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, ErrInvalidToken
        }
        return s.secretKey, nil
    })

    if err != nil {
        if errors.Is(err, jwt.ErrTokenExpired) {
            return nil, ErrExpiredToken
        }
        return nil, ErrInvalidToken
    }

    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, ErrInvalidToken
    }

    return claims, nil
}

func (s *JWTService) RefreshToken(claims *Claims) (string, error) {
    // Create new token with extended expiry
    claims.ExpiresAt = jwt.NewNumericDate(time.Now().Add(s.tokenDuration))
    claims.IssuedAt = jwt.NewNumericDate(time.Now())

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secretKey)
}
```

**`internal/auth/middleware.go`:**

```go
package auth

import (
    "context"
    "net/http"
    "strings"
)

type contextKey string

const userContextKey contextKey = "user"

// AuthMiddleware validates JWT tokens
func (s *JWTService) AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Try cookie first, then Authorization header
        var tokenString string

        if cookie, err := r.Cookie("lumikb_auth"); err == nil {
            tokenString = cookie.Value
        } else if auth := r.Header.Get("Authorization"); auth != "" {
            if strings.HasPrefix(auth, "Bearer ") {
                tokenString = strings.TrimPrefix(auth, "Bearer ")
            }
        }

        if tokenString == "" {
            http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
            return
        }

        claims, err := s.ValidateToken(tokenString)
        if err != nil {
            http.Error(w, `{"error":"invalid token"}`, http.StatusUnauthorized)
            return
        }

        // Add claims to context
        ctx := context.WithValue(r.Context(), userContextKey, claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// RequirePermission checks user permission level
func RequirePermission(level int) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            claims := UserFromContext(r.Context())
            if claims == nil {
                http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
                return
            }

            if claims.PermissionLevel < level {
                http.Error(w, `{"error":"forbidden"}`, http.StatusForbidden)
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

// RequireSuperuser checks for superuser status
func RequireSuperuser(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        claims := UserFromContext(r.Context())
        if claims == nil || !claims.IsSuperuser {
            http.Error(w, `{"error":"forbidden"}`, http.StatusForbidden)
            return
        }
        next.ServeHTTP(w, r)
    })
}

// UserFromContext extracts user claims from context
func UserFromContext(ctx context.Context) *Claims {
    claims, ok := ctx.Value(userContextKey).(*Claims)
    if !ok {
        return nil
    }
    return claims
}
```

---

## API Endpoints Migration

### Route Mapping (Python → Go)

| Endpoint | Python Handler | Go Handler | Auth Required |
|----------|---------------|------------|---------------|
| `POST /api/v1/auth/login` | `auth.py:login` | `handlers/auth.go:Login` | No |
| `POST /api/v1/auth/register` | `auth.py:register` | `handlers/auth.go:Register` | No |
| `POST /api/v1/auth/logout` | `auth.py:logout` | `handlers/auth.go:Logout` | Yes |
| `GET /api/v1/users/me` | `users.py:get_me` | `handlers/users.go:GetMe` | Yes |
| `GET /api/v1/admin/users` | `admin.py:list_users` | `handlers/users.go:List` | Admin |
| `POST /api/v1/admin/users` | `admin.py:create_user` | `handlers/users.go:Create` | Admin |
| `PATCH /api/v1/admin/users/{id}` | `admin.py:update_user` | `handlers/users.go:Update` | Admin |
| `GET /api/v1/knowledge-bases` | `knowledge_bases.py:list` | `handlers/kb.go:List` | Yes |
| `POST /api/v1/knowledge-bases` | `knowledge_bases.py:create` | `handlers/kb.go:Create` | Operator+ |
| `DELETE /api/v1/knowledge-bases/{id}` | `knowledge_bases.py:delete` | `handlers/kb.go:Delete` | Admin |
| `GET /api/v1/admin/audit/logs` | `admin.py:query_logs` | `handlers/audit.go:QueryLogs` | Admin |
| `POST /api/v1/admin/audit/export` | `admin.py:export_logs` | `handlers/audit.go:Export` | Admin |
| `GET /api/v1/admin/queue/status` | `admin.py:queue_status` | `handlers/queue.go:Status` | Operator+ |
| `GET /api/v1/admin/config` | `admin.py:get_config` | `handlers/config.go:Get` | Admin |
| `PUT /api/v1/admin/config` | `admin.py:update_config` | `handlers/config.go:Update` | Admin |
| `GET /api/v1/search` | `search.py:search` | `handlers/search.go:SearchSSE` | Yes (Proxy) |
| `POST /api/v1/chat` | `chat.py:chat` | `handlers/chat.go:ChatSSE` | Yes (Proxy) |
| `POST /api/v1/generate` | `generate.py:generate` | `handlers/generation.go:GenerateSSE` | Yes (Proxy) |

### Go Router Setup

**`cmd/api/main.go`:**

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/go-chi/cors"

    "lumikb/internal/auth"
    "lumikb/internal/config"
    "lumikb/internal/database"
    "lumikb/internal/handlers"
    "lumikb/internal/services"
    mw "lumikb/internal/middleware"
)

func main() {
    // Load configuration
    cfg, err := config.Load()
    if err != nil {
        log.Fatalf("Failed to load config: %v", err)
    }

    // Initialize database
    db, err := database.New(cfg.DatabaseURL)
    if err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    // Initialize AI client (gRPC to Python)
    aiClient, err := services.NewAIClient(services.AIClientConfig{
        Address: cfg.AIServiceAddr,
    })
    if err != nil {
        log.Fatalf("Failed to connect to AI service: %v", err)
    }
    defer aiClient.Close()

    // Initialize services
    jwtService := auth.NewJWTService(cfg.JWTSecret, 24*time.Hour)
    userService := services.NewUserService(db)
    auditService := services.NewAuditService(db)
    kbService := services.NewKBService(db)

    // Initialize handlers
    authHandler := handlers.NewAuthHandler(userService, jwtService)
    userHandler := handlers.NewUserHandler(userService, auditService)
    kbHandler := handlers.NewKBHandler(kbService, auditService)
    auditHandler := handlers.NewAuditHandler(auditService)
    searchHandler := handlers.NewSearchHandler(aiClient)
    genHandler := handlers.NewGenerationHandler(aiClient)

    // Setup router
    r := chi.NewRouter()

    // Global middleware
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(mw.StructuredLogger)
    r.Use(middleware.Recoverer)
    r.Use(mw.PrometheusMetrics)
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   cfg.CORSOrigins,
        AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-Request-ID"},
        AllowCredentials: true,
        MaxAge:           300,
    }))

    // Health check (no auth)
    r.Get("/health", handlers.HealthCheck)
    r.Get("/ready", handlers.ReadinessCheck(db, aiClient))

    // API v1 routes
    r.Route("/api/v1", func(r chi.Router) {
        // Public routes (no auth)
        r.Route("/auth", func(r chi.Router) {
            r.Post("/login", authHandler.Login)
            r.Post("/register", authHandler.Register)
            r.Post("/forgot-password", authHandler.ForgotPassword)
            r.Post("/reset-password", authHandler.ResetPassword)
        })

        // Authenticated routes
        r.Group(func(r chi.Router) {
            r.Use(jwtService.AuthMiddleware)

            // Auth actions
            r.Post("/auth/logout", authHandler.Logout)
            r.Post("/auth/refresh", authHandler.Refresh)

            // User profile
            r.Get("/users/me", userHandler.GetMe)
            r.Patch("/users/me", userHandler.UpdateMe)
            r.Post("/users/me/password", userHandler.ChangePassword)

            // Knowledge Bases
            r.Route("/knowledge-bases", func(r chi.Router) {
                r.Get("/", kbHandler.List)
                r.With(auth.RequirePermission(2)).Post("/", kbHandler.Create)
                r.Route("/{kb_id}", func(r chi.Router) {
                    r.Get("/", kbHandler.Get)
                    r.With(auth.RequirePermission(2)).Patch("/", kbHandler.Update)
                    r.With(auth.RequirePermission(3)).Delete("/", kbHandler.Delete)
                    r.Get("/documents", kbHandler.ListDocuments)
                })
            })

            // Search (proxied to Python)
            r.Get("/search", searchHandler.SearchSSE)
            r.Get("/search/similar", searchHandler.SimilarSSE)

            // Chat (proxied to Python)
            r.Post("/chat", genHandler.ChatSSE)
            r.Get("/chat/history", genHandler.GetHistory)
            r.Delete("/chat/history", genHandler.ClearHistory)

            // Generation (proxied to Python)
            r.Post("/generate", genHandler.GenerateSSE)
            r.Get("/templates", genHandler.ListTemplates)

            // Operations routes (Operator+)
            r.Route("/operations", func(r chi.Router) {
                r.Use(auth.RequirePermission(2))
                r.Get("/queue/status", auditHandler.QueueStatus)
                r.Get("/audit/logs", auditHandler.QueryLogs)
            })

            // Admin routes
            r.Route("/admin", func(r chi.Router) {
                r.Use(auth.RequireSuperuser)

                // User management
                r.Get("/users", userHandler.List)
                r.Post("/users", userHandler.Create)
                r.Patch("/users/{user_id}", userHandler.Update)

                // Audit
                r.Post("/audit/logs", auditHandler.QueryLogs)
                r.Post("/audit/export", auditHandler.Export)

                // Config
                r.Get("/config", handlers.GetConfig)
                r.Put("/config", handlers.UpdateConfig)

                // Stats
                r.Get("/stats", handlers.GetAdminStats)
            })
        })
    })

    // Start server
    srv := &http.Server{
        Addr:         cfg.ListenAddr,
        Handler:      r,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 60 * time.Second, // Longer for SSE
        IdleTimeout:  60 * time.Second,
    }

    // Graceful shutdown
    go func() {
        sigint := make(chan os.Signal, 1)
        signal.Notify(sigint, syscall.SIGINT, syscall.SIGTERM)
        <-sigint

        log.Println("Shutting down server...")
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()

        if err := srv.Shutdown(ctx); err != nil {
            log.Printf("HTTP server shutdown error: %v", err)
        }
    }()

    log.Printf("Starting server on %s", cfg.ListenAddr)
    if err := srv.ListenAndServe(); err != http.ErrServerClosed {
        log.Fatalf("HTTP server error: %v", err)
    }
}
```

---

## Streaming Implementation

### SSE Handler for Search

**`internal/handlers/search.go`:**

```go
package handlers

import (
    "encoding/json"
    "fmt"
    "net/http"
    "strconv"

    pb "lumikb/api/gen"
    "lumikb/internal/auth"
    "lumikb/internal/services"
)

type SearchHandler struct {
    aiClient *services.AIClient
}

func NewSearchHandler(aiClient *services.AIClient) *SearchHandler {
    return &SearchHandler{aiClient: aiClient}
}

// SearchSSE handles streaming search via Server-Sent Events
func (h *SearchHandler) SearchSSE(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    claims := auth.UserFromContext(ctx)

    // Parse query parameters
    query := r.URL.Query().Get("query")
    if query == "" {
        http.Error(w, `{"error":"query is required"}`, http.StatusBadRequest)
        return
    }

    kbIDs := r.URL.Query()["kb_ids"]
    limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
    if limit == 0 {
        limit = 20
    }

    // Set SSE headers
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")
    w.Header().Set("X-Accel-Buffering", "no") // Disable nginx buffering

    flusher, ok := w.(http.Flusher)
    if !ok {
        http.Error(w, `{"error":"streaming not supported"}`, http.StatusInternalServerError)
        return
    }

    // Build gRPC request
    req := &pb.SearchRequest{
        Query:  query,
        KbIds:  kbIDs,
        Limit:  int32(limit),
        UserId: claims.UserID,
    }

    // Stream results from Python service
    events := h.aiClient.SearchStream(ctx, req)

    for event := range events {
        if event.Error != nil {
            data, _ := json.Marshal(map[string]string{"error": event.Error.Error()})
            fmt.Fprintf(w, "event: error\ndata: %s\n\n", data)
            flusher.Flush()
            return
        }

        if event.Done {
            fmt.Fprintf(w, "event: done\ndata: {}\n\n")
            flusher.Flush()
            return
        }

        if event.Result != nil {
            data, _ := json.Marshal(map[string]interface{}{
                "chunk_id":      event.Result.ChunkId,
                "document_id":   event.Result.DocumentId,
                "document_name": event.Result.DocumentName,
                "content":       event.Result.Content,
                "score":         event.Result.Score,
                "metadata":      event.Result.Metadata,
            })
            fmt.Fprintf(w, "event: result\ndata: %s\n\n", data)
            flusher.Flush()
        }
    }
}

// SimilarSSE handles streaming similar document search
func (h *SearchHandler) SimilarSSE(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    documentID := r.URL.Query().Get("document_id")
    chunkID := r.URL.Query().Get("chunk_id")

    if documentID == "" {
        http.Error(w, `{"error":"document_id is required"}`, http.StatusBadRequest)
        return
    }

    limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
    if limit == 0 {
        limit = 10
    }

    // For similar search, we use sync API (typically fewer results)
    resp, err := h.aiClient.SearchClient().FindSimilar(ctx, &pb.SimilarRequest{
        DocumentId: documentID,
        ChunkId:    chunkID,
        Limit:      int32(limit),
    })

    if err != nil {
        http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]interface{}{
        "results":     resp.Results,
        "total_count": resp.TotalCount,
    })
}
```

### SSE Handler for Generation

**`internal/handlers/generation.go`:**

```go
package handlers

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"

    pb "lumikb/api/gen"
    "lumikb/internal/auth"
    "lumikb/internal/services"
)

type GenerationHandler struct {
    aiClient *services.AIClient
}

func NewGenerationHandler(aiClient *services.AIClient) *GenerationHandler {
    return &GenerationHandler{aiClient: aiClient}
}

// ChatSSE handles streaming chat responses
func (h *GenerationHandler) ChatSSE(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    claims := auth.UserFromContext(ctx)

    // Parse request body
    var reqBody struct {
        Query          string   `json:"query"`
        KBIDs          []string `json:"kb_ids"`
        ModelID        string   `json:"model_id"`
        ConversationID string   `json:"conversation_id"`
    }
    if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
        http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
        return
    }

    // First: get search results for context
    searchResp, err := h.aiClient.SearchSync(ctx, &pb.SearchRequest{
        Query:  reqBody.Query,
        KbIds:  reqBody.KBIDs,
        Limit:  10,
        UserId: claims.UserID,
    })
    if err != nil {
        http.Error(w, fmt.Sprintf(`{"error":"search failed: %s"}`, err.Error()), http.StatusInternalServerError)
        return
    }

    // Set SSE headers
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")
    w.Header().Set("X-Accel-Buffering", "no")

    flusher := w.(http.Flusher)

    // Send search context first
    contextData, _ := json.Marshal(map[string]interface{}{
        "type":    "context",
        "results": searchResp.Results,
    })
    fmt.Fprintf(w, "event: context\ndata: %s\n\n", contextData)
    flusher.Flush()

    // Call generation service
    genReq := &pb.GenerateAnswerRequest{
        Query:          reqBody.Query,
        Context:        searchResp.Results,
        ModelId:        reqBody.ModelID,
        UserId:         claims.UserID,
        ConversationId: reqBody.ConversationID,
    }

    events := h.aiClient.GenerateAnswerStream(ctx, genReq)

    for event := range events {
        if event.Error != nil {
            data, _ := json.Marshal(map[string]string{"error": event.Error.Error()})
            fmt.Fprintf(w, "event: error\ndata: %s\n\n", data)
            flusher.Flush()
            return
        }

        if event.Done {
            fmt.Fprintf(w, "event: done\ndata: {}\n\n")
            flusher.Flush()
            return
        }

        if event.Chunk != nil {
            data, _ := json.Marshal(map[string]interface{}{
                "content":   event.Chunk.Content,
                "type":      event.Chunk.Type.String(),
                "is_final":  event.Chunk.IsFinal,
                "citations": convertCitations(event.Chunk.Citations),
            })
            fmt.Fprintf(w, "event: chunk\ndata: %s\n\n", data)
            flusher.Flush()
        }
    }
}

// GenerateSSE handles streaming document generation
func (h *GenerationHandler) GenerateSSE(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    claims := auth.UserFromContext(ctx)

    var reqBody struct {
        TemplateID             string   `json:"template_id"`
        Topic                  string   `json:"topic"`
        AdditionalInstructions string   `json:"additional_instructions"`
        KBIDs                  []string `json:"kb_ids"`
        ModelID                string   `json:"model_id"`
    }
    if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
        http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
        return
    }

    // Set SSE headers
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")
    w.Header().Set("X-Accel-Buffering", "no")

    flusher := w.(http.Flusher)

    genReq := &pb.GenerateDocumentRequest{
        TemplateId:             reqBody.TemplateID,
        Topic:                  reqBody.Topic,
        AdditionalInstructions: reqBody.AdditionalInstructions,
        KbIds:                  reqBody.KBIDs,
        ModelId:                reqBody.ModelID,
        UserId:                 claims.UserID,
    }

    events := h.aiClient.GenerateDocumentStream(ctx, genReq)

    for event := range events {
        if event.Error != nil {
            data, _ := json.Marshal(map[string]string{"error": event.Error.Error()})
            fmt.Fprintf(w, "event: error\ndata: %s\n\n", data)
            flusher.Flush()
            return
        }

        if event.Done {
            fmt.Fprintf(w, "event: done\ndata: {}\n\n")
            flusher.Flush()
            return
        }

        if event.Chunk != nil {
            data, _ := json.Marshal(map[string]interface{}{
                "content":   event.Chunk.Content,
                "type":      event.Chunk.Type.String(),
                "is_final":  event.Chunk.IsFinal,
                "citations": convertCitations(event.Chunk.Citations),
            })
            fmt.Fprintf(w, "event: chunk\ndata: %s\n\n", data)
            flusher.Flush()
        }
    }
}

// ListTemplates returns available generation templates
func (h *GenerationHandler) ListTemplates(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    category := r.URL.Query().Get("category")

    resp, err := h.aiClient.ListTemplates(ctx, category)
    if err != nil {
        http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]interface{}{
        "templates": resp.Templates,
    })
}

func convertCitations(pbCitations []*pb.Citation) []map[string]interface{} {
    citations := make([]map[string]interface{}, len(pbCitations))
    for i, c := range pbCitations {
        citations[i] = map[string]interface{}{
            "document_id":     c.DocumentId,
            "document_name":   c.DocumentName,
            "chunk_id":        c.ChunkId,
            "quoted_text":     c.QuotedText,
            "relevance_score": c.RelevanceScore,
        }
    }
    return citations
}
```

---

## Database Access

### sqlc Configuration

**`sqlc.yaml`:**

```yaml
version: "2"
sql:
  - engine: "postgresql"
    queries: "internal/database/queries/*.sql"
    schema: "migrations/"
    gen:
      go:
        package: "db"
        out: "internal/database/gen"
        sql_package: "pgx/v5"
        emit_json_tags: true
        emit_empty_slices: true
        emit_pointers_for_null_types: true
        overrides:
          - db_type: "uuid"
            go_type: "github.com/google/uuid.UUID"
          - db_type: "timestamptz"
            go_type: "time.Time"
```

### Sample Queries

**`internal/database/queries/users.sql`:**

```sql
-- name: GetUserByID :one
SELECT id, email, hashed_password, is_active, is_superuser, is_verified,
       first_name, last_name, created_at, updated_at
FROM users
WHERE id = $1;

-- name: GetUserByEmail :one
SELECT id, email, hashed_password, is_active, is_superuser, is_verified,
       first_name, last_name, created_at, updated_at
FROM users
WHERE email = $1;

-- name: CreateUser :one
INSERT INTO users (id, email, hashed_password, is_active, is_superuser, first_name, last_name)
VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING *;

-- name: UpdateUser :one
UPDATE users
SET email = COALESCE(sqlc.narg(email), email),
    first_name = COALESCE(sqlc.narg(first_name), first_name),
    last_name = COALESCE(sqlc.narg(last_name), last_name),
    is_active = COALESCE(sqlc.narg(is_active), is_active),
    is_superuser = COALESCE(sqlc.narg(is_superuser), is_superuser),
    updated_at = NOW()
WHERE id = $1
RETURNING *;

-- name: ListUsers :many
SELECT id, email, is_active, is_superuser, is_verified,
       first_name, last_name, created_at, updated_at
FROM users
ORDER BY created_at DESC
LIMIT $1 OFFSET $2;

-- name: CountUsers :one
SELECT COUNT(*) FROM users;

-- name: GetUserPermissionLevel :one
SELECT COALESCE(MAX(g.permission_level), 1) as permission_level
FROM user_groups ug
JOIN groups g ON g.id = ug.group_id
WHERE ug.user_id = $1;

-- name: GetUserGroups :many
SELECT g.id, g.name, g.permission_level, g.is_system
FROM groups g
JOIN user_groups ug ON ug.group_id = g.id
WHERE ug.user_id = $1;
```

---

## Docker Deployment

### Docker Compose

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # Go API Gateway
  api-gateway:
    build:
      context: ./go-api
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - LISTEN_ADDR=:8080
      - DATABASE_URL=postgres://lumikb:lumikb_dev_password@postgres:5432/lumikb?sslmode=disable
      - REDIS_URL=redis://redis:6379/0
      - AI_SERVICE_ADDR=ai-service:50051
      - JWT_SECRET=${JWT_SECRET:-super-secret-key-change-in-production}
      - CORS_ORIGINS=http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      ai-service:
        condition: service_started
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Python AI Services (gRPC)
  ai-service:
    build:
      context: ./backend
      dockerfile: Dockerfile.grpc
    ports:
      - "50051:50051"
    environment:
      - DATABASE_URL=postgresql+asyncpg://lumikb:lumikb_dev_password@postgres:5432/lumikb
      - QDRANT_URL=http://qdrant:6333
      - LITELLM_API_BASE=http://litellm:4000
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
      litellm:
        condition: service_started

  # Python Celery Worker
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://lumikb:lumikb_dev_password@postgres:5432/lumikb
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - QDRANT_URL=http://qdrant:6333
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      qdrant:
        condition: service_started

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8080
    depends_on:
      - api-gateway

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=lumikb
      - POSTGRES_PASSWORD=lumikb_dev_password
      - POSTGRES_DB=lumikb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lumikb"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Qdrant Vector DB
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

  # MinIO Object Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  # LiteLLM
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    volumes:
      - ./infrastructure/docker/litellm_config.yaml:/app/config.yaml
    ports:
      - "4000:4000"
    command: ["--config", "/app/config.yaml"]

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

### Go Dockerfile

**`go-api/Dockerfile`:**

```dockerfile
# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /api ./cmd/api

# Runtime stage
FROM alpine:3.19

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Copy binary from builder
COPY --from=builder /api /app/api

# Create non-root user
RUN adduser -D -g '' appuser
USER appuser

EXPOSE 8080

ENTRYPOINT ["/app/api"]
```

### Python gRPC Dockerfile

**`backend/Dockerfile.grpc`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ ./app/

# Generate gRPC code
COPY api/proto/ ./api/proto/
RUN python -m grpc_tools.protoc \
    -I./api/proto \
    --python_out=./app/grpc \
    --grpc_python_out=./app/grpc \
    ./api/proto/ai_services.proto

EXPOSE 50051

CMD ["python", "-m", "app.grpc.server"]
```

---

## Migration Strategy

### Phase 1: Parallel Operation (Week 1-2)

1. Deploy Go API Gateway alongside Python FastAPI
2. Use nginx to route traffic:
   - `/api/v1/auth/*` → Go Gateway
   - All other routes → Python FastAPI
3. Monitor error rates and latency

### Phase 2: Incremental Migration (Week 3-4)

1. Migrate User Management endpoints
2. Migrate Audit endpoints
3. Migrate KB CRUD endpoints
4. Each migration includes:
   - Contract tests (same responses)
   - Performance benchmarks
   - Rollback plan

### Phase 3: Full Cutover (Week 5-6)

1. Route all traffic through Go Gateway
2. Python only receives gRPC from Go
3. Remove direct Python HTTP exposure
4. Update monitoring dashboards

### Rollback Plan

```bash
# If issues arise:
# 1. Update nginx to route back to Python
nginx -s reload

# 2. Scale down Go service
docker-compose scale api-gateway=0

# 3. Scale up Python API
docker-compose scale api=2
```

---

## Testing Strategy

### Unit Tests (Go)

```go
// internal/auth/jwt_test.go
func TestJWTService_GenerateAndValidate(t *testing.T) {
    svc := NewJWTService("test-secret", time.Hour)

    user := &User{
        ID:              uuid.New(),
        Email:           "test@example.com",
        IsSuperuser:     false,
        PermissionLevel: 2,
    }

    token, err := svc.GenerateToken(user)
    require.NoError(t, err)
    require.NotEmpty(t, token)

    claims, err := svc.ValidateToken(token)
    require.NoError(t, err)
    assert.Equal(t, user.ID.String(), claims.UserID)
    assert.Equal(t, user.Email, claims.Email)
    assert.Equal(t, 2, claims.PermissionLevel)
}
```

### Integration Tests

```go
// internal/handlers/search_test.go
func TestSearchSSE_Integration(t *testing.T) {
    // Start test gRPC server (mock)
    mockServer := startMockAIServer(t)
    defer mockServer.Stop()

    // Create handler
    client, _ := services.NewAIClient(services.AIClientConfig{
        Address: mockServer.Addr(),
    })
    handler := NewSearchHandler(client)

    // Create request
    req := httptest.NewRequest("GET", "/search?query=test&kb_ids=kb1", nil)
    req = req.WithContext(auth.ContextWithUser(req.Context(), testClaims))

    // Record response
    rec := httptest.NewRecorder()
    handler.SearchSSE(rec, req)

    // Verify SSE format
    assert.Equal(t, "text/event-stream", rec.Header().Get("Content-Type"))
    assert.Contains(t, rec.Body.String(), "event: result")
    assert.Contains(t, rec.Body.String(), "event: done")
}
```

### Contract Tests

```bash
# Run same tests against both Python and Go APIs
API_URL=http://localhost:8000 pytest tests/contract/
API_URL=http://localhost:8080 pytest tests/contract/
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| gRPC connection failures | Medium | High | Retry with backoff, circuit breaker |
| JWT incompatibility | Low | High | Shared secret, same algorithm |
| Database schema drift | Low | Medium | Single migration source (Alembic) |
| Performance regression | Low | Medium | Benchmark before/after |
| SSE streaming issues | Medium | Medium | Extensive browser testing |

---

## Implementation Roadmap

| Sprint | Focus | Deliverables |
|--------|-------|--------------|
| Sprint 1 | Go Foundation | Project structure, config, DB, auth |
| Sprint 2 | User Management | Registration, login, JWT, user CRUD |
| Sprint 3 | gRPC Integration | Proto definitions, Python server, Go client |
| Sprint 4 | Proxy Handlers | Search SSE, Generation SSE |
| Sprint 5 | KB & Audit | KB CRUD, audit endpoints |
| Sprint 6 | Production Ready | Metrics, logging, health checks, docs |

---

## References

- [System Overview](01-system-overview.md)
- [Technology Stack](02-technology-stack.md)
- [LLM Configuration](03-llm-configuration.md)
- [Data & API](06-data-and-api.md)
- [Security](07-security.md)
- [Deployment](08-deployment.md)

---

*Document Version: 1.0*
*Last Updated: 2025-12-09*
*Status: Proposed*
