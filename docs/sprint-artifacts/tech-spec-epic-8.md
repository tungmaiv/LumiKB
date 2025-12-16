# Epic 8: GraphRAG Integration - Technical Specification

**Epic ID:** 8
**Created:** 2025-12-08
**Status:** BACKLOG
**Total Story Points:** 63
**Number of Stories:** 15

---

## Executive Summary

Epic 8 introduces Knowledge Graph-Augmented Retrieval (GraphRAG) to LumiKB, enabling structured entity and relationship extraction from documents. This enhancement provides more precise and contextually-aware search results by combining vector similarity (existing) with graph traversal capabilities.

### Key Capabilities

1. **Domain Schema Management** - Define custom entity types and relationships per use case
2. **LLM-Based Entity Extraction** - Extract entities and relationships using LiteLLM-routed models
3. **Graph Storage** - Neo4j Community Edition for entity/relationship persistence
4. **Graph-Augmented Retrieval** - Combine vector search with graph context for enhanced results
5. **Schema Evolution** - Version tracking, drift detection, and batch re-extraction

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LumiKB Application                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────────────────┐   │
│  │   Frontend    │    │   FastAPI     │    │     Celery Workers         │   │
│  │   (Next.js)   │────│   Backend     │────│  - document_processing     │   │
│  │               │    │               │    │  - reprocessing (NEW)      │   │
│  └───────────────┘    └───────────────┘    └───────────────────────────┘   │
│          │                   │                        │                      │
├──────────┼───────────────────┼────────────────────────┼──────────────────────┤
│          │                   │                        │                      │
│  ┌───────▼───────────────────▼────────────────────────▼───────────────────┐ │
│  │                        Service Layer                                    │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │ │
│  │  │  DomainService  │  │EntityExtraction │  │  GraphQueryService      │ │ │
│  │  │                 │  │    Service      │  │                         │ │ │
│  │  │ - CRUD domains  │  │ - LLM extract   │  │ - Entity search         │ │ │
│  │  │ - Clone templ.  │  │ - Deduplication │  │ - Neighborhood expand   │ │ │
│  │  │ - Link to KB    │  │ - Confidence    │  │ - Path finding          │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │ │
│  │  │GraphStorageServ.│  │ RetrievalStrat. │  │  SchemaEvolutionServ.   │ │ │
│  │  │                 │  │    Registry     │  │                         │ │ │
│  │  │ - Store entities│  │ - Vector-only   │  │ - Version tracking      │ │ │
│  │  │ - Store rels    │  │ - Graph-augment │  │ - Drift detection       │ │ │
│  │  │ - Merge/update  │  │ - Auto-select   │  │ - Re-extraction jobs    │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Data Layer                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │   PostgreSQL   │  │    Qdrant      │  │    Neo4j       │  │   Redis    │ │
│  │                │  │                │  │   (NEW)        │  │            │ │
│  │ - Domains      │  │ - Vectors      │  │ - Entities     │  │ - Cache    │ │
│  │ - Entity Types │  │ - Chunks       │  │ - Relationships│  │ - Jobs     │ │
│  │ - KB links     │  │ - Metadata     │  │ - Properties   │  │ - Progress │ │
│  └────────────────┘  └────────────────┘  └────────────────┘  └────────────┘ │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                            External Services                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        LiteLLM Proxy                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │ │
│  │  │   Ollama     │  │   OpenAI     │  │   Gemini     │  │ Anthropic  │ │ │
│  │  │  (local)     │  │  (cloud)     │  │  (cloud)     │  │  (cloud)   │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Document Upload                Entity Extraction                Graph Storage
     │                              │                                │
     ▼                              ▼                                ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐
│ MinIO   │───▶│   Parsing   │───▶│  Chunking   │───▶│  EntityExtraction   │
│ Upload  │    │   Worker    │    │  & Embed    │    │      Service        │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘
                                                              │
                                                              ▼
                                       ┌───────────────────────────────────┐
                                       │  For each chunk:                  │
                                       │  1. Build extraction prompt       │
                                       │  2. Call LLM via LiteLLM          │
                                       │  3. Parse JSON response           │
                                       │  4. Validate against schema       │
                                       │  5. Deduplicate entities          │
                                       │  6. Store in Neo4j                │
                                       └───────────────────────────────────┘
                                                              │
                                                              ▼
                                       ┌───────────────────────────────────┐
                                       │            Neo4j                   │
                                       │  ┌─────────────────────────────┐  │
                                       │  │ (server)-[HOSTS]->(service) │  │
                                       │  │ (service)-[USES]->(db)      │  │
                                       │  │ (incident)-[AFFECTS]->(...) │  │
                                       │  └─────────────────────────────┘  │
                                       └───────────────────────────────────┘
```

### Search Flow with Graph Augmentation

```
User Query                                             Final Results
    │                                                       ▲
    ▼                                                       │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RetrievalStrategyRegistry                            │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     GraphAugmentedRetriever                            │  │
