# KB Settings Parameter Reference

> **Version**: 1.0
> **Last Updated**: 2025-12-09
> **Related**: [LLM Configuration Architecture](./03-llm-configuration.md)

This document provides comprehensive parameter reference for KB-Level Configuration in LumiKB. Each configuration category can be customized per Knowledge Base to optimize for specific content types and use cases.

## Table of Contents

1. [Configuration Precedence](#configuration-precedence)
2. [ChunkingConfig](#1-chunkingconfig)
3. [EmbeddingConfig](#2-embeddingconfig)
4. [RetrievalConfig](#3-retrievalconfig)
5. [RerankingConfig](#4-rerankingconfig)
6. [GenerationConfig](#5-generationconfig)
7. [NERConfig](#6-nerconfig)
8. [DocumentProcessingConfig](#7-documentprocessingconfig)
9. [KBPromptConfig](#8-kbpromptconfig)
10. [Debug Mode](#9-debug-mode)
11. [Preset Configurations](#preset-configurations)
12. [Migration & Re-indexing](#migration--re-indexing)

---

## Configuration Precedence

LumiKB uses a three-layer configuration hierarchy:

```
Request Parameters → KB Settings → System Defaults
     (highest)                        (lowest)
```

- **Request Parameters**: Per-request overrides (e.g., `/search?top_k=20`)
- **KB Settings**: Knowledge Base configuration (stored in `kb_settings` JSONB)
- **System Defaults**: Global defaults from system configuration

---

## 1. ChunkingConfig

Controls how documents are split into chunks for embedding and retrieval.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `strategy` | enum | `"recursive"` | fixed, recursive, semantic, sentence, paragraph | Chunking algorithm |
| `chunk_size` | int | `512` | 100-4096 | Target chunk size in tokens |
| `chunk_overlap` | int | `50` | 0-512 | Overlap between consecutive chunks |
| `separators` | list[str] | `["\n\n", "\n", ". "]` | - | Custom separators for recursive strategy |

### Strategy Details

| Strategy | Best For | Pros | Cons |
|----------|----------|------|------|
| **fixed** | Uniform content | Predictable sizes, fast | May break mid-sentence |
| **recursive** | General documents | Respects structure, flexible | Slightly slower |
| **semantic** | Complex documents | Preserves meaning | Requires embedding calls, slowest |
| **sentence** | Q&A content | Clean boundaries | Variable chunk sizes |
| **paragraph** | Articles, reports | Natural breaks | May produce large chunks |

### Use Case Guidelines

| Content Type | Recommended Strategy | chunk_size | chunk_overlap |
|--------------|---------------------|------------|---------------|
| Legal documents | recursive | 1024 | 100 |
| Technical docs | recursive | 512 | 50 |
| Q&A/FAQ | sentence | 256 | 25 |
| Code files | fixed | 256 | 50 |
| Research papers | semantic | 1024 | 100 |
| Chat logs | paragraph | 512 | 0 |

### Schema

```python
class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "recursive", "semantic", "sentence", "paragraph"] = "recursive"
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=512)
    separators: Optional[list[str]] = None

    @validator("chunk_overlap")
    def overlap_less_than_size(cls, v, values):
        if "chunk_size" in values and v >= values["chunk_size"]:
            raise ValueError("overlap must be less than chunk_size")
        return v
```

---

## 2. EmbeddingConfig

Controls how text is converted to vector embeddings for semantic search.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `model_id` | UUID | `None` | - | Reference to LLM model registry (None = system default) |
| `batch_size` | int | `32` | 1-100 | Number of texts to embed per API call |
| `normalize` | bool | `True` | - | L2 normalize embeddings |
| `truncation` | enum | `"end"` | start, end, none | How to truncate oversized text |
| `max_length` | int | `None` | 128-16384 | Maximum input length (None = model default) |
| `prefix_document` | str | `""` | max 100 chars | Prefix added to documents before embedding |
| `prefix_query` | str | `""` | max 100 chars | Prefix added to queries before embedding |
| `pooling_strategy` | enum | `"mean"` | mean, cls, max, last | Token pooling strategy |

### Truncation Strategies

| Strategy | Behavior | Best For |
|----------|----------|----------|
| **end** | Truncate excess from end | General use, most common |
| **start** | Truncate from beginning | Summaries, conclusions |
| **none** | Error on overflow | Strict validation |

### Pooling Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **mean** | Average all token embeddings | General purpose, most robust |
| **cls** | Use [CLS] token embedding | BERT-style models |
| **max** | Max pooling across tokens | Capturing key features |
| **last** | Use last token embedding | Autoregressive models |

### Prefix Examples

| Use Case | prefix_document | prefix_query |
|----------|-----------------|--------------|
| General | `""` | `""` |
| E5 models | `"passage: "` | `"query: "` |
| Instructor | `"Represent the document for retrieval: "` | `"Represent the question for retrieval: "` |
| BGE models | `""` | `"Represent this sentence for searching: "` |

### Schema

```python
class EmbeddingConfig(BaseModel):
    model_id: Optional[UUID] = None  # None = system default
    batch_size: int = Field(default=32, ge=1, le=100)
    normalize: bool = True
    truncation: Literal["start", "end", "none"] = "end"
    max_length: Optional[int] = Field(default=None, ge=128, le=16384)
    prefix_document: str = Field(default="", max_length=100)
    prefix_query: str = Field(default="", max_length=100)
    pooling_strategy: Literal["mean", "cls", "max", "last"] = "mean"
```

### Important Constraints

> **Warning**: Changing embedding configuration (especially `model_id`, `normalize`, `prefix_*`, or `pooling_strategy`) requires **re-indexing all documents** in the KB. The system will:
> 1. Validate the new configuration
> 2. Mark all documents for re-processing
> 3. Queue embedding regeneration jobs
> 4. Update the Qdrant collection

---

## 3. RetrievalConfig

Controls how chunks are retrieved from the vector database during search.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `method` | enum | `"hybrid"` | vector, hybrid, hyde | Retrieval strategy |
| `top_k` | int | `10` | 1-100 | Number of chunks to retrieve |
| `similarity_threshold` | float | `0.7` | 0.0-1.0 | Minimum similarity score |
| `use_mmr` | bool | `True` | - | Enable Maximal Marginal Relevance |
| `mmr_lambda` | float | `0.5` | 0.0-1.0 | MMR diversity factor |
| `hybrid_alpha` | float | `0.5` | 0.0-1.0 | Blend factor for hybrid search |

### Method Details

| Method | Description | When to Use |
|--------|-------------|-------------|
| **vector** | Pure semantic similarity search | Well-defined concepts, synonyms matter |
| **hybrid** | Combines vector + keyword (BM25) | General purpose, balanced results |
| **hyde** | Hypothetical Document Embeddings | Complex queries, "find documents about X" |

### MMR (Maximal Marginal Relevance)

MMR reduces redundancy by balancing relevance with diversity:

```
MMR = λ × Sim(doc, query) - (1-λ) × max(Sim(doc, selected_docs))
```

| mmr_lambda | Behavior |
|------------|----------|
| 1.0 | Pure relevance (no diversity) |
| 0.5 | Balanced (recommended) |
| 0.0 | Maximum diversity |

### Hybrid Alpha

Controls vector vs keyword weight in hybrid search:

| hybrid_alpha | Behavior |
|--------------|----------|
| 1.0 | Pure vector search |
| 0.5 | Equal weight (default) |
| 0.0 | Pure keyword search |

### Schema

```python
class RetrievalConfig(BaseModel):
    method: Literal["vector", "hybrid", "hyde"] = "hybrid"
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_mmr: bool = True
    mmr_lambda: float = Field(default=0.5, ge=0.0, le=1.0)
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)
```

---

## 4. RerankingConfig

Controls post-retrieval reranking using cross-encoder models.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enabled` | bool | `True` | - | Enable/disable reranking |
| `model` | str | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | - | Reranking model identifier |
| `top_n` | int | `5` | 1-50 | Final number of chunks after reranking |

### Recommended Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Fast | Good | General use |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | Medium | Better | Balanced |
| `BAAI/bge-reranker-base` | Medium | Very Good | Multilingual |
| `BAAI/bge-reranker-large` | Slow | Excellent | High precision |
| `mixedbread-ai/mxbai-rerank-large-v1` | Slow | Excellent | Maximum quality |

### Pipeline Flow

```
Retrieval (top_k=20) → Reranking → Final Results (top_n=5)
```

### Schema

```python
class RerankingConfig(BaseModel):
    enabled: bool = True
    model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_n: int = Field(default=5, ge=1, le=50)

    @validator("top_n")
    def top_n_validation(cls, v):
        # Note: top_n should be <= retrieval top_k (validated at runtime)
        return v
```

---

## 5. GenerationConfig

Controls LLM response generation parameters.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `model_id` | UUID | `None` | - | Reference to LLM model registry |
| `temperature` | float | `0.7` | 0.0-2.0 | Randomness in generation |
| `top_p` | float | `0.9` | 0.0-1.0 | Nucleus sampling threshold |
| `top_k` | int | `None` | 1-100 | Top-k token sampling |
| `max_tokens` | int | `2048` | 100-32768 | Maximum response length |
| `frequency_penalty` | float | `0.0` | -2.0-2.0 | Penalize repeated tokens |
| `presence_penalty` | float | `0.0` | -2.0-2.0 | Penalize topic repetition |
| `stop_sequences` | list[str] | `[]` | max 4 | Stop generation triggers |

### Temperature Guidelines

| Temperature | Behavior | Use Case |
|-------------|----------|----------|
| 0.0-0.3 | Very deterministic | Facts, citations, code |
| 0.4-0.7 | Balanced | General Q&A |
| 0.8-1.0 | Creative | Drafts, brainstorming |
| 1.0-2.0 | Highly random | Creative writing |

### Penalty Effects

| Parameter | Positive Value | Negative Value |
|-----------|----------------|----------------|
| `frequency_penalty` | Discourages repetition | Encourages patterns |
| `presence_penalty` | Encourages new topics | Stays focused |

### Schema

```python
class GenerationConfig(BaseModel):
    model_id: Optional[UUID] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1, le=100)
    max_tokens: int = Field(default=2048, ge=100, le=32768)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: list[str] = Field(default_factory=list, max_items=4)
```

---

## 6. NERConfig

Controls Named Entity Recognition for GraphRAG integration.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enabled` | bool | `False` | - | Enable entity extraction |
| `model` | str | `"en_core_web_lg"` | - | SpaCy/custom NER model |
| `confidence_threshold` | float | `0.8` | 0.0-1.0 | Minimum entity confidence |
| `entity_types` | list[str] | `["PERSON", "ORG", "GPE", "DATE"]` | - | Entity types to extract |
| `batch_size` | int | `10` | 1-100 | Documents per NER batch |

### Entity Types

| Type | Description | Examples |
|------|-------------|----------|
| `PERSON` | People names | "John Smith", "Dr. Jones" |
| `ORG` | Organizations | "Google", "United Nations" |
| `GPE` | Geo-political entities | "Paris", "United States" |
| `DATE` | Dates and periods | "January 2024", "Q3 2023" |
| `MONEY` | Monetary values | "$1.5 million", "EUR 500" |
| `PRODUCT` | Products | "iPhone", "Windows 11" |
| `EVENT` | Named events | "World War II", "Olympics" |
| `LAW` | Legal documents | "GDPR", "Section 230" |
| `WORK_OF_ART` | Creative works | "Mona Lisa", "Star Wars" |

### Schema

```python
class NERConfig(BaseModel):
    enabled: bool = False
    model: str = "en_core_web_lg"
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    entity_types: list[str] = Field(
        default=["PERSON", "ORG", "GPE", "DATE"]
    )
    batch_size: int = Field(default=10, ge=1, le=100)
```

---

## 7. DocumentProcessingConfig

Controls document parsing and content extraction.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `ocr_enabled` | bool | `True` | - | Enable OCR for images/scans |
| `ocr_language` | str | `"eng"` | Tesseract codes | OCR language |
| `language_detection` | bool | `True` | - | Auto-detect document language |
| `table_extraction` | bool | `True` | - | Extract tables as structured data |
| `image_extraction` | bool | `False` | - | Extract and describe images |

### OCR Language Codes

| Code | Language | Code | Language |
|------|----------|------|----------|
| `eng` | English | `fra` | French |
| `deu` | German | `spa` | Spanish |
| `chi_sim` | Chinese (Simplified) | `chi_tra` | Chinese (Traditional) |
| `jpn` | Japanese | `kor` | Korean |
| `ara` | Arabic | `rus` | Russian |

Multiple languages: `"eng+fra+deu"`

### Schema

```python
class DocumentProcessingConfig(BaseModel):
    ocr_enabled: bool = True
    ocr_language: str = Field(default="eng", max_length=50)
    language_detection: bool = True
    table_extraction: bool = True
    image_extraction: bool = False
```

---

## 8. KBPromptConfig

Controls system prompts and response formatting.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `system_prompt` | str | `None` | max 4000 chars | Custom system prompt |
| `context_template` | str | `None` | max 2000 chars | Template for context injection |
| `citation_style` | enum | `"inline"` | inline, footnote, none | Citation format |
| `uncertainty_handling` | enum | `"acknowledge"` | acknowledge, refuse, best_effort | Low-confidence behavior |
| `response_language` | str | `None` | ISO 639-1 | Force response language |

### Citation Styles

| Style | Example Output |
|-------|----------------|
| **inline** | "The company was founded in 2020 [1] and expanded globally [2]." |
| **footnote** | "The company was founded in 2020¹ and expanded globally²." |
| **none** | "The company was founded in 2020 and expanded globally." |

### Uncertainty Handling

| Mode | Behavior |
|------|----------|
| **acknowledge** | "Based on available information... I'm not certain, but..." |
| **refuse** | "I don't have enough information to answer this question." |
| **best_effort** | Provide best answer without caveats |

### Context Template Variables

| Variable | Description |
|----------|-------------|
| `{context}` | Retrieved chunks |
| `{query}` | User question |
| `{kb_name}` | Knowledge base name |
| `{sources}` | Source document list |

### Example System Prompt

```
You are a helpful assistant for {kb_name}.
Answer questions using ONLY the provided context.
If the answer is not in the context, say "I don't have that information."
Always cite your sources using [1], [2], etc.
```

### Schema

```python
class KBPromptConfig(BaseModel):
    system_prompt: Optional[str] = Field(default=None, max_length=4000)
    context_template: Optional[str] = Field(default=None, max_length=2000)
    citation_style: Literal["inline", "footnote", "none"] = "inline"
    uncertainty_handling: Literal["acknowledge", "refuse", "best_effort"] = "acknowledge"
    response_language: Optional[str] = Field(default=None, max_length=10)
```

---

## 9. Debug Mode

Controls RAG pipeline telemetry for debugging and troubleshooting.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `debug_mode` | bool | `false` | - | Enable debug output for RAG pipeline |

### Debug Mode Output

When enabled, chat responses include additional telemetry:

| Field | Type | Description |
|-------|------|-------------|
| `kb_params` | object | Active KB configuration parameters |
| `chunks_retrieved` | array | Retrieved chunks with similarity scores |
| `timing` | object | Performance metrics (retrieval_ms, context_assembly_ms) |

### SSE Event Format

```json
{
  "type": "debug",
  "data": {
    "kb_params": {
      "system_prompt": "...",
      "citation_style": "inline",
      "response_language": "en",
      "uncertainty_handling": "acknowledge"
    },
    "chunks_retrieved": [
      {
        "document_id": "uuid",
        "document_name": "example.pdf",
        "score": 0.92,
        "text_preview": "First 100 chars..."
      }
    ],
    "timing": {
      "retrieval_ms": 145,
      "context_assembly_ms": 12
    }
  }
}
```

### Use Cases

| Scenario | How Debug Mode Helps |
|----------|---------------------|
| Poor retrieval quality | View similarity scores and chunk content |
| Slow responses | Identify timing bottlenecks |
| Unexpected behavior | Verify KB configuration is applied correctly |
| Citation issues | Inspect retrieved chunks and mapping |

### Security Note

> **Important**: Debug output may contain sensitive document content. Debug mode should only be accessible to users with KB admin/edit permissions.

---

## Preset Configurations

Pre-defined configuration bundles for common use cases.

### Legal KB Preset

```python
LEGAL_PRESET = {
    "chunking": {
        "strategy": "recursive",
        "chunk_size": 1024,
        "chunk_overlap": 100
    },
    "retrieval": {
        "method": "hybrid",
        "top_k": 15,
        "similarity_threshold": 0.75,
        "use_mmr": True,
        "mmr_lambda": 0.6
    },
    "generation": {
        "temperature": 0.3,
        "max_tokens": 4096
    },
    "prompt": {
        "citation_style": "footnote",
        "uncertainty_handling": "refuse"
    }
}
```

### Technical Documentation Preset

```python
TECHNICAL_PRESET = {
    "chunking": {
        "strategy": "recursive",
        "chunk_size": 512,
        "chunk_overlap": 50
    },
    "retrieval": {
        "method": "hybrid",
        "top_k": 10,
        "similarity_threshold": 0.7
    },
    "generation": {
        "temperature": 0.5,
        "max_tokens": 2048
    },
    "prompt": {
        "citation_style": "inline",
        "uncertainty_handling": "acknowledge"
    }
}
```

### Creative Writing Preset

```python
CREATIVE_PRESET = {
    "chunking": {
        "strategy": "semantic",
        "chunk_size": 768,
        "chunk_overlap": 100
    },
    "retrieval": {
        "method": "vector",
        "top_k": 8,
        "similarity_threshold": 0.6,
        "mmr_lambda": 0.4
    },
    "generation": {
        "temperature": 0.9,
        "top_p": 0.95,
        "max_tokens": 4096
    },
    "prompt": {
        "citation_style": "none",
        "uncertainty_handling": "best_effort"
    }
}
```

### Code Repository Preset

```python
CODE_PRESET = {
    "chunking": {
        "strategy": "fixed",
        "chunk_size": 256,
        "chunk_overlap": 50
    },
    "retrieval": {
        "method": "hybrid",
        "top_k": 20,
        "similarity_threshold": 0.65,
        "hybrid_alpha": 0.6
    },
    "generation": {
        "temperature": 0.2,
        "max_tokens": 3000
    },
    "prompt": {
        "citation_style": "inline",
        "uncertainty_handling": "acknowledge"
    }
}
```

---

## Migration & Re-indexing

### Changes Requiring Re-indexing

| Configuration | Requires Re-index | Reason |
|--------------|-------------------|--------|
| ChunkingConfig.strategy | Yes | Chunk boundaries change |
| ChunkingConfig.chunk_size | Yes | Chunk content changes |
| ChunkingConfig.chunk_overlap | Yes | Chunk content changes |
| EmbeddingConfig.model_id | Yes | Vector dimensions may differ |
| EmbeddingConfig.normalize | Yes | Vector values change |
| EmbeddingConfig.prefix_* | Yes | Embedding inputs change |
| EmbeddingConfig.pooling_strategy | Yes | Vector calculation changes |
| RetrievalConfig.* | No | Query-time only |
| RerankingConfig.* | No | Query-time only |
| GenerationConfig.* | No | Query-time only |
| NERConfig.* | Partial | Only new documents |
| DocumentProcessingConfig.* | Partial | Only new documents |
| KBPromptConfig.* | No | Query-time only |

### Re-indexing Process

When a re-indexing trigger is detected:

1. **Validation**: System validates new configuration
2. **Estimate**: Calculate re-indexing time/cost
3. **Confirmation**: User confirms the operation
4. **Marking**: All documents marked `needs_reprocessing`
5. **Queue**: Background jobs process documents
6. **Progress**: Real-time progress tracking
7. **Completion**: KB settings updated on success

### API Response for Re-indexing Changes

```json
{
  "requires_reindex": true,
  "affected_documents": 1523,
  "estimated_time_minutes": 45,
  "estimated_cost_tokens": 2500000,
  "message": "Changing embedding model requires re-indexing all documents. Proceed?"
}
```

---

## Related Documentation

- [LLM Configuration Architecture](./03-llm-configuration.md)
- [Epic 7: Infrastructure & Operations](../epics/epic-7-infrastructure.md) - Stories 7.12-7.17
- [PRD Requirements](../prd.md) - FR99-FR110
