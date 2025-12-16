# LLM Configuration

← Back to [Architecture Index](index.md) | **Previous**: [02 - Technology Stack](02-technology-stack.md)

---

## LLM Model Configuration

LumiKB uses a **centralized model configuration pattern** that allows switching between LLM providers by changing settings in one location. The system defaults to local Ollama models for offline/free usage.

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL CONFIGURATION FLOW                      │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │ backend/app/core │  settings.llm_model = "ollama/gemma3:4b"  │
│  │    config.py     │  settings.embedding_model = "ollama-embedding"│
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │   LiteLLM Proxy  │  Routes model requests to providers       │
│  │ litellm_config.yaml│  Model aliases: default, embedding       │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ├──────────────┬──────────────┬──────────────┐        │
│           ▼              ▼              ▼              ▼        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Ollama  │    │  OpenAI  │    │  Gemini  │    │ Anthropic│  │
│  │  (local) │    │  (cloud) │    │  (cloud) │    │  (cloud) │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Default Models (Local Ollama)

| Purpose | Model | Dimensions | Config Setting |
|---------|-------|------------|----------------|
| **Generation** | `gemma3:4b` | N/A | `settings.llm_model = "ollama/gemma3:4b"` |
| **Embedding** | `nomic-embed-text` | 768 | `settings.embedding_model = "ollama-embedding"` |

### How to Change Models

**Option 1: Change Default Provider (Recommended)**

Edit `infrastructure/docker/litellm_config.yaml` model aliases:

```yaml
# Change default generation model
- model_name: default
  litellm_params:
    model: openai/gpt-4o-mini  # Was: ollama/gemma3:4b
    api_key: os.environ/OPENAI_API_KEY

# Change default embedding model
- model_name: embedding
  litellm_params:
    model: openai/text-embedding-3-small  # Was: ollama/nomic-embed-text
    api_key: os.environ/OPENAI_API_KEY
```

Then rebuild LiteLLM: `docker compose build litellm && docker compose up -d litellm`

**Option 2: Direct Model Reference**

Edit `backend/app/core/config.py`:

```python
# For generation
llm_model: str = "gpt-4o-mini"  # Uses LiteLLM routing

# For embeddings
embedding_model: str = "gemini-embedding"  # Uses LiteLLM alias
```

### LiteLLM Model Aliases

| Alias | Current Target | Description |
|-------|----------------|-------------|
| `default` | `ollama/gemma3:4b` | Default generation model for chat/synthesis |
| `embedding` | `ollama/nomic-embed-text` | Default embedding model (768 dims) |
| `ollama-embedding` | `ollama/nomic-embed-text` | Explicit Ollama embedding reference |
| `gemini-embedding` | `gemini/text-embedding-004` | Google Gemini embedding (768 dims) |
| `openai-embedding-small` | `openai/text-embedding-3-small` | OpenAI embedding (1536 dims) |

### Embedding Dimension Compatibility

| Model | Dimensions | Compatible Collections |
|-------|------------|------------------------|
| `nomic-embed-text` (Ollama) | **768** | Current default |
| `text-embedding-004` (Gemini) | **768** | Compatible with current |
| `text-embedding-3-small` (OpenAI) | 1536 | Requires collection rebuild |
| `text-embedding-3-large` (OpenAI) | 3072 | Requires collection rebuild |

> **Important**: Changing embedding models with different dimensions requires recreating Qdrant collections and re-embedding all documents.

### Docker Configuration

LiteLLM config is baked into the Docker image to avoid bind mount caching issues:

```dockerfile
# infrastructure/docker/Dockerfile.litellm
FROM ghcr.io/berriai/litellm:main-latest
COPY litellm_config.yaml /app/config.yaml
CMD ["--config", "/app/config.yaml", "--port", "4000"]
```

After changing `litellm_config.yaml`, rebuild the container:

```bash
cd infrastructure/docker
docker compose build litellm
docker compose up -d litellm
```

### Environment Variables for API Keys

Set in `.env` or `docker-compose.yml`:

```bash
# Required for cloud providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# For local Ollama (default)
OLLAMA_API_BASE=http://host.docker.internal:11434
```

---

## LLM Model Registry (Epic 7)