│  │                                                                        │  │
│  │   Step 1: Vector Search (Qdrant)                                       │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │   │  query_embedding = embed(user_query)                            │ │  │
│  │   │  vector_results = qdrant.search(query_embedding, top_k=20)      │ │  │
│  │   │  # Returns: chunk_id, score, doc_id, text                       │ │  │
│  │   └─────────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                         │  │
│  │                              ▼                                         │  │
│  │   Step 2: Extract Entity Context from Vector Results                   │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │   │  For each chunk in vector_results:                              │ │  │
│  │   │    entities = neo4j.get_entities_for_chunk(chunk_id)            │ │  │
│  │   │    # Collect entity IDs mentioned in top results                │ │  │
│  │   └─────────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                         │  │
│  │                              ▼                                         │  │
│  │   Step 3: Graph Expansion (Neighborhood)                               │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │   │  For each entity in extracted_entities:                         │ │  │
│  │   │    neighbors = neo4j.expand_neighborhood(entity, depth=2)       │ │  │
│  │   │    related_chunks = get_chunks_for_entities(neighbors)          │ │  │
│  │   │    # Find additional relevant chunks via graph connections      │ │  │
│  │   └─────────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                         │  │
│  │                              ▼                                         │  │
│  │   Step 4: Merge & Rerank                                               │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │   │  combined = vector_results + graph_expanded_chunks              │ │  │
│  │   │  deduplicated = dedupe_by_chunk_id(combined)                    │ │  │
│  │   │  final = rerank_by_combined_score(deduplicated, alpha=0.7)      │ │  │
│  │   │  # alpha: weight for vector score vs graph relevance            │ │  │
│  │   └─────────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                         │  │
│  └──────────────────────────────┼─────────────────────────────────────────┘  │
│                                 ▼                                            │
│                          Return top_k results                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### PostgreSQL Schema (Domain Management)

```sql
-- Domains: Reusable entity type definitions
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_system_template BOOLEAN DEFAULT FALSE,  -- Built-in templates (read-only)
    is_public BOOLEAN DEFAULT FALSE,           -- Visible to all users
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entity Types within a domain
CREATE TABLE domain_entity_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    attributes JSONB DEFAULT '[]'::jsonb,  -- [{name, type, required, values?}]
    color VARCHAR(7) DEFAULT '#6B7280',    -- Hex color for visualization
    icon VARCHAR(50) DEFAULT 'circle',     -- Lucide icon identifier
    extraction_hints TEXT,                  -- Prompt hints for LLM extraction
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- Relationship Types within a domain
CREATE TABLE domain_relationship_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,                -- e.g., "HOSTS", "USES"
    from_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE CASCADE,
    to_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE CASCADE,
    attributes JSONB DEFAULT '[]'::jsonb,      -- Relationship properties
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- KB-Domain linking (many-to-many)
CREATE TABLE kb_domains (
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    linked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (kb_id, domain_id)
);

-- Document extraction version tracking
CREATE TABLE document_extraction_versions (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    schema_version INTEGER NOT NULL,           -- Domain version at extraction time
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    entity_count INTEGER DEFAULT 0,
    relationship_count INTEGER DEFAULT 0,
    PRIMARY KEY (document_id, domain_id)
);

-- Schema enrichment suggestions
CREATE TABLE schema_enrichment_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(50) NOT NULL,      -- 'new_entity_type', 'new_attribute', 'new_relationship'
    entity_name VARCHAR(100),
    sample_values JSONB,                        -- Example values found
    occurrence_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',      -- 'pending', 'accepted', 'rejected'
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_entity_types_domain ON domain_entity_types(domain_id);
CREATE INDEX idx_relationship_types_domain ON domain_relationship_types(domain_id);
CREATE INDEX idx_kb_domains_kb ON kb_domains(kb_id);
CREATE INDEX idx_kb_domains_domain ON kb_domains(domain_id);
CREATE INDEX idx_doc_extraction_document ON document_extraction_versions(document_id);
CREATE INDEX idx_enrichment_domain_status ON schema_enrichment_suggestions(domain_id, status);
```

### Neo4j Schema

```cypher
// Entity nodes with dynamic labels based on entity type
// Label pattern: EntityType (e.g., :Server, :Service, :Incident)
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// Standard properties on all entity nodes:
// - id: UUID (primary identifier)
// - name: String (display name, extracted from document)
// - domain_id: UUID (reference to PostgreSQL domain)
// - entity_type: String (e.g., "Server", "Service")
// - kb_id: UUID (knowledge base context)
// - source_chunk_ids: [String] (chunks where entity was found)
// - confidence: Float (extraction confidence 0-1)
// - properties: Map (dynamic attributes from schema)
// - created_at: DateTime
// - updated_at: DateTime

// Relationship pattern
// All relationships have:
// - type: Relationship type name (e.g., HOSTS, USES)
// - source_chunk_id: Where relationship was extracted
// - confidence: Float
// - properties: Map (dynamic attributes)

// Example entity creation
CREATE (s:Server:Entity {
    id: $id,
    name: $name,
    domain_id: $domain_id,
    entity_type: 'Server',
    kb_id: $kb_id,
    source_chunk_ids: [$chunk_id],
    confidence: 0.95,
    properties: {hostname: 'web-01', ip_address: '10.0.0.1', environment: 'production'},
    created_at: datetime(),
    updated_at: datetime()
})

// Example relationship creation
MATCH (from:Entity {id: $from_id})
MATCH (to:Entity {id: $to_id})
CREATE (from)-[r:HOSTS {
    source_chunk_id: $chunk_id,
    confidence: 0.92,
    properties: {port: 8080}
}]->(to)

// Indexes for common queries
CREATE INDEX entity_kb_idx IF NOT EXISTS FOR (e:Entity) ON (e.kb_id);
CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);
CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS FOR (e:Entity) ON EACH [e.name];
```

---

## Service Implementations

### EntityExtractionService

