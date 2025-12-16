# Story 8-11: Graph-Augmented Retrieval

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-11
**Priority:** HIGH (Core Feature)
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Implement the Vector-first + Graph-augment retrieval strategy. Vector search runs first, then graph queries expand the context with related entities and their source documents. This improves answer quality by including semantically related but textually different content.

---

## Acceptance Criteria

### AC1: Vector-First Search
**Given** a user submits a search query
**When** retrieval is performed
**Then** vector search runs first (existing behavior)
**And** top-K similar chunks are retrieved
**And** results are scored by similarity

### AC2: Entity Extraction from Query
**Given** vector search completes
**When** graph augmentation begins
**Then** entities are extracted from the user query
**And** entity types are limited to the KB's domain schema
**And** extraction uses lightweight pattern matching first, LLM fallback

### AC3: Graph Neighborhood Expansion
**Given** entities are identified in the query
**When** graph expansion runs
**Then** each entity's 1-hop neighborhood is queried
**And** related entities are collected
**And** source documents of related entities are identified

### AC4: Context Augmentation
**Given** related entities have source documents
**When** augmentation merges results
**Then** chunks from related documents are added to context
**And** duplicates are removed (same chunk not added twice)
**And** augmented chunks are marked with relationship path
**And** total context respects token limits

### AC5: Merged Result Scoring
**Given** vector and graph results are combined
**When** final ranking is performed
**Then** scores consider:
  - Original vector similarity (primary)
  - Graph relationship strength (secondary)
  - Entity confidence scores
**And** results are sorted by combined score

### AC6: Retrieval Transparency
**Given** augmented results are returned
**When** the response is generated
**Then** each result indicates:
  - Source type: "vector" | "graph_augmented"
  - For graph results: the relationship path that included it
**And** this information is available for citation generation

---

## Technical Notes

### Retrieval Flow

```
1. User Query → Vector Search (Qdrant)
     ↓
2. Top-K Chunks Retrieved
     ↓
3. Entity Extraction from Query
     ↓
4. Graph Query (Neo4j) - Find entities, expand neighborhoods
     ↓
5. Collect source documents from graph entities
     ↓
6. Retrieve chunks from those documents (Qdrant)
     ↓
7. Merge & Rank: Vector results + Graph-augmented results
     ↓
8. Return combined context for LLM synthesis
```

### Service Implementation