LumiKB implements a **centralized model registry** that enables administrators to configure and manage LLM providers at the system level, with per-KB model overrides for specialized use cases.

### Model Registry Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MODEL REGISTRY ARCHITECTURE                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    SYSTEM-LEVEL REGISTRY                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │   Providers  │  │    Models    │  │   Defaults   │             │ │
│  │  │  ┌────────┐  │  │  ┌────────┐  │  │  Generation  │             │ │
│  │  │  │ Ollama │  │  │  │gemma3:4b│  │  │  Embedding   │             │ │
│  │  │  │ OpenAI │  │  │  │gpt-4o  │  │  │  NER         │             │ │
│  │  │  │ Gemini │  │  │  │claude  │  │  │              │             │ │
│  │  │  │Anthropic│  │  │  │nomic  │  │  │              │             │ │
│  │  │  │ Cohere │  │  │  └────────┘  │  └──────────────┘             │ │
│  │  │  └────────┘  │  └──────────────┘                               │ │
│  │  └──────────────┘                                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    KB-LEVEL OVERRIDES (Optional)                   │ │
│  │  KB: "Legal Documents"          KB: "Technical Wiki"               │ │
│  │  ┌─────────────────────┐        ┌─────────────────────┐           │ │
│  │  │ Generation: gpt-4o  │        │ Generation: default │           │ │
│  │  │ Embedding: default  │        │ Embedding: default  │           │ │
│  │  │ NER: legal-ner      │        │ NER: default        │           │ │
│  │  └─────────────────────┘        └─────────────────────┘           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         LITELLM PROXY                              │ │
│  │              Routes requests to appropriate providers              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Model Types

| Type | Purpose | Example Models | Configuration |
|------|---------|----------------|---------------|
| **Generation** | Chat, synthesis, document creation | `gemma3:4b`, `gpt-4o`, `claude-3-5-sonnet` | `settings.llm_model` |
| **Embedding** | Text vectorization for search | `nomic-embed-text`, `text-embedding-3-small` | `settings.embedding_model` |
| **NER** | Named Entity Recognition for GraphRAG | LLM-based, `spacy/en_core_web_lg` | `settings.ner_model` |

### Model Providers

The Model Registry supports multiple LLM providers, each requiring different API routing:

| Provider | Type | Routing | API Format |
|----------|------|---------|------------|
| **ollama** | Local | Direct call | `ollama/{model}` with `api_base` |
| **lmstudio** | Local | Direct call | `lmstudio/{model}` with `api_base` |
| **openai** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **anthropic** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **gemini** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **azure** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **cohere** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **deepseek** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **qwen** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |
| **mistral** | Cloud | LiteLLM Proxy | OpenAI-compatible via proxy |

### DB-to-Proxy Sync (Option C)

LumiKB implements **automatic model synchronization** between the database and LiteLLM proxy. When administrators create, update, or delete models via the Admin UI, the changes are automatically registered with the LiteLLM proxy runtime - no manual YAML editing required.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DB-TO-PROXY SYNC ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Admin UI                 Backend                    LiteLLM Proxy       │
│  ─────────                ───────                    ─────────────       │
│      │                       │                            │              │
│      │  Create Model         │                            │              │
│      │─────────────────────>│                            │              │
│      │                       │  1. Save to DB             │              │
│      │                       │─────────────────>│        │              │
│      │                       │                   │ llm_models table     │
│      │                       │                   │        │              │
│      │                       │  2. POST /model/new        │              │
│      │                       │──────────────────────────>│              │
│      │                       │    {                       │              │
│      │                       │      model_name: db-{uuid} │              │
│      │                       │      litellm_params: {...} │              │
│      │                       │    }                       │              │
│      │                       │<──────────────────────────│              │
│      │  Model Created        │                            │              │
│      │<─────────────────────│                            │              │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                        Connection Test Flow                              │
│  ─────────────────────────────────────────────────────────────────────  │
│      │                       │                            │              │
│      │  Test Connection      │                            │              │
│      │─────────────────────>│                            │              │
│      │                       │  aembedding/acompletion(   │              │
│      │                       │    model="openai/db-{uuid}"│              │
│      │                       │    api_base=litellm_url    │              │
│      │                       │  )                         │              │
│      │                       │──────────────────────────>│              │
│      │                       │                            │  Routes to   │
│      │                       │                            │  actual      │
│      │                       │                            │  provider    │
│      │                       │<──────────────────────────│              │
│      │  Test Result          │                            │              │
│      │<─────────────────────│                            │              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Components:**