```python
# backend/app/services/entity_extraction_service.py
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.integrations.litellm_client import LiteLLMClient
from app.services.domain_service import DomainService

class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    attributes: dict
    confidence: float

class ExtractedRelationship(BaseModel):
    from_entity: str
    to_entity: str
    relationship_type: str
    attributes: dict
    confidence: float

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    unrecognized: List[dict]  # For schema enrichment

class EntityExtractionService:
    def __init__(
        self,
        llm_client: LiteLLMClient,
        domain_service: DomainService
    ):
        self.llm = llm_client
        self.domain_service = domain_service

    async def extract_from_chunk(
        self,
        chunk_text: str,
        chunk_id: str,
        domain_id: UUID,
        kb_id: UUID
    ) -> ExtractionResult:
        """Extract entities and relationships from a text chunk."""

        # Get domain schema
        domain = await self.domain_service.get_domain(domain_id)
        entity_types = await self.domain_service.get_entity_types(domain_id)
        relationship_types = await self.domain_service.get_relationship_types(domain_id)

        # Build extraction prompt
        prompt = self._build_extraction_prompt(
            chunk_text=chunk_text,
            entity_types=entity_types,
            relationship_types=relationship_types
        )

        # Call LLM
        response = await self.llm.chat_completion(
            model=domain.ner_model or "gpt-4o-mini",  # Configurable model
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1  # Low temperature for consistency
        )

        # Parse and validate
        extraction = self._parse_extraction_response(response)
        validated = self._validate_against_schema(extraction, entity_types, relationship_types)

        return validated

    def _build_extraction_prompt(
        self,
        chunk_text: str,
        entity_types: List,
        relationship_types: List
    ) -> str:
        """Build the extraction prompt with schema context."""

        entity_schema = "\n".join([
            f"- {et.name}: {et.description or 'No description'}\n"
            f"  Attributes: {', '.join(a['name'] for a in et.attributes)}\n"
            f"  Hints: {et.extraction_hints or 'None'}"
            for et in entity_types
        ])

        rel_schema = "\n".join([
            f"- {rt.name}: {rt.from_entity_type.name} -> {rt.to_entity_type.name}"
            for rt in relationship_types
        ])

        return f"""Extract entities and relationships from the following text.

## Entity Types to Extract
{entity_schema}

## Relationship Types to Extract
{rel_schema}

## Text to Analyze
{chunk_text}

## Output Format
Return a JSON object with:
- entities: Array of {{name, entity_type, attributes, confidence}}
- relationships: Array of {{from_entity, to_entity, relationship_type, attributes, confidence}}
- unrecognized: Array of potential entities not matching defined types

Only extract entities and relationships explicitly stated or strongly implied in the text.
Assign confidence scores (0-1) based on how explicitly the information is stated."""

    def _get_system_prompt(self) -> str:
        return """You are a precise entity extraction assistant. Your task is to identify
entities and relationships from text according to a predefined schema.

Guidelines:
1. Only extract entities that match the defined entity types
2. Use the exact entity type names from the schema
3. Extract all specified attributes when present
4. Identify relationships between extracted entities
5. Assign confidence scores based on clarity of the text
6. Note potential entities that don't match the schema in 'unrecognized'

Be conservative - only extract what is clearly stated or strongly implied."""
```

### GraphStorageService

```python
# backend/app/services/graph_storage_service.py
from typing import List, Optional
from uuid import UUID, uuid4
from neo4j import AsyncGraphDatabase
from app.core.config import settings

class GraphStorageService:
    def __init__(self):
        self._driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def store_entities(
        self,
        entities: List[ExtractedEntity],
        domain_id: UUID,
        kb_id: UUID,
        chunk_id: str
    ) -> List[str]:
        """Store entities in Neo4j, deduplicating by name within KB."""

        entity_ids = []
        async with self._driver.session() as session:
            for entity in entities:
                # Check for existing entity with same name and type in KB
                existing = await session.run("""
                    MATCH (e:Entity {
                        name: $name,
                        entity_type: $entity_type,
                        kb_id: $kb_id
                    })
                    RETURN e.id AS id, e.source_chunk_ids AS chunks
                """, name=entity.name, entity_type=entity.entity_type, kb_id=str(kb_id))

                record = await existing.single()

                if record:
                    # Merge: update confidence if higher, add chunk to sources
                    entity_id = record["id"]
                    await session.run("""
                        MATCH (e:Entity {id: $id})
                        SET e.source_chunk_ids = e.source_chunk_ids + $chunk_id,
                            e.confidence = CASE
                                WHEN $confidence > e.confidence THEN $confidence
                                ELSE e.confidence
                            END,
                            e.updated_at = datetime()
                    """, id=entity_id, chunk_id=chunk_id, confidence=entity.confidence)
                else:
                    # Create new entity with dynamic label
                    entity_id = str(uuid4())
                    await session.run(f"""
                        CREATE (e:Entity:{entity.entity_type} {{
                            id: $id,
                            name: $name,
                            entity_type: $entity_type,
                            domain_id: $domain_id,
                            kb_id: $kb_id,
                            source_chunk_ids: [$chunk_id],
                            confidence: $confidence,
                            properties: $properties,
                            created_at: datetime(),
                            updated_at: datetime()
                        }})
                    """,
                        id=entity_id,
                        name=entity.name,
                        entity_type=entity.entity_type,
                        domain_id=str(domain_id),
                        kb_id=str(kb_id),
                        chunk_id=chunk_id,
                        confidence=entity.confidence,
                        properties=entity.attributes
                    )

                entity_ids.append(entity_id)

        return entity_ids

    async def store_relationships(
        self,
        relationships: List[ExtractedRelationship],
        kb_id: UUID,
        chunk_id: str
    ) -> int:
        """Store relationships between existing entities."""

        count = 0
        async with self._driver.session() as session:
            for rel in relationships:
                # Find source and target entities
                result = await session.run("""
                    MATCH (from:Entity {name: $from_name, kb_id: $kb_id})
                    MATCH (to:Entity {name: $to_name, kb_id: $kb_id})
                    MERGE (from)-[r:RELATES {type: $rel_type}]->(to)
                    ON CREATE SET
                        r.source_chunk_id = $chunk_id,
                        r.confidence = $confidence,
                        r.properties = $properties,
                        r.created_at = datetime()
                    ON MATCH SET
                        r.confidence = CASE
                            WHEN $confidence > r.confidence THEN $confidence
                            ELSE r.confidence
                        END
                    RETURN r
                """,
                    from_name=rel.from_entity,
                    to_name=rel.to_entity,
                    kb_id=str(kb_id),
                    rel_type=rel.relationship_type,
                    chunk_id=chunk_id,
                    confidence=rel.confidence,
                    properties=rel.attributes
                )
                if await result.single():
                    count += 1

        return count
```

