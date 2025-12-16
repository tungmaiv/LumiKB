# GraphRAG Integration

← Back to [Architecture Index](index.md) | **Previous**: [03 - LLM Configuration](03-llm-configuration.md)

---

## Graph Database Configuration (Epic 8)

Neo4j provides entity-relationship storage for GraphRAG-enabled knowledge bases. This is an **optional component** - KBs without graph features use vector-only retrieval.

### Neo4j Configuration

```yaml
# infrastructure/docker/docker-compose.yml
neo4j:
  image: neo4j:5-community
  container_name: lumikb-neo4j
  ports:
    - "7474:7474"  # Browser
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    - NEO4J_PLUGINS=["apoc"]
    - NEO4J_dbms_memory_heap_initial__size=512m
    - NEO4J_dbms_memory_heap_max__size=1G
  volumes:
    - neo4j_data:/data
  networks:
    - lumikb-network
```

### Graph Schema

```cypher
// Core node labels
(:Entity {id, name, type, source_document_id, source_chunk_id, confidence})
(:Document {id, name, kb_id})
(:Chunk {id, document_id, text, page, section})

// Relationships
(:Entity)-[:MENTIONED_IN]->(:Chunk)
(:Entity)-[:RELATED_TO {type, confidence}]->(:Entity)
(:Chunk)-[:PART_OF]->(:Document)

// Domain-specific labels (examples)
(:Person), (:Organization), (:Location), (:Product), (:Event)
(:Contract), (:Regulation), (:Technology), (:Process)
```

### Domain Schema Configuration

Domain schemas define extractable entity types and relationships for a knowledge base:

```python
# backend/app/models/domain.py
class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Schema versioning
    schema_version: Mapped[int] = mapped_column(default=1)
    last_schema_change: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    entity_types: Mapped[List["EntityType"]] = relationship(back_populates="domain")
    relationship_types: Mapped[List["RelationshipType"]] = relationship(back_populates="domain")

class EntityType(Base):
    __tablename__ = "entity_types"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"))
    name: Mapped[str] = mapped_column(String(100))  # e.g., "Person", "Contract"
    label: Mapped[str] = mapped_column(String(100))  # Neo4j node label
    description: Mapped[Optional[str]] = mapped_column(Text)
    extraction_prompt: Mapped[Optional[str]] = mapped_column(Text)  # Custom prompt hints
    color: Mapped[Optional[str]] = mapped_column(String(7))  # UI display color

class RelationshipType(Base):
    __tablename__ = "relationship_types"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"))
    name: Mapped[str] = mapped_column(String(100))  # e.g., "REPORTS_TO"
    source_entity_type_id: Mapped[UUID] = mapped_column(ForeignKey("entity_types.id"))
    target_entity_type_id: Mapped[UUID] = mapped_column(ForeignKey("entity_types.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
```

### Built-in Domain Templates

| Domain | Entity Types | Relationship Types | Use Case |
|--------|--------------|-------------------|----------|
| **IT Operations** | Server, Application, Team, Incident | RUNS_ON, OWNED_BY, CAUSED_BY | Infrastructure documentation |
| **Legal/Compliance** | Contract, Party, Clause, Regulation | SIGNED_BY, REFERENCES, GOVERNED_BY | Legal document analysis |
| **Sales/Marketing** | Customer, Product, Campaign, Competitor | PURCHASED, TARGETS, COMPETES_WITH | CRM knowledge base |
| **Project Management** | Project, Milestone, Resource, Risk | ASSIGNED_TO, DEPENDS_ON, MITIGATED_BY | Project documentation |
| **HR/People** | Employee, Department, Role, Policy | REPORTS_TO, BELONGS_TO, SUBJECT_TO | HR knowledge management |

---

## GraphRAG Integration Pattern (Epic 8)

GraphRAG enhances retrieval by combining vector similarity with graph traversal. This enables answering questions that require understanding entity relationships across documents.