| Component | Description |
|-----------|-------------|
| `litellm_proxy_service.py` | Core sync service handling proxy registration |
| `db-{uuid}` alias | Unique identifier for DB models in proxy (prevents conflicts with YAML models) |
| `openai/` prefix | Universal routing prefix for connection testing through LiteLLM |
| `STORE_MODEL_IN_DB: "True"` | LiteLLM environment variable enabling runtime model registration |

**Sync Behavior:**

1. **On Model Create/Update**: `register_model_with_proxy()` calls LiteLLM `/model/new` API
2. **On Model Delete**: `unregister_model_from_proxy()` calls LiteLLM `/model/delete` API
3. **On Backend Startup**: `sync_all_models_to_proxy()` re-registers all DB models (handles proxy restarts)
4. **Clear-Before-Sync**: Prevents duplicate entries by clearing `db-*` prefixed models before re-registering

**LiteLLM API Deletion Note:**

LiteLLM's `/model/delete` endpoint requires the internal `model_info.id` (a hash), **not** the `model_name` alias. The sync service handles this by:

1. Looking up `model_info.id` from `/model/info` response before deletion
2. Matching by `model_name` to find the corresponding `model_info.id`
3. Using `model_info.id` in the deletion request: `{"id": "<hash>"}`

```python
# Example: Correct deletion flow
# 1. Get model info to find internal ID
response = await client.get(f"{litellm_url}/model/info")
for m in response.json()["data"]:
    if m["model_name"] == "db-{uuid}":
        model_info_id = m["model_info"]["id"]  # e.g., "abc123hash"

# 2. Delete using model_info.id (NOT model_name)
await client.post(
    f"{litellm_url}/model/delete",
    json={"id": model_info_id}  # Correct: uses internal hash
)
```

**Provider Routing Through Proxy:**

| Provider | Model Name in Proxy | api_base | Notes |
|----------|---------------------|----------|-------|
| Ollama | `ollama/{model_id}` | `settings.ollama_url_for_proxy` | Docker networking |
| OpenAI | `openai/{model_id}` | None (uses default) | API key from DB |
| Anthropic | `anthropic/{model_id}` | None | API key from DB |
| LM Studio | `openai/{model_id}` | `model.api_endpoint` | OpenAI-compatible |
| All others | `{prefix}/{model_id}` | Varies | Standard LiteLLM routing |

**Docker Configuration:**

```yaml
# docker-compose.yml - LiteLLM service
litellm:
  environment:
    # Enable runtime model registration
    STORE_MODEL_IN_DB: "True"
```

**Environment-Specific URL Resolution:**

```python
# config.py
ollama_url_for_proxy: str = "http://host.docker.internal:11434"
# When backend runs on host but LiteLLM proxy runs in Docker,
# the proxy needs host.docker.internal to reach Ollama on the host.
```

### Provider-Based Routing (KB Model Configuration)

When a KB specifies a custom embedding or generation model, the system uses **provider-based routing** to correctly call the model API:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROVIDER-BASED ROUTING FLOW                           │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Document Processing Worker                                        │ │
│  │  1. Load KB's embedding_model_id from database                     │ │
│  │  2. Fetch LLMModel with provider, model_id, api_endpoint           │ │
│  │  3. Create EmbeddingConfig with provider field                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  LiteLLMEmbeddingClient._call_embedding_api()                      │ │
│  │                                                                     │ │
│  │  if provider in DIRECT_CALL_PROVIDERS:  # {"ollama", "lmstudio"}   │ │
│  │      └─→ Direct API call with provider prefix                      │ │
│  │          model = f"{provider}/{model_id}"                          │ │
│  │          api_base = model's custom endpoint                        │ │
│  │  else:                                                             │ │
│  │      └─→ LiteLLM Proxy with OpenAI-compatible format               │ │
│  │          custom_llm_provider = "openai"                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                   ┌────────────────┴────────────────┐                   │
│                   ▼                                  ▼                   │
│  ┌──────────────────────────┐      ┌──────────────────────────┐        │
│  │  Local Providers          │      │  Cloud Providers          │        │
│  │  • Ollama (port 11434)    │      │  • OpenAI                 │        │
│  │  • LM Studio (port 1234)  │      │  • Anthropic              │        │
│  │  • Custom local servers   │      │  • Gemini, Azure, etc.    │        │
│  └──────────────────────────┘      └──────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Implementation Details:**