```python
# backend/app/services/graph_augmented_retrieval_service.py
class GraphAugmentedRetrievalService:
    def __init__(
        self,
        search_service: SearchService,
        graph_query_service: GraphQueryService,
        entity_extraction_service: EntityExtractionService
    ):
        self.search = search_service
        self.graph = graph_query_service
        self.extraction = entity_extraction_service

    async def retrieve(
        self,
        kb_id: UUID,
        query: str,
        vector_top_k: int = 10,
        graph_expansion_depth: int = 1,
        max_augmented_chunks: int = 5,
        max_total_chunks: int = 15
    ) -> AugmentedRetrievalResult:
        """Perform vector-first + graph-augmented retrieval."""

        # Step 1: Vector search
        vector_results = await self.search.semantic_search(
            kb_id=kb_id,
            query=query,
            top_k=vector_top_k
        )

        # Step 2: Check if KB has graph data
        has_graph = await self._kb_has_graph_data(kb_id)
        if not has_graph:
            return AugmentedRetrievalResult(
                chunks=vector_results,
                graph_context=None,
                retrieval_strategy="vector_only"
            )

        # Step 3: Extract entities from query
        query_entities = await self._extract_entities_from_query(kb_id, query)

        if not query_entities:
            return AugmentedRetrievalResult(
                chunks=vector_results,
                graph_context=None,
                retrieval_strategy="vector_only"
            )

        # Step 4: Graph neighborhood expansion
        related_entities = await self._expand_graph_neighborhood(
            kb_id, query_entities, depth=graph_expansion_depth
        )

        # Step 5: Collect source documents from related entities
        source_doc_ids = self._collect_source_documents(
            related_entities, exclude=self._get_doc_ids(vector_results)
        )

        # Step 6: Retrieve chunks from those documents
        augmented_chunks = await self._retrieve_augmented_chunks(
            kb_id, query, source_doc_ids, limit=max_augmented_chunks
        )

        # Step 7: Mark augmented chunks with graph context
        for chunk in augmented_chunks:
            chunk.source_type = "graph_augmented"
            chunk.relationship_path = self._get_relationship_path(chunk, related_entities)

        # Step 8: Merge and rank
        combined = self._merge_and_rank(
            vector_results, augmented_chunks, max_total=max_total_chunks
        )

        return AugmentedRetrievalResult(
            chunks=combined,
            graph_context=GraphContext(
                query_entities=query_entities,
                expanded_entities=related_entities
            ),
            retrieval_strategy="vector_first_graph_augmented"
        )

    async def _extract_entities_from_query(
        self,
        kb_id: UUID,
        query: str
    ) -> List[EntityMatch]:
        """Extract entities from query using pattern matching and LLM fallback."""
        # Get KB's domain schema
        domain_schema = await self._get_kb_domain_schema(kb_id)

        # Fast: Pattern matching for known entity names
        pattern_matches = await self._pattern_match_entities(kb_id, query)

        if pattern_matches:
            return pattern_matches

        # Fallback: LLM extraction (slower but more accurate)
        return await self.extraction.extract_entities_from_text(
            text=query,
            domain_schema=domain_schema,
            mode="query"  # Lightweight mode for queries
        )

    async def _expand_graph_neighborhood(
        self,
        kb_id: UUID,
        entities: List[EntityMatch],
        depth: int
    ) -> List[RelatedEntity]:
        """Expand entity neighborhoods in the graph."""
        related = []

        for entity in entities:
            neighborhood = await self.graph.get_entity_neighborhood(
                kb_id=kb_id,
                entity_id=entity.id,
                depth=depth,
                limit=20
            )

            for connection in neighborhood.connections:
                related.append(RelatedEntity(
                    entity_id=connection.neighbor_id,
                    entity_type=connection.neighbor_type,
                    entity_name=connection.neighbor_name,
                    relationship=connection.relationship,
                    direction=connection.direction,
                    source_entity=entity.name
                ))

        # Deduplicate
        return self._deduplicate_entities(related)

    def _merge_and_rank(
        self,
        vector_results: List[ChunkResult],
        augmented_chunks: List[ChunkResult],
        max_total: int
    ) -> List[ChunkResult]:
        """Merge and rank vector + graph results."""
        # Vector results keep their original scores
        for chunk in vector_results:
            chunk.source_type = "vector"
            chunk.combined_score = chunk.similarity_score

        # Augmented chunks get boosted score based on graph relevance
        for chunk in augmented_chunks:
            graph_boost = 0.1  # Base boost for being graph-related
            chunk.combined_score = chunk.similarity_score * (1 + graph_boost)

        # Combine and sort
        all_chunks = vector_results + augmented_chunks

        # Remove duplicates (prefer vector result if same chunk)
        seen_chunk_ids = set()
        unique_chunks = []
        for chunk in all_chunks:
            if chunk.id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk.id)
                unique_chunks.append(chunk)

        # Sort by combined score
        unique_chunks.sort(key=lambda c: c.combined_score, reverse=True)

        return unique_chunks[:max_total]
```

### Response Schema

```python
class AugmentedRetrievalResult(BaseModel):
    chunks: List[ChunkResult]
    graph_context: Optional[GraphContext]
    retrieval_strategy: Literal["vector_only", "vector_first_graph_augmented"]

class ChunkResult(BaseModel):
    id: str
    content: str
    document_id: UUID
    document_name: str
    similarity_score: float
    combined_score: Optional[float] = None
    source_type: Literal["vector", "graph_augmented"] = "vector"
    relationship_path: Optional[str] = None  # e.g., "Server -[HOSTS]-> Service"

class GraphContext(BaseModel):
    query_entities: List[EntityMatch]
    expanded_entities: List[RelatedEntity]
```

### Integration with Existing Search

```python
# Modify existing search endpoint to use augmented retrieval
@router.post("/search")
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Semantic search with optional graph augmentation."""
    # Check if graph augmentation is enabled for KB
    if await kb_has_graph_enabled(request.kb_id):
        service = GraphAugmentedRetrievalService(...)
        results = await service.retrieve(
            kb_id=request.kb_id,
            query=request.query,
            vector_top_k=request.top_k or 10
        )
    else:
        # Fallback to vector-only search
        service = SearchService(...)
        results = await service.semantic_search(...)

    return results
```

---

## Definition of Done

- [ ] Vector-first search integration
- [ ] Query entity extraction (pattern + LLM)
- [ ] Graph neighborhood expansion
- [ ] Source document collection
- [ ] Augmented chunk retrieval
- [ ] Result merging and ranking
- [ ] Source type tracking (vector vs graph)
- [ ] Relationship path in results
- [ ] Performance within acceptable limits
- [ ] Unit tests for retrieval logic
- [ ] Integration tests end-to-end
- [ ] A/B comparison with vector-only

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-10 (Graph Query Service), Story 8-8 (Entity Extraction)
**Next Story:** Story 8-12 (Retrieval Strategy Abstraction)
