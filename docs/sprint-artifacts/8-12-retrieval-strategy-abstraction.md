# Story 8-12: Retrieval Strategy Abstraction

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-12
**Priority:** MEDIUM
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Create an abstraction layer for retrieval strategies that allows switching between Vector-only, Vector-first + Graph-augment, and future Parallel Merge strategies. This enables per-KB configuration and prepares for future enhancements.

---

## Acceptance Criteria

### AC1: Strategy Interface
**Given** multiple retrieval strategies exist
**When** the abstraction is implemented
**Then** all strategies implement a common interface:
  - `retrieve(kb_id, query, options) -> RetrievalResult`
  - `supports_kb(kb_id) -> bool`
  - `get_capabilities() -> StrategyCapabilities`

### AC2: Strategy Registry
**Given** strategies are registered
**When** retrieval is requested
**Then** the appropriate strategy is selected based on:
  - KB configuration (if explicitly set)
  - KB capabilities (has graph data?)
  - Default system configuration

### AC3: Vector-Only Strategy
**Given** a KB without graph data
**When** retrieval is requested
**Then** the VectorOnlyStrategy is used
**And** standard Qdrant vector search runs
**And** results are returned without graph context

### AC4: Vector-First Strategy
**Given** a KB with graph data (default)
**When** retrieval is requested
**Then** the VectorFirstGraphAugmentStrategy is used
**And** vector search runs first
**And** graph augmentation enhances results

### AC5: Strategy Configuration per KB
**Given** an admin configures a KB
**When** retrieval strategy is set
**Then** the KB stores the strategy preference
**And** future retrievals use the configured strategy
**And** fallback occurs if strategy requirements aren't met

### AC6: Parallel Merge Strategy (Future-Ready)
**Given** future Parallel Merge implementation
**When** the strategy is registered
**Then** it integrates seamlessly with existing abstraction
**And** no changes to consuming code are required
**And** interface contract is satisfied

---

## Technical Notes

### Strategy Interface

```python
# backend/app/services/retrieval/strategy_base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

class RetrievalStrategy(ABC):
    """Base class for all retrieval strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    @abstractmethod
    async def retrieve(
        self,
        kb_id: UUID,
        query: str,
        top_k: int = 10,
        options: Optional[RetrievalOptions] = None
    ) -> RetrievalResult:
        """Execute retrieval with this strategy."""
        pass

    @abstractmethod
    async def supports_kb(self, kb_id: UUID) -> bool:
        """Check if this strategy can be used for the given KB."""
        pass

    def get_capabilities(self) -> StrategyCapabilities:
        """Return strategy capabilities."""
        return StrategyCapabilities(
            supports_graph=False,
            supports_hybrid=False,
            supports_reranking=False
        )

class RetrievalOptions(BaseModel):
    """Options for retrieval strategies."""
    vector_top_k: int = 10
    graph_expansion_depth: int = 1
    max_augmented_chunks: int = 5
    similarity_threshold: float = 0.5
    include_graph_context: bool = True

class StrategyCapabilities(BaseModel):
    """Capabilities of a retrieval strategy."""
    supports_graph: bool = False
    supports_hybrid: bool = False
    supports_reranking: bool = False
    requires_graph_data: bool = False
```

### Concrete Strategies

```python
# backend/app/services/retrieval/vector_only_strategy.py
class VectorOnlyStrategy(RetrievalStrategy):
    """Standard vector-based retrieval using Qdrant."""

    name = "vector_only"
    description = "Vector similarity search without graph augmentation"

    def __init__(self, search_service: SearchService):
        self.search = search_service

    async def retrieve(
        self,
        kb_id: UUID,
        query: str,
        top_k: int = 10,
        options: Optional[RetrievalOptions] = None
    ) -> RetrievalResult:
        results = await self.search.semantic_search(kb_id, query, top_k)

        return RetrievalResult(
            chunks=results,
            strategy_used=self.name,
            graph_context=None
        )

    async def supports_kb(self, kb_id: UUID) -> bool:
        # Vector-only always works
        return True


# backend/app/services/retrieval/vector_first_strategy.py
class VectorFirstGraphAugmentStrategy(RetrievalStrategy):
    """Vector search first, then graph augmentation."""

    name = "vector_first_graph_augment"
    description = "Vector search with graph-based context expansion"

    def __init__(
        self,
        search_service: SearchService,
        graph_service: GraphQueryService,
        extraction_service: EntityExtractionService
    ):
        self.search = search_service
        self.graph = graph_service
        self.extraction = extraction_service

    async def retrieve(
        self,
        kb_id: UUID,
        query: str,
        top_k: int = 10,
        options: Optional[RetrievalOptions] = None
    ) -> RetrievalResult:
        opts = options or RetrievalOptions()

        # Implementation from Story 8-11
        # ...

    async def supports_kb(self, kb_id: UUID) -> bool:
        # Requires graph data
        return await self._kb_has_graph_data(kb_id)

    def get_capabilities(self) -> StrategyCapabilities:
        return StrategyCapabilities(
            supports_graph=True,
            supports_hybrid=False,
            supports_reranking=False,
            requires_graph_data=True
        )
```