### GraphQueryService

```python
# backend/app/services/graph_query_service.py
from typing import List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel

class EntityResult(BaseModel):
    id: str
    name: str
    entity_type: str
    properties: dict
    confidence: float

class RelationshipResult(BaseModel):
    from_entity: EntityResult
    to_entity: EntityResult
    relationship_type: str
    properties: dict

class GraphQueryService:
    def __init__(self, driver):
        self._driver = driver

    async def search_entities(
        self,
        kb_id: UUID,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[EntityResult]:
        """Full-text search for entities."""

        type_filter = ""
        if entity_types:
            type_filter = f"AND e.entity_type IN {entity_types}"

        async with self._driver.session() as session:
            result = await session.run(f"""
                CALL db.index.fulltext.queryNodes('entity_name_fulltext', $query)
                YIELD node, score
                WHERE node.kb_id = $kb_id {type_filter}
                RETURN node, score
                ORDER BY score DESC
                LIMIT $limit
            """, query=query, kb_id=str(kb_id), limit=limit)

            entities = []
            async for record in result:
                node = record["node"]
                entities.append(EntityResult(
                    id=node["id"],
                    name=node["name"],
                    entity_type=node["entity_type"],
                    properties=node.get("properties", {}),
                    confidence=node["confidence"]
                ))

            return entities

    async def expand_neighborhood(
        self,
        entity_id: str,
        depth: int = 2,
        limit: int = 50
    ) -> Dict:
        """Get entity neighborhood (connected entities and relationships)."""

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (start:Entity {id: $entity_id})
                CALL apoc.path.subgraphAll(start, {
                    maxLevel: $depth,
                    limit: $limit
                })
                YIELD nodes, relationships
                RETURN nodes, relationships
            """, entity_id=entity_id, depth=depth, limit=limit)

            record = await result.single()
            if not record:
                return {"nodes": [], "relationships": []}

            return {
                "nodes": [self._node_to_dict(n) for n in record["nodes"]],
                "relationships": [self._rel_to_dict(r) for r in record["relationships"]]
            }

    async def find_path(
        self,
        from_entity_id: str,
        to_entity_id: str,
        max_depth: int = 5
    ) -> List[Dict]:
        """Find shortest path between two entities."""

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (start:Entity {id: $from_id}), (end:Entity {id: $to_id})
                MATCH path = shortestPath((start)-[*..5]-(end))
                RETURN path
            """, from_id=from_entity_id, to_id=to_entity_id)

            record = await result.single()
            if not record:
                return []

            path = record["path"]
            return self._path_to_list(path)

    async def get_entities_for_chunk(self, chunk_id: str) -> List[EntityResult]:
        """Get all entities extracted from a specific chunk."""

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity)
                WHERE $chunk_id IN e.source_chunk_ids
                RETURN e
            """, chunk_id=chunk_id)

            entities = []
            async for record in result:
                node = record["e"]
                entities.append(EntityResult(
                    id=node["id"],
                    name=node["name"],
                    entity_type=node["entity_type"],
                    properties=node.get("properties", {}),
                    confidence=node["confidence"]
                ))

            return entities
```

### GraphAugmentedRetriever

```python
# backend/app/services/retrieval/graph_augmented_retriever.py
from typing import List, Optional
from uuid import UUID
from app.services.retrieval.base import RetrievalStrategy, SearchResult
from app.services.search_service import SearchService
from app.services.graph_query_service import GraphQueryService

class GraphAugmentedRetriever(RetrievalStrategy):
    """Vector-first with graph context expansion."""

    name = "graph_augmented"
    description = "Combines vector similarity with knowledge graph context"

    def __init__(
        self,
        search_service: SearchService,
        graph_service: GraphQueryService,
        vector_weight: float = 0.7,  # Weight for vector score
        graph_weight: float = 0.3,   # Weight for graph relevance
        expansion_depth: int = 2     # How many hops to expand
    ):
        self.search = search_service
        self.graph = graph_service
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
        self.expansion_depth = expansion_depth

    async def retrieve(
        self,
        query: str,
        kb_ids: List[UUID],
        top_k: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """Execute graph-augmented retrieval."""

        # Step 1: Vector search
        vector_results = await self.search.semantic_search(
            query=query,
            kb_ids=kb_ids,
            top_k=top_k * 2  # Get more for reranking
        )

        # Step 2: Extract entities from top vector results
        entity_ids = set()
        chunk_to_entities = {}

        for result in vector_results[:top_k]:
            entities = await self.graph.get_entities_for_chunk(result.chunk_id)
            chunk_to_entities[result.chunk_id] = entities
            entity_ids.update(e.id for e in entities)

        # Step 3: Expand graph neighborhood
        graph_chunks = set()
        for entity_id in entity_ids:
            neighborhood = await self.graph.expand_neighborhood(
                entity_id=entity_id,
                depth=self.expansion_depth
            )

            # Get chunks for neighboring entities
            for node in neighborhood["nodes"]:
                for chunk_id in node.get("source_chunk_ids", []):
                    graph_chunks.add(chunk_id)

        # Step 4: Retrieve chunks found via graph
        graph_results = []
        for chunk_id in graph_chunks:
            if chunk_id not in {r.chunk_id for r in vector_results}:
                chunk_data = await self.search.get_chunk_by_id(chunk_id)
                if chunk_data:
                    graph_results.append(SearchResult(
                        chunk_id=chunk_id,
                        text=chunk_data.text,
                        score=0.5,  # Base graph score
                        doc_id=chunk_data.doc_id,
                        metadata={"source": "graph_expansion"}
                    ))

        # Step 5: Merge and rerank
        combined = self._merge_results(vector_results, graph_results)
        reranked = self._rerank(combined, query)

        return reranked[:top_k]

    def _merge_results(
        self,
        vector_results: List[SearchResult],
        graph_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Merge vector and graph results, deduplicating by chunk_id."""

        seen = set()
        merged = []

        for result in vector_results:
            if result.chunk_id not in seen:
                result.metadata["source"] = "vector"
                merged.append(result)
                seen.add(result.chunk_id)

        for result in graph_results:
            if result.chunk_id not in seen:
                merged.append(result)
                seen.add(result.chunk_id)

        return merged

    def _rerank(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Rerank results by combined vector + graph score."""

        for result in results:
            if result.metadata.get("source") == "vector":
                final_score = (
                    result.score * self.vector_weight +
                    self.graph_weight  # Bonus for having entities
                )
            else:
                final_score = result.score * self.graph_weight

            result.score = final_score

        return sorted(results, key=lambda r: r.score, reverse=True)
```