```python
# backend/app/workers/embedding.py
class EmbeddingConfig(NamedTuple):
    """Configuration for KB-specific embedding model."""
    model_id: str | None = None
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    api_endpoint: str | None = None
    provider: str | None = None  # Used for routing decisions

# backend/app/integrations/litellm_client.py
class LiteLLMEmbeddingClient:
    # Providers requiring direct API calls (not through LiteLLM proxy)
    DIRECT_CALL_PROVIDERS = {"ollama", "lmstudio"}

    async def _call_embedding_api(self, texts: list[str]):
        is_direct_provider = (
            self.provider and self.provider.lower() in self.DIRECT_CALL_PROVIDERS
        )

        if is_direct_provider:
            # Direct call to local provider with provider prefix
            model_name = f"{self.provider.lower()}/{self.model}"
            response = await aembedding(
                model=model_name,
                input=texts,
                api_base=self.api_base,  # e.g., http://localhost:11434
            )
        else:
            # Cloud providers via LiteLLM proxy
            response = await aembedding(
                model=self.model,
                input=texts,
                api_base=self.api_base,  # LiteLLM proxy URL
                api_key=self.api_key,
                custom_llm_provider="openai",
            )
```

This routing pattern ensures:
- **Local providers** (Ollama, LM Studio) are called directly with the correct model prefix
- **Cloud providers** are routed through the LiteLLM proxy for unified API handling
- **Extensibility**: New local providers can be added to `DIRECT_CALL_PROVIDERS` without code changes

### LiteLLM Streaming Configuration

**Critical Setting for Streaming:** When using LiteLLM for chat streaming, retries must be disabled to prevent duplicate token delivery.

**Problem:** LiteLLM's retry mechanism can cause streaming responses to be duplicated (e.g., "HereHere's's a a").

**Solution:** Set `num_retries: 0` in both proxy and client:

```yaml
# infrastructure/docker/litellm_config.yaml
router_settings:
  num_retries: 0  # CRITICAL: Prevents duplicate streaming requests
  timeout: 120
```

```python
# backend/app/integrations/litellm_client.py
response = await acompletion(
    model=model_name,
    stream=True,
    num_retries=0,  # Prevents duplicate streaming
)
```

**Additional Settings:**
```python
# Disable streaming logging (prevents event loop issues in Celery workers)
litellm.disable_streaming_logging = True
litellm.turn_off_message_logging = True
```

> **Note:** Model prefix should be `litellm_proxy/{model}` when routing through the LiteLLM proxy server.

---

### Chat/Generation Model Configuration

Chat conversations use KB-specific generation models through the ConversationService:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHAT KB MODEL ROUTING FLOW                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Chat API Endpoint (chat.py, chat_stream.py)                       │ │
│  │  1. Receive ChatRequest with kb_id                                 │ │
│  │  2. Inject AsyncSession into ConversationService                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ConversationService._get_kb_generation_model(kb_id)               │ │
│  │  1. Query KB with joinedload(generation_model)                     │ │
│  │  2. Return model_id string (e.g., "gpt-4o-mini", "gemma3:4b")     │ │
│  │  3. Return None if not configured → use system default            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  LiteLLMEmbeddingClient.chat_completion(model=kb_model)            │ │
│  │  1. Format model name: "litellm_proxy/{model_id}"                  │ │
│  │  2. Route through LiteLLM proxy for all providers                  │ │
│  │  3. Proxy handles provider-specific routing                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Implementation Details:**