### Strategy Registry

```python
# backend/app/services/retrieval/strategy_registry.py
from typing import Dict, Type

class StrategyRegistry:
    """Registry and factory for retrieval strategies."""

    _strategies: Dict[str, Type[RetrievalStrategy]] = {}
    _default_strategy: str = "vector_only"

    @classmethod
    def register(cls, strategy_class: Type[RetrievalStrategy]):
        """Register a retrieval strategy."""
        instance = strategy_class()
        cls._strategies[instance.name] = strategy_class

    @classmethod
    def get_strategy(
        cls,
        name: Optional[str] = None,
        **dependencies
    ) -> RetrievalStrategy:
        """Get a strategy instance by name."""
        strategy_name = name or cls._default_strategy

        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        return cls._strategies[strategy_name](**dependencies)

    @classmethod
    def get_best_strategy_for_kb(
        cls,
        kb_id: UUID,
        kb_config: Optional[KBRetrievalConfig] = None,
        **dependencies
    ) -> RetrievalStrategy:
        """Select the best strategy for a KB."""
        # If KB has explicit preference, use it
        if kb_config and kb_config.retrieval_strategy:
            strategy = cls.get_strategy(kb_config.retrieval_strategy, **dependencies)
            if await strategy.supports_kb(kb_id):
                return strategy

        # Auto-select: use graph strategy if KB has graph data
        graph_strategy = cls.get_strategy("vector_first_graph_augment", **dependencies)
        if await graph_strategy.supports_kb(kb_id):
            return graph_strategy

        # Fallback to vector-only
        return cls.get_strategy("vector_only", **dependencies)

    @classmethod
    def list_strategies(cls) -> List[StrategyInfo]:
        """List all registered strategies."""
        return [
            StrategyInfo(
                name=s.name,
                description=s.description,
                capabilities=s.get_capabilities()
            )
            for s in cls._strategies.values()
        ]


# Register strategies at module load
StrategyRegistry.register(VectorOnlyStrategy)
StrategyRegistry.register(VectorFirstGraphAugmentStrategy)
```

### KB Retrieval Configuration

```python
# Add to KB model/schema
class KBRetrievalConfig(BaseModel):
    retrieval_strategy: Optional[str] = None  # None = auto-select
    vector_top_k: int = 10
    graph_expansion_depth: int = 1
    similarity_threshold: float = 0.5
```

### Usage in Search Endpoint

```python
# backend/app/api/v1/search.py
@router.post("/search")
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unified search endpoint using strategy abstraction."""
    # Get KB configuration
    kb_config = await get_kb_retrieval_config(request.kb_id, db)

    # Get appropriate strategy
    strategy = StrategyRegistry.get_best_strategy_for_kb(
        kb_id=request.kb_id,
        kb_config=kb_config,
        search_service=SearchService(db),
        graph_service=GraphQueryService(get_neo4j()),
        extraction_service=EntityExtractionService(get_litellm())
    )

    # Execute retrieval
    result = await strategy.retrieve(
        kb_id=request.kb_id,
        query=request.query,
        top_k=request.top_k or kb_config.vector_top_k
    )

    return result
```

---

## Definition of Done

- [ ] RetrievalStrategy abstract base class
- [ ] VectorOnlyStrategy implementation
- [ ] VectorFirstGraphAugmentStrategy implementation
- [ ] StrategyRegistry with registration
- [ ] Auto-selection based on KB capabilities
- [ ] KB configuration for strategy preference
- [ ] API endpoint updated to use abstraction
- [ ] Strategy listing endpoint
- [ ] Unit tests for registry
- [ ] Integration tests for strategy selection
- [ ] Documentation for adding new strategies

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-11 (Graph-Augmented Retrieval)
**Next Story:** Story 8-13 (LLM Schema Enrichment Suggestions)