### RetrievalStrategyRegistry

```python
# backend/app/services/retrieval/registry.py
from typing import Dict, List, Optional, Type
from uuid import UUID
from app.services.retrieval.base import RetrievalStrategy

class RetrievalStrategyRegistry:
    """Registry for retrieval strategies with auto-selection."""

    _strategies: Dict[str, Type[RetrievalStrategy]] = {}
    _instances: Dict[str, RetrievalStrategy] = {}

    @classmethod
    def register(cls, strategy_class: Type[RetrievalStrategy]):
        """Register a retrieval strategy."""
        cls._strategies[strategy_class.name] = strategy_class
        return strategy_class

    @classmethod
    def get(cls, name: str) -> Optional[RetrievalStrategy]:
        """Get a strategy instance by name."""
        if name not in cls._instances:
            if name in cls._strategies:
                cls._instances[name] = cls._strategies[name]()
        return cls._instances.get(name)

    @classmethod
    def list_strategies(cls) -> List[Dict]:
        """List all available strategies."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "requires_graph": getattr(s, "requires_graph", False)
            }
            for s in cls._strategies.values()
        ]

    @classmethod
    async def auto_select(cls, kb_ids: List[UUID]) -> RetrievalStrategy:
        """Auto-select best strategy based on KB configuration."""

        # Check if any KB has graph enabled
        has_graph = await cls._check_graph_availability(kb_ids)

        if has_graph:
            return cls.get("graph_augmented")

        return cls.get("vector_only")

    @classmethod
    async def _check_graph_availability(cls, kb_ids: List[UUID]) -> bool:
        """Check if any KB has linked domains with entities."""
        from app.services.kb_service import KBService

        kb_service = KBService()
        for kb_id in kb_ids:
            domains = await kb_service.get_linked_domains(kb_id)
            if domains:
                # Check if there are any entities for this KB
                from app.services.graph_query_service import GraphQueryService
                graph = GraphQueryService()
                count = await graph.count_entities_for_kb(kb_id)
                if count > 0:
                    return True

        return False
```

---

## API Endpoints

### Domain Management

```
# Domain CRUD
POST   /api/v1/domains                     - Create new domain
GET    /api/v1/domains                     - List domains (user's + public)
GET    /api/v1/domains/{id}                - Get domain details
PUT    /api/v1/domains/{id}                - Update domain
DELETE /api/v1/domains/{id}                - Delete domain (if no KBs linked)

# Entity Types
POST   /api/v1/domains/{id}/entity-types   - Add entity type
GET    /api/v1/domains/{id}/entity-types   - List entity types
PUT    /api/v1/domains/{id}/entity-types/{type_id}  - Update entity type
DELETE /api/v1/domains/{id}/entity-types/{type_id}  - Delete entity type

# Relationship Types
POST   /api/v1/domains/{id}/relationship-types   - Add relationship type
GET    /api/v1/domains/{id}/relationship-types   - List relationship types
PUT    /api/v1/domains/{id}/relationship-types/{rel_id}  - Update relationship type
DELETE /api/v1/domains/{id}/relationship-types/{rel_id}  - Delete relationship type

# Domain Cloning
POST   /api/v1/domains/{id}/clone          - Clone domain (from template)

# KB Linking
POST   /api/v1/knowledge-bases/{kb_id}/domains/{domain_id}  - Link domain to KB
DELETE /api/v1/knowledge-bases/{kb_id}/domains/{domain_id}  - Unlink domain from KB
GET    /api/v1/knowledge-bases/{kb_id}/domains              - List linked domains
```

### LLM Recommendations

```
# Schema Recommendations
POST   /api/v1/domains/recommend           - Get LLM domain recommendations
{
  "description": "IT operations documentation",
  "sample_documents": ["doc_id_1", "doc_id_2"]
}

# Schema Enrichment
GET    /api/v1/domains/{id}/enrichment-suggestions  - Get unrecognized entity suggestions
POST   /api/v1/domains/{id}/enrichment-suggestions/{suggestion_id}/accept  - Accept suggestion
POST   /api/v1/domains/{id}/enrichment-suggestions/{suggestion_id}/reject  - Reject suggestion
```

### Graph Operations

```
# Graph Query
POST   /api/v1/knowledge-bases/{kb_id}/graph/search  - Search entities
GET    /api/v1/knowledge-bases/{kb_id}/graph/entities/{id}  - Get entity details
GET    /api/v1/knowledge-bases/{kb_id}/graph/entities/{id}/neighborhood  - Get neighbors
POST   /api/v1/knowledge-bases/{kb_id}/graph/path    - Find path between entities

# Graph Stats
GET    /api/v1/knowledge-bases/{kb_id}/graph/stats   - Get entity/relationship counts
```