```python
# backend/app/services/conversation_service.py
class ConversationService:
    def __init__(self, search_service, session: AsyncSession | None = None):
        self._session = session  # For KB model lookup

    async def _get_kb_generation_model(self, kb_id: str) -> str | None:
        """Get KB-specific generation model ID."""
        if not self._session:
            return None  # Fall back to system default

        result = await self._session.execute(
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.generation_model))
            .where(KnowledgeBase.id == uuid.UUID(kb_id))
        )
        kb = result.unique().scalar_one_or_none()
        if kb and kb.generation_model:
            return kb.generation_model.model_id  # e.g., "gpt-4o-mini"
        return None

    async def send_message(self, ...):
        kb_model = await self._get_kb_generation_model(kb_id)
        response = await self.llm_client.chat_completion(
            messages=prompt_messages,
            model=kb_model,  # Uses KB model or system default if None
        )

# backend/app/api/v1/chat.py
def get_conversation_service(
    search_service: SearchService = Depends(get_search_service),
    session: AsyncSession = Depends(get_async_session),  # For KB model lookup
) -> ConversationService:
    return ConversationService(search_service, session=session)
```

### KB Model Configuration

Knowledge bases can override system defaults for specialized requirements:

```python
# backend/app/models/knowledge_base.py
class KnowledgeBase(Base):
    # ... existing fields ...

    # Model overrides (NULL = use system default)
    generation_model: Mapped[Optional[str]] = mapped_column(String(100))
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))
    ner_model: Mapped[Optional[str]] = mapped_column(String(100))

    # GraphRAG settings
    domain_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("domains.id"))
    graph_enabled: Mapped[bool] = mapped_column(default=False)
```

---

## KB-Level Configuration (Epic 7)

LumiKB implements a **three-layer configuration model** that allows fine-grained control at the request, knowledge base, and system levels. This enables specialized RAG parameters per KB while maintaining sensible defaults.

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THREE-LAYER CONFIGURATION MODEL                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: REQUEST PARAMETERS (Highest Priority)                    │ │
│  │  API request body parameters (temperature, top_k, etc.)            │ │
│  │  When present: Use this value                                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼ (if NULL)                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: KB-LEVEL SETTINGS                                        │ │
│  │  KnowledgeBase.settings JSONB with KBSettings Pydantic schema      │ │
│  │  Configured per-KB via Admin UI or API                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼ (if NULL)                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: SYSTEM DEFAULTS                                          │ │
│  │  backend/app/core/config.py + Pydantic defaults                    │ │
│  │  Last resort fallback values                                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### KBSettings Schema Structure

> **Detailed Parameter Reference**: For complete parameter documentation including ranges, defaults, use cases, and preset configurations, see [KB Settings Parameter Reference](./kb-settings-parameter-reference.md).

The `KnowledgeBase.settings` JSONB column stores a validated `KBSettings` Pydantic model:

```python
class KBSettings(BaseModel):
    """Complete KB-level configuration with sensible defaults."""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)  # NEW
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reranking: RerankingConfig = Field(default_factory=RerankingConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    ner: NERConfig = Field(default_factory=NERConfig)
    processing: DocumentProcessingConfig = Field(default_factory=DocumentProcessingConfig)
    prompts: KBPromptConfig = Field(default_factory=KBPromptConfig)
    preset: Literal["legal", "technical", "creative", "code", "general", None] = None

# Nested Configuration Models
class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "recursive", "semantic", "sentence", "paragraph"] = "recursive"
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=512)

class EmbeddingConfig(BaseModel):
    """KB-level embedding configuration - changes require re-indexing."""
    model_id: Optional[UUID] = None  # None = system default
    batch_size: int = Field(default=32, ge=1, le=100)
    normalize: bool = True
    truncation: Literal["start", "end", "none"] = "end"
    max_length: Optional[int] = Field(default=None, ge=128, le=16384)
    prefix_document: str = Field(default="", max_length=100)
    prefix_query: str = Field(default="", max_length=100)
    pooling_strategy: Literal["mean", "cls", "max", "last"] = "mean"

class RetrievalConfig(BaseModel):
    method: Literal["vector", "hybrid", "hyde"] = "hybrid"
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_mmr: bool = True
    mmr_lambda: float = Field(default=0.5, ge=0.0, le=1.0)

class RerankingConfig(BaseModel):
    enabled: bool = True
    model: Optional[str] = None  # NULL = system default
    top_n: int = Field(default=5, ge=1, le=50)

class GenerationConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=100, le=32768)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

class NERConfig(BaseModel):
    enabled: bool = True
    model: Optional[str] = None  # NULL = system default
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

class DocumentProcessingConfig(BaseModel):
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    table_extraction: bool = True
    image_extraction: bool = False

class KBPromptConfig(BaseModel):
    """KB-level prompt customization - KEY FEATURE for per-KB behavior."""
    system_prompt: str = ""  # Custom LLM instructions with {kb_name}, {context}, {query} variables
    context_template: str = ""  # Optional template for context formatting
    citation_style: Literal["inline", "footnote", "none"] = "inline"
    uncertainty_handling: Literal["acknowledge", "refuse", "best_effort"] = "acknowledge"
    response_language: str = "en"  # Supported: en, vi - auto-switches prompt templates
```

