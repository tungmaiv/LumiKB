# RAG Knowledge Base Management Platform – Solution Blueprint

## 1. High-Level Architecture

This solution outlines an enterprise‑grade, headless, modular RAG system with support for hybrid retrieval, multi‑agent workflow orchestration, and strong RBAC security.

### Architecture Layers
- **Frontend (Next.js)**: KB management, Admin dashboard, Chat UI
- **API Gateway (FastAPI/Go Gin)**: JWT auth, RBAC middleware, REST APIs
- **Orchestration Layer (LangGraph)**: Stateful AI workflow engine
- **Agent Layer**:
  - Ingestion Agent
  - Text Splitter Agent
  - Embedding Agent
  - Hybrid Retrieval Agent
  - Knowledge Base Manager Agent
  - User & RBAC Agent
- **Infrastructure Layer**:
  - MinIO: blob storage
  - PostgreSQL: metadata, RBAC, chat history
  - Qdrant: vector store
  - Neo4j (optional): graph search
  - Meilisearch/Elastic/BM25: keyword search

---

## 2. Technology Stack

### Recommended Backend Language
**Python**, due to strong ecosystem support (LlamaIndex, LangChain, LangGraph, OCR tooling).

### Frameworks and Components
| Component | Technology |
|----------|------------|
| Backend API | FastAPI |
| Orchestration | LangGraph |
| Frontend | Next.js |
| Document Storage | MinIO |
| RDBMS | PostgreSQL |
| Vector DB | Qdrant |
| Graph DB (optional) | Neo4j |
| BM25 Engine | Meilisearch or Postgres FTS |
| LLM Router | LiteLLM |
| Local Model Runtime | Ollama / LLM.cpp |
| Security | JWT, RBAC, API Keys |
| Deployment | Docker Compose |

---

## 3. Modular Agent Design (Core Workflow)

### A. Knowledge Base Manager Agent
Responsible for:
- Create KB (metadata + MinIO bucket/folder)
- Assign groups/permissions
- Delete/Update KB
- Upload documents (single or batch)

---

### B. Ingestion Agent
Sub‑agents:
- File Loader (MinIO → buffer)
- Parser (PDF/DOCX/TXT/IMG to Markdown)
- Metadata Extractor
- Text Splitter (configurable: recursive, semantic, hybrid)
- Cleaning & Normalization

Optional: Integrate RAGFlow’s DeepDoc parser for better OCR and layout recovery.

---

### C. Embedding & Indexing Agent
Responsibilities:
- Embed chunks using OpenAI/Gemini/Claude/Ollama
- Store vectors in Qdrant
- Store chunk metadata in PostgreSQL
- Extract entities & relationships → store in Neo4j
- Insert chunk tokens into BM25 search engine

Supports configurable embedding models per KB.

---

### D. Retrieval Agent
Performs hybrid search:
1. Vector search (semantic)
2. BM25 keyword search
3. Graph traversal (optional)
4. Reranking using cross‑encoder
5. Return context blocks + citations

It selects retrieval mode dynamically:
- Queries with entities → Graph
- Highly technical terms → BM25
- Natural language → Vector
- Mixed queries → Hybrid

---

### E. Chat & Reasoning Agent
- Handles user chat sessions
- Maintains per‑KB conversation history
- Sends user query → Retrieval Agent → LLM
- Injects citations and context blocks
- Logs conversation metadata

---

### F. User & RBAC Agent
Core rules:
- Users belong to groups
- Groups are assigned to KBs
- Access control is validated *before* any retrieval
- All actions logged for audit

---

## 4. Database Schema (PostgreSQL)

### Key Tables
**users**
**roles** (admin/editor/viewer)
**groups**
**user_groups**
**knowledge_bases**
**kb_permissions** (group_id, kb_id, access_level)
**documents**
**chunks**
**chats**
**messages**

This schema enforces:
- Multi‑tenant KB access
- Group‑based RBAC
- Auditability
- Strong isolation between KBs

---

## 5. Ingestion Pipeline Example (LangGraph)

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IngestionState(TypedDict):
    kb_id: str
    file_id: str
    text_chunks: List[str]
    vectors: List[list]
    status: str

def load_from_minio(state: IngestionState):
    file_content = MinioClient.get(state["kb_id"], state["file_id"])
    return {"file_content": file_content}

def parse_document(state: IngestionState):
    text = parser.parse(state["file_content"])
    return {"raw_text": text}

def split_text(state: IngestionState):
    chunks = text_splitter.split(state["raw_text"])
    return {"text_chunks": chunks}

def embed_chunks(state: IngestionState):
    vectors = embedder.embed(state["text_chunks"])
    return {"vectors": vectors}

def store_results(state: IngestionState):
    Qdrant.upsert(state["kb_id"], state["text_chunks"], state["vectors"])
    return {"status": "complete"}

workflow = StateGraph(IngestionState)
workflow.add_node("load", load_from_minio)
workflow.add_node("parse", parse_document)
workflow.add_node("split", split_text)
workflow.add_node("embed", embed_chunks)
workflow.add_node("store", store_results)

workflow.set_entry_point("load")
workflow.add_edge("load", "parse")
workflow.add_edge("parse", "split")
workflow.add_edge("split", "embed")
workflow.add_edge("embed", "store")
workflow.add_edge("store", END)

ingestion_app = workflow.compile()
```

---

## 6. Deployment Layout (Docker Compose)

### Services
- frontend (Next.js)
- backend (FastAPI + LangGraph)
- postgres
- minio
- qdrant
- neo4j (optional)
- meilisearch
- ollama (optional)
- prometheus + grafana

This setup supports:
- Isolation between KBs
- Horizontal scaling
- Modular agent‑based architecture

---

## 7. Comparison vs RAGFlow

### Borrow from RAGFlow:
- DeepDoc parsing
- Layout-aware extraction
- Good OCR for structured docs

### Improve beyond RAGFlow:
- Fully modular agent architecture
- RBAC user/group access per KB
- Headless API-only design
- Multiple embedding models per KB
- Optional GraphRAG
- Optional BM25 search
- Highly configurable ingestion pipelines

---

## 8. Implementation Roadmap

### **Phase 1: Foundation**
- JWT auth
- RBAC model
- KB management API
- File upload to MinIO

### **Phase 2: Ingestion Pipeline**
- Parser → Splitter → Embedder → Store
- Background task execution

### **Phase 3: Hybrid Retrieval**
- Vector + BM25 + Graph
- Reranking
- Chat API with history

### **Phase 4: Advanced**
- Multi‑LLM routing (via LiteLLM)
- Per‑KB embeddings + settings
- Monitoring & metrics
- Admin dashboards

---

# End of Document