### Schema Evolution

```
# Re-extraction
POST   /api/v1/knowledge-bases/{kb_id}/reextract     - Trigger re-extraction job
{
  "mode": "incremental",  // or "full"
  "domain_id": "uuid",
  "document_ids": ["uuid"] // optional, all if empty
}

# Job Progress
GET    /api/v1/jobs/{job_id}/progress                - Get re-extraction progress

# Schema Drift
GET    /api/v1/knowledge-bases/{kb_id}/schema-drift  - Check for outdated documents
```

---

## Docker Compose Changes

```yaml
# infrastructure/docker/docker-compose.yml (additions)

neo4j:
  image: neo4j:5-community
  container_name: lumikb-neo4j
  ports:
    - "7474:7474"  # HTTP Browser
    - "7687:7687"  # Bolt protocol
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-lumikb_dev_password}
    - NEO4J_PLUGINS=["apoc"]
    - NEO4J_dbms_security_procedures_unrestricted=apoc.*
    - NEO4J_dbms_memory_heap_initial__size=512m
    - NEO4J_dbms_memory_heap_max__size=1G
  volumes:
    - lumikb-neo4j-data:/data
    - lumikb-neo4j-logs:/logs
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:7474"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - lumikb-network

celery-reprocessing:
  build:
    context: ../../backend
    dockerfile: Dockerfile
  container_name: lumikb-celery-reprocessing
  command: celery -A app.workers.celery_app worker -Q reprocessing -c 2 --loglevel=info
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USER=neo4j
    - NEO4J_PASSWORD=${NEO4J_PASSWORD:-lumikb_dev_password}
    - LITELLM_API_BASE=http://litellm:4000
  depends_on:
    - redis
    - postgres
    - neo4j
    - litellm
  volumes:
    - ../../backend:/app
  networks:
    - lumikb-network
  deploy:
    resources:
      limits:
        memory: 2G

volumes:
  lumikb-neo4j-data:
  lumikb-neo4j-logs:
```

---

## Non-Functional Requirements

### Performance

| Metric | Target | Context |
|--------|--------|---------|
| Entity extraction latency | < 2s per chunk | Single chunk with 5-10 entity types |
| Graph query response | < 200ms | Entity search, neighborhood expansion |
| Neo4j connection pool | 10-50 connections | Based on concurrent worker count |
| Graph-augmented search | < 500ms additional | Over base vector search time |
| Batch re-extraction throughput | 100 chunks/min | With rate limiting per LLM provider |
| Neo4j memory usage | < 1GB heap | For up to 100K entities per KB |

### Security

| Requirement | Implementation | Story |
|-------------|----------------|-------|
| Neo4j Authentication | Username/password via environment variables | 8-1 |
| Neo4j Network Isolation | Internal Docker network only, no external port exposure in prod | 8-1 |
| LLM API Key Handling | Keys stored encrypted in PostgreSQL (pgcrypto), passed via LiteLLM proxy | 8-4, 8-8 |
| Domain Access Control | Users can only access own domains + public domains | 8-5 |
| KB-Domain Permission | Only KB owners/admins can link/unlink domains | 8-7 |
| Entity Isolation | Entities scoped to kb_id, no cross-KB leakage | 8-8 |
| Audit Logging | All domain CRUD, KB linking, extraction operations logged | 8-5, 8-7 |
| Input Sanitization | Cypher query parameters always parameterized, no string interpolation | 8-10 |
| Extraction Prompt Injection | LLM prompts sanitized, user content wrapped in clear delimiters | 8-8 |

### Reliability/Availability

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Neo4j Health Check | < 10s detection | Docker healthcheck with wget |
| Graceful Degradation | Graph features disabled if Neo4j unavailable | Strategy registry fallback to vector-only |
| Extraction Retry | 3 attempts with exponential backoff | Celery task retry configuration |
| Connection Pool Recovery | Auto-reconnect on Neo4j restart | neo4j-driver built-in retry |
| Data Consistency | PostgreSQL as source of truth for domains | Neo4j rebuilt from extraction versions if needed |

### Observability

| Metric | Type | Labels |
|--------|------|--------|
| `lumikb_entity_extraction_duration_seconds` | Histogram | kb_id, domain_id, status |
| `lumikb_entity_extraction_count` | Counter | kb_id, entity_type |
| `lumikb_relationship_count` | Counter | kb_id, relationship_type |
| `lumikb_graph_query_duration_seconds` | Histogram | query_type (search, expand, path) |
| `lumikb_neo4j_connection_pool_active` | Gauge | - |
| `lumikb_reextraction_job_progress` | Gauge | job_id, kb_id |

**Logging:**
- Structured JSON logs for all graph operations
- Entity extraction results logged with chunk_id, entity count, confidence scores
- Graph query performance logged at DEBUG level

---

## Acceptance Criteria (Authoritative)

### Story 8-1: Neo4j Docker Infrastructure
1. **AC-8.1.1**: Neo4j 5 Community Edition container starts via docker-compose
2. **AC-8.1.2**: APOC plugin enabled and functional
3. **AC-8.1.3**: Python neo4j-driver connects successfully from backend
4. **AC-8.1.4**: Health check endpoint responds within 10s
5. **AC-8.1.5**: Data persists across container restarts via named volume

### Story 8-2: Domain Data Model
1. **AC-8.2.1**: `domains` table created with all specified columns
2. **AC-8.2.2**: `domain_entity_types` table supports JSONB attributes
3. **AC-8.2.3**: `domain_relationship_types` table links entity types
4. **AC-8.2.4**: `kb_domains` junction table enables many-to-many linking
5. **AC-8.2.5**: All foreign keys and indexes created per schema
6. **AC-8.2.6**: Alembic migration reversible