**System Prompt Variables:**
- `{kb_name}` - Knowledge Base name
- `{context}` - Retrieved document chunks
- `{query}` - User's question

**Bilingual Templates:** Frontend provides EN/VI prompt templates that auto-switch when response language changes.

### Configuration Presets

Presets provide one-click configuration for common use cases:

| Preset | Chunking | Retrieval | Generation | Use Case |
|--------|----------|-----------|------------|----------|
| **legal** | semantic, 1024 chunks | hybrid, 0.85 threshold | temp=0.3, explicit citations | Legal documents, contracts |
| **technical** | fixed, 512 chunks | vector, top_k=15 | temp=0.5, footnote citations | Technical docs, APIs |
| **creative** | paragraph | hyde, 0.6 threshold | temp=0.9, max_tokens=4096 | Marketing, creative writing |
| **code** | fixed, 256 chunks | vector, top_k=20 | temp=0.2, inline citations | Code repos, documentation |
| **general** | semantic, 512 chunks | hybrid, 0.7 threshold | temp=0.7, inline citations | Default balanced config |

### KBConfigResolver Service

The `KBConfigResolver` service implements three-layer resolution with caching:

```python
class KBConfigResolver:
    """Resolves effective configuration from three layers."""

    async def resolve_retrieval_config(
        self,
        kb_id: UUID,
        request_params: Optional[RetrievalParams] = None
    ) -> RetrievalConfig:
        """
        Resolution order:
        1. request_params (if provided and non-None for each field)
        2. kb.settings.retrieval (from DB, cached)
        3. system defaults (Pydantic defaults)
        """
        kb_settings = await self._get_kb_settings(kb_id)  # Redis cached

        return RetrievalConfig(
            method=request_params.method if request_params?.method else kb_settings.retrieval.method,
            top_k=request_params.top_k if request_params?.top_k else kb_settings.retrieval.top_k,
            # ... etc
        )

    async def _get_kb_settings(self, kb_id: UUID) -> KBSettings:
        """Get KB settings with Redis caching (5min TTL)."""
        cache_key = f"kb_settings:{kb_id}"
        cached = await redis.get(cache_key)
        if cached:
            return KBSettings.model_validate_json(cached)

        kb = await kb_repo.get(kb_id)
        settings = KBSettings.model_validate(kb.settings or {})
        await redis.setex(cache_key, 300, settings.model_dump_json())
        return settings
```

### Service Integration Pattern

All services that use KB-level configuration follow this integration pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SERVICE INTEGRATION ARCHITECTURE                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  API Layer (chat_stream.py, search.py)                             │ │
│  │  Dependencies: session (DB), redis_client (cache)                  │ │
│  │  Injection: Passes dependencies to services for config resolution  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Service Layer                                                      │ │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐          │ │
│  │  │  SearchService          │  │  ConversationService    │          │ │
│  │  │  _resolve_retrieval_    │  │  _resolve_generation_   │          │ │
│  │  │  config(kb_id)          │  │  config(kb_id)          │          │ │
│  │  │  Uses: top_k,           │  │  Uses: temperature,     │          │ │
│  │  │  similarity_threshold   │  │  max_tokens, top_p      │          │ │
│  │  └─────────────────────────┘  └─────────────────────────┘          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  KBConfigResolver                                                   │ │
│  │  _get_kb_settings_cached() → Redis (5min TTL)                      │ │
│  │  resolve_retrieval_config() / resolve_generation_config()          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