### Retrieval Strategy Abstraction

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL STRATEGY PATTERN                            │
│                                                                          │
│  Query: "Who manages the authentication service?"                        │
│                           │                                              │
│                           ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │               STRATEGY SELECTOR (based on KB config)               │ │
│  │                                                                     │ │
│  │   graph_enabled=false     OR     graph_enabled=true                 │ │
│  │          │                              │                           │ │
│  │          ▼                              ▼                           │ │
│  │   ┌─────────────┐              ┌─────────────────────┐             │ │
│  │   │ VECTOR-ONLY │              │  GRAPH-AUGMENTED    │             │ │
│  │   │  RETRIEVAL  │              │    RETRIEVAL        │             │ │
│  │   └──────┬──────┘              └──────────┬──────────┘             │ │
│  └──────────┼─────────────────────────────────┼────────────────────────┘ │
│             │                                 │                          │
│             ▼                                 ▼                          │
│   ┌──────────────────┐          ┌─────────────────────────────────────┐ │
│   │     Qdrant       │          │  1. Qdrant: Vector search           │ │
│   │ Semantic Search  │          │  2. Neo4j: Entity extraction        │ │
│   │                  │          │  3. Neo4j: Graph traversal          │ │
│   │ Return: Chunks   │          │  4. Merge & rank results            │ │
│   └──────────────────┘          └─────────────────────────────────────┘ │
│             │                                 │                          │
│             └─────────────────┬───────────────┘                          │
│                               ▼                                          │
│                   ┌─────────────────────┐                                │
│                   │  UNIFIED RESPONSE   │                                │
│                   │  (Chunks + Context) │                                │
│                   └─────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Graph-Augmented Retrieval Flow

```python
# backend/app/services/graphrag_service.py
class GraphRAGService:
    async def retrieve(
        self,
        query: str,
        kb_id: UUID,
        top_k: int = 10
    ) -> RetrievalResult:
        """
        Enhanced retrieval combining vector search with graph context.
        """
        # Step 1: Vector search for relevant chunks
        vector_results = await self.qdrant.search(
            collection=f"kb_{kb_id}",
            query_vector=await self.embed(query),
            limit=top_k
        )

        # Step 2: Extract entities from query
        query_entities = await self.extract_entities(query)

        # Step 3: Find related entities via graph traversal
        graph_context = await self.neo4j.query("""
            MATCH (e:Entity)-[r*1..2]-(related:Entity)
            WHERE e.name IN $entity_names
            RETURN e, r, related
            LIMIT 50
        """, entity_names=[e.name for e in query_entities])

        # Step 4: Expand chunk results with graph-connected chunks
        connected_chunks = await self.get_chunks_for_entities(graph_context)

        # Step 5: Merge and re-rank
        return self.merge_and_rank(vector_results, connected_chunks, query_entities)
```

### Entity Extraction Pipeline

```
Document Upload → Chunking → Embedding → ENTITY EXTRACTION → Graph Storage
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                    │
                    ▼                                                    ▼
           ┌───────────────┐                                  ┌───────────────┐
           │  LLM-based    │                                  │ spaCy/Local   │
           │  Extraction   │                                  │  NER Model    │
           │               │                                  │               │
           │ - Domain-aware│                                  │ - Fast        │
           │ - Custom types│                                  │ - Standard    │
           │ - Relationships│                                 │ - No LLM cost │
           └───────┬───────┘                                  └───────┬───────┘
                   │                                                   │
                   └─────────────────────┬─────────────────────────────┘
                                         ▼
                               ┌───────────────────┐
                               │   Entity Store    │
                               │     (Neo4j)       │
                               │                   │
                               │ Nodes: Entities   │
                               │ Edges: Relations  │
                               │ Props: Provenance │
                               └───────────────────┘
```

### LLM-based Entity Extraction Prompt

```python
EXTRACTION_SYSTEM_PROMPT = """
You are an expert entity extraction system. Given a text chunk and a domain schema,
extract entities and relationships following these rules:

DOMAIN: {domain_name}
ENTITY TYPES: {entity_types}
RELATIONSHIP TYPES: {relationship_types}

For each entity found:
1. Identify the exact text span
2. Classify into one of the provided entity types
3. Assign confidence score (0.0-1.0)

For each relationship:
1. Identify source and target entities
2. Classify the relationship type
3. Extract any relationship properties

Return JSON in this format:
{
  "entities": [
    {"name": "...", "type": "...", "span": "...", "confidence": 0.95}
  ],
  "relationships": [
    {"source": "...", "target": "...", "type": "...", "confidence": 0.9}
  ]
}
"""
```

---

**Previous**: [03 - LLM Configuration](03-llm-configuration.md) | **Next**: [05 - Implementation Patterns](05-implementation-patterns.md) | **Index**: [Architecture](index.md)