### Story 8-3: System Domain Templates
1. **AC-8.3.1**: IT Operations template seeded with Server, Service, Incident, Database entity types
2. **AC-8.3.2**: Legal Contracts template seeded with Party, Clause, Obligation entity types
3. **AC-8.3.3**: Sales & CRM template seeded with Company, Contact, Deal entity types
4. **AC-8.3.4**: Project Management template seeded with Task, Milestone, Resource entity types
5. **AC-8.3.5**: HR & People template seeded with Employee, Department, Role entity types
6. **AC-8.3.6**: All templates marked `is_system_template=true` and `is_public=true`

### Story 8-4: LLM Domain Recommendation
1. **AC-8.4.1**: POST /api/v1/domains/recommend accepts description and sample doc IDs
2. **AC-8.4.2**: LLM returns suggested entity types with names, descriptions, attributes
3. **AC-8.4.3**: LLM returns suggested relationship types between entities
4. **AC-8.4.4**: Response includes confidence scores for each suggestion
5. **AC-8.4.5**: Similar system templates suggested if applicable
6. **AC-8.4.6**: Request timeout < 30s with graceful error handling

### Story 8-5: Domain Management API
1. **AC-8.5.1**: CRUD endpoints for domains return proper HTTP status codes
2. **AC-8.5.2**: Entity type CRUD nested under domain routes
3. **AC-8.5.3**: Relationship type CRUD validates from/to entity type existence
4. **AC-8.5.4**: Domain deletion blocked if KBs are linked (409 Conflict)
5. **AC-8.5.5**: Clone endpoint copies all entity/relationship types
6. **AC-8.5.6**: List endpoint filters by user ownership and public visibility

### Story 8-6: Domain Management UI
1. **AC-8.6.1**: Domain list page shows user's domains and public templates
2. **AC-8.6.2**: Create domain wizard with name, description, clone-from-template option
3. **AC-8.6.3**: Entity type editor with name, description, color, icon, attributes form
4. **AC-8.6.4**: Relationship type editor with from/to entity dropdowns
5. **AC-8.6.5**: Visual schema preview using graph visualization library
6. **AC-8.6.6**: Delete confirmation with KB dependency warning

### Story 8-7: KB-Domain Linking
1. **AC-8.7.1**: KB settings page shows linked domains section
2. **AC-8.7.2**: Link domain dropdown shows available domains
3. **AC-8.7.3**: Multiple domains can be linked to single KB
4. **AC-8.7.4**: Unlink triggers re-extraction prompt for affected documents
5. **AC-8.7.5**: Link/unlink operations require KB write permission
6. **AC-8.7.6**: Linked domains visible in KB details response