**SearchService Integration (retrieval config):**

```python
# backend/app/services/search_service.py
class SearchService:
    async def _resolve_retrieval_config(self, kb_id: str) -> RetrievalConfig:
        """Resolve retrieval config with three-layer precedence."""
        if self._session and self._redis:
            resolver = KBConfigResolver(self._session, self._redis)
            return await resolver.resolve_retrieval_config(uuid.UUID(kb_id))
        # Fallback to schema defaults (not hardcoded values)
        return RetrievalConfig()

    async def search_similar(self, kb_id: str, ...):
        config = await self._resolve_retrieval_config(kb_id)
        # Use config.top_k, config.similarity_threshold from KB settings
        results = await self.qdrant_client.search(
            limit=config.top_k,
            score_threshold=config.similarity_threshold,
        )
```

**ConversationService Integration (generation config):**

```python
# backend/app/services/conversation_service.py
class ConversationService:
    def __init__(self, search_service, session=None, redis_client=None):
        self._session = session      # For KB model & config lookup
        self._redis = redis_client   # For config caching

    async def _resolve_generation_config(self, kb_id: str) -> GenerationConfig:
        """Resolve generation config with three-layer precedence."""
        if self._session and self._redis:
            resolver = KBConfigResolver(self._session, self._redis)
            return await resolver.resolve_generation_config(uuid.UUID(kb_id))
        return GenerationConfig()

    async def send_message_stream(self, kb_id: str, ...):
        gen_config = await self._resolve_generation_config(kb_id)
        # Use KB settings for LLM call
        response = await self.llm_client.chat_completion(
            temperature=gen_config.temperature,  # From KB settings
            max_tokens=gen_config.max_tokens,    # From KB settings
            top_p=gen_config.top_p,              # From KB settings
        )
```

**API Dependency Injection:**

```python
# backend/app/api/v1/chat_stream.py
async def get_conversation_service(
    search_service: SearchService = Depends(get_search_service),
    session: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client),  # Required for caching
) -> ConversationService:
    return ConversationService(search_service, session=session, redis_client=redis_client)
```

**Key Implementation Notes:**

1. **No Hardcoded Fallbacks**: Services use `RetrievalConfig()` or `GenerationConfig()` defaults, not hardcoded values like `10` or `0.7`
2. **Redis Required for Caching**: Services must receive `redis_client` to enable KB settings caching
3. **Graceful Degradation**: If DB/Redis unavailable, falls back to Pydantic schema defaults
4. **Schema Defaults**: All default values defined in `backend/app/schemas/kb_settings.py`

### Hot-Reload Configuration

KB configuration changes take effect without service restart:

1. **API Update**: `PATCH /api/v1/knowledge-bases/{kb_id}/settings`
2. **Cache Invalidation**: Redis pub/sub notifies all workers
3. **Next Request**: Fresh config loaded from DB
4. **Audit Logging**: All config changes logged with before/after diff

### KB Settings UI

Two admin panels provide configuration access:

| Panel | Purpose | Key Features |
|-------|---------|--------------|
| **General Panel** | RAG parameters | Chunking strategy, retrieval method, temperature, top_k |
| **Prompts Panel** | LLM behavior | System prompt editor with variables, citation style, uncertainty handling, response language (EN/VI) with bilingual template support |

**Prompts Panel Features:**
- System prompt textarea with {kb_name}, {context}, {query} variable support
- Load Template dropdown with 4 templates in EN and VI languages
- Response language dropdown (English/Tiếng Việt) - auto-switches prompt to selected language
- Preview modal showing rendered prompt with sample values

Presets can be applied with one click, populating all fields with recommended values for the use case.

### Migration & Backwards Compatibility

- Empty `settings` (`{}` or `NULL`) parses to all defaults - no errors
- Partial settings merge with defaults - only override what's specified
- Migration adds `settings JSONB DEFAULT '{}'` - zero downtime
- Existing KBs continue working with system defaults

---

**Previous**: [02 - Technology Stack](02-technology-stack.md) | **Next**: [04 - GraphRAG Integration](04-graphrag-integration.md) | **Index**: [Architecture](index.md)