### Story 8-8: Entity Extraction Service
1. **AC-8.8.1**: EntityExtractionService.extract_from_chunk() returns entities and relationships
2. **AC-8.8.2**: Extraction prompt built dynamically from domain schema
3. **AC-8.8.3**: LLM response parsed and validated against schema
4. **AC-8.8.4**: Entities deduplicated by name within KB (merge, don't duplicate)
5. **AC-8.8.5**: Confidence scores assigned based on extraction clarity
6. **AC-8.8.6**: Unrecognized entities captured for enrichment suggestions

### Story 8-9: Document Processing Graph Integration
1. **AC-8.9.1**: Entity extraction task added to Celery document processing pipeline
2. **AC-8.9.2**: Extraction runs after chunking, before completion
3. **AC-8.9.3**: Entities stored in Neo4j with source_chunk_ids
4. **AC-8.9.4**: Relationships stored with chunk provenance
5. **AC-8.9.5**: document_extraction_versions table updated on completion
6. **AC-8.9.6**: Processing continues if extraction fails (graceful degradation)

### Story 8-10: Graph Query Service
1. **AC-8.10.1**: search_entities() returns entities matching full-text query
2. **AC-8.10.2**: expand_neighborhood() returns connected entities up to depth
3. **AC-8.10.3**: find_path() returns shortest path between two entities
4. **AC-8.10.4**: get_entities_for_chunk() returns all entities from chunk
5. **AC-8.10.5**: All queries parameterized (no Cypher injection)
6. **AC-8.10.6**: Query results include confidence scores

### Story 8-11: Graph-Augmented Retrieval
1. **AC-8.11.1**: GraphAugmentedRetriever executes vector search first
2. **AC-8.11.2**: Entities extracted from top vector results
3. **AC-8.11.3**: Graph neighborhood expanded for found entities
4. **AC-8.11.4**: Additional chunks discovered via graph connections
5. **AC-8.11.5**: Results merged and reranked by combined score
6. **AC-8.11.6**: Configurable vector_weight and graph_weight parameters

### Story 8-12: Retrieval Strategy Abstraction
1. **AC-8.12.1**: RetrievalStrategy base class defines retrieve() interface
2. **AC-8.12.2**: RetrievalStrategyRegistry.register() adds strategies
3. **AC-8.12.3**: RetrievalStrategyRegistry.get() returns strategy by name
4. **AC-8.12.4**: auto_select() chooses graph-augmented if KB has entities
5. **AC-8.12.5**: auto_select() falls back to vector-only if no graph data
6. **AC-8.12.6**: Strategy selection overridable via search API parameter

### Story 8-13: LLM Schema Enrichment
1. **AC-8.13.1**: Unrecognized entities from extraction stored as suggestions
2. **AC-8.13.2**: GET endpoint returns pending enrichment suggestions
3. **AC-8.13.3**: Accept suggestion creates new entity type in domain
4. **AC-8.13.4**: Reject suggestion marks as rejected with reviewer
5. **AC-8.13.5**: Duplicate suggestions incremented occurrence_count
6. **AC-8.13.6**: Suggestions grouped by entity name with sample values

### Story 8-14: Schema Evolution & Re-extraction
1. **AC-8.14.1**: Domain version incremented on entity/relationship type changes
2. **AC-8.14.2**: schema-drift endpoint identifies outdated documents
3. **AC-8.14.3**: POST reextract triggers Celery job for selected documents
4. **AC-8.14.4**: Incremental mode only processes docs older than schema version
5. **AC-8.14.5**: Full mode clears existing entities and re-extracts all
6. **AC-8.14.6**: Job progress trackable via GET /jobs/{id}/progress

### Story 8-15: Batch Reprocessing Worker
1. **AC-8.15.1**: Dedicated Celery queue 'reprocessing' for re-extraction jobs
2. **AC-8.15.2**: Worker concurrency limited to 2 to avoid LLM overload
3. **AC-8.15.3**: Rate limiting configurable per LLM provider
4. **AC-8.15.4**: Progress stored in Redis with document count and completion %
5. **AC-8.15.5**: Job cancellation supported via Celery revoke
6. **AC-8.15.6**: Failed documents logged but don't block job completion

---

## Test Strategy

### Unit Tests

| Story | Test Area | Target Coverage |
|-------|-----------|-----------------|
| 8-2 | Domain models, schemas | 90% |
| 8-4 | LLM recommendation parsing | 85% |
| 8-5 | Domain CRUD validation | 90% |
| 8-8 | Entity extraction parsing | 90% |
| 8-10 | Cypher query generation | 85% |
| 8-11 | Result merging/reranking | 90% |
| 8-12 | Strategy selection logic | 85% |
| 8-13 | Enrichment detection | 80% |
| 8-14 | Version comparison | 85% |
| 8-15 | Progress calculation | 80% |

### Integration Tests

| Story | Test Area | Dependencies |
|-------|-----------|--------------|
| 8-1 | Neo4j connectivity | Docker Neo4j |
| 8-3 | Template seeding | PostgreSQL + migrations |
| 8-5 | API endpoint coverage | FastAPI TestClient |
| 8-7 | KB-Domain linking | PostgreSQL + Qdrant |
| 8-8 | Entity extraction + storage | LiteLLM + Neo4j |
| 8-9 | Celery task execution | Redis + Celery |
| 8-11 | Full retrieval flow | All services |
| 8-14 | Re-extraction job | Celery + Neo4j |

### E2E Tests

| Story | User Journey |
|-------|--------------|
| 8-6 | Create domain via UI, add entity types, visualize |
| 8-7 | Link domain to KB, verify extraction on upload |
| 8-11 | Search query, verify graph-augmented results |
| 8-13 | Review enrichment suggestions, accept/reject |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM extraction quality varies | HIGH | MEDIUM | Confidence thresholds, human review for low confidence |
| Neo4j performance under load | MEDIUM | LOW | Connection pooling, query optimization, indexes |
| Graph complexity explosion | MEDIUM | MEDIUM | Limit entity count per chunk, max expansion depth |
| Schema drift detection false positives | LOW | MEDIUM | Configurable thresholds, manual override |
| Re-extraction overwhelms LLM | HIGH | MEDIUM | Rate limiting, dedicated queue, batch scheduling |

---

## Story Dependencies

```
8-1 (Neo4j Infrastructure)
  └── 8-2 (Domain Data Model)
        └── 8-3 (System Templates)
        └── 8-4 (LLM Recommendation)
        └── 8-5 (Domain API)
              └── 8-6 (Domain UI)
              └── 8-7 (KB-Domain Linking)
                    └── 8-8 (Entity Extraction)
                          └── 8-9 (Doc Processing Integration)
                          └── 8-10 (Graph Query)
                                └── 8-11 (Graph-Augmented Retrieval)
                                      └── 8-12 (Strategy Abstraction)
                          └── 8-13 (Schema Enrichment)
                          └── 8-14 (Schema Evolution)
                                └── 8-15 (Batch Worker)
```

---

## Traceability Matrix

| Requirement | Stories | Description |
|-------------|---------|-------------|
| FR-GRAPH-1 | 8-1 | Neo4j infrastructure |
| FR-GRAPH-2 | 8-2, 8-5 | Domain schema management |
| FR-GRAPH-3 | 8-3 | Pre-built domain templates |
| FR-GRAPH-4 | 8-4 | LLM schema recommendations |
| FR-GRAPH-5 | 8-6, 8-7 | Domain UI and KB linking |
| FR-GRAPH-6 | 8-8, 8-9 | Entity extraction pipeline |
| FR-GRAPH-7 | 8-10 | Graph query capabilities |
| FR-GRAPH-8 | 8-11 | Graph-augmented retrieval |
| FR-GRAPH-9 | 8-12 | Strategy abstraction |
| FR-GRAPH-10 | 8-13 | Schema enrichment suggestions |
| FR-GRAPH-11 | 8-14, 8-15 | Schema evolution and re-extraction |

---

## Open Questions

1. **Entity Deduplication Strategy** - Should entities be deduplicated across KBs or only within a single KB?
   - Current decision: Within KB only to maintain isolation

2. **Graph Visualization Library** - Which library for schema editor visualization?
   - Options: react-force-graph, Cytoscape.js, D3.js
   - To be decided in Story 8-6

3. **NER Model Selection** - Which model provides best extraction quality?
   - Need benchmarking in Story 8-8
   - Candidates: GPT-4o-mini, Claude 3 Haiku, local Ollama models

4. **Re-extraction Scheduling** - Should re-extraction be automatic on schema change or manual trigger?
   - Current decision: Manual trigger with optional scheduled checks

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08
**Author:** BMAD Agent Collaboration
