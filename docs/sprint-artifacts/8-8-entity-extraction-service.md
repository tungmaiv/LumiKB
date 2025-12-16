# Story 8-8: Per-KB Entity Extraction Service

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-8
**Priority:** HIGH (Core Feature)
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Implement the core entity extraction service that uses LLM to identify entities and relationships from document chunks based on the KB's linked domain schema. Extracted entities are stored in Neo4j.

---

## Acceptance Criteria

### AC1: Domain-Aware Extraction
**Given** a document chunk is processed
**When** entity extraction runs
**Then** the LLM is prompted with:
  - The chunk text
  - The domain's entity type definitions
  - The domain's relationship type definitions
  - Extraction hints for each entity type
**And** only entities matching the domain schema are extracted

### AC2: Entity Storage in Neo4j
**Given** entities are extracted from a chunk
**When** storage occurs
**Then** each entity is stored as a Neo4j node with:
  - Unique ID (UUID)
  - Label matching the entity type name
  - Properties from extracted attributes
  - Source document reference (document_id, chunk_id)
  - KB reference (kb_id)
  - Extraction confidence score

### AC3: Relationship Storage in Neo4j
**Given** relationships are extracted between entities
**When** storage occurs
**Then** each relationship is stored as a Neo4j edge with:
  - Type matching the relationship type name
  - Properties from extracted attributes
  - Source reference (document_id, chunk_id)
  - Extraction confidence score

### AC4: Entity Deduplication
**Given** the same entity appears in multiple chunks
**When** extraction identifies a potential duplicate
**Then** the service:
  - Compares entity names and key attributes
  - Uses fuzzy matching for near-duplicates
  - Merges duplicate entities into one node
  - Tracks all source references on the merged node

### AC5: Extraction Prompt Design
**Given** the LLM needs clear instructions
**When** the extraction prompt is built
**Then** it includes:
  - System instructions for NER task
  - Entity type definitions with examples
  - Relationship type definitions
  - Output format specification (JSON)
  - Confidence scoring instructions

### AC6: LiteLLM NER Model Integration
**Given** the Model Registry (Story 7-9) has NER models
**When** extraction runs
**Then** the configured NER model is used
**And** if no NER model is configured, fallback to generation model
**And** model selection is logged for audit

---

## Technical Notes

### Extraction Prompt Template

```python
ENTITY_EXTRACTION_PROMPT = """
You are an expert entity extraction system. Analyze the following text and extract entities and relationships according to the provided schema.

## Entity Types to Extract:
{entity_types_json}

## Relationship Types to Extract:
{relationship_types_json}

## Text to Analyze:
{chunk_text}

## Instructions:
1. Identify all entities matching the defined types
2. Extract attributes for each entity as specified
3. Identify relationships between extracted entities
4. Assign confidence scores (0.0-1.0) based on extraction certainty
5. Return results in the specified JSON format

## Output Format:
{
  "entities": [
    {
      "type": "EntityTypeName",
      "name": "Entity identifier",
      "attributes": {"attr1": "value1"},
      "confidence": 0.95
    }
  ],
  "relationships": [
    {
      "type": "RELATIONSHIP_NAME",
      "from_entity": "Entity name",
      "to_entity": "Another entity name",
      "attributes": {},
      "confidence": 0.88
    }
  ]
}

Only extract entities and relationships that clearly match the schema definitions.
"""
```

### Neo4j Storage Service

```python
# backend/app/services/graph_storage_service.py
class GraphStorageService:
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

    async def store_entities(
        self,
        kb_id: UUID,
        document_id: UUID,
        chunk_id: str,
        entities: List[ExtractedEntity]
    ) -> List[UUID]:
        """Store extracted entities in Neo4j."""
        entity_ids = []

        async with self.neo4j.session() as session:
            for entity in entities:
                # Check for existing entity (deduplication)
                existing = await self._find_similar_entity(
                    session, kb_id, entity.type, entity.name
                )

                if existing:
                    # Merge: add new source reference
                    await self._add_source_reference(
                        session, existing['id'], document_id, chunk_id
                    )
                    entity_ids.append(existing['id'])
                else:
                    # Create new entity node
                    entity_id = await self._create_entity_node(
                        session, kb_id, document_id, chunk_id, entity
                    )
                    entity_ids.append(entity_id)

        return entity_ids

    async def _create_entity_node(
        self,
        session,
        kb_id: UUID,
        document_id: UUID,
        chunk_id: str,
        entity: ExtractedEntity
    ) -> UUID:
        """Create a new entity node in Neo4j."""
        entity_id = uuid4()

        # Dynamic label based on entity type
        query = f"""
        CREATE (n:{entity.type} {{
            id: $id,
            name: $name,
            kb_id: $kb_id,
            confidence: $confidence,
            source_documents: [$document_id],
            source_chunks: [$chunk_id],
            created_at: datetime()
        }})
        SET n += $attributes
        RETURN n.id as id
        """

        await session.run(query, {
            'id': str(entity_id),
            'name': entity.name,
            'kb_id': str(kb_id),
            'confidence': entity.confidence,
            'document_id': str(document_id),
            'chunk_id': chunk_id,
            'attributes': entity.attributes
        })

        return entity_id

    async def store_relationships(
        self,
        kb_id: UUID,
        document_id: UUID,
        chunk_id: str,
        relationships: List[ExtractedRelationship],
        entity_name_to_id: Dict[str, UUID]
    ):
        """Store extracted relationships in Neo4j."""
        async with self.neo4j.session() as session:
            for rel in relationships:
                from_id = entity_name_to_id.get(rel.from_entity)
                to_id = entity_name_to_id.get(rel.to_entity)

                if not from_id or not to_id:
                    continue  # Skip if entities not found

                query = f"""
                MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                MERGE (a)-[r:{rel.type}]->(b)
                SET r.kb_id = $kb_id,
                    r.confidence = $confidence,
                    r.source_document = $document_id,
                    r.source_chunk = $chunk_id
                SET r += $attributes
                """

                await session.run(query, {
                    'from_id': str(from_id),
                    'to_id': str(to_id),
                    'kb_id': str(kb_id),
                    'confidence': rel.confidence,
                    'document_id': str(document_id),
                    'chunk_id': chunk_id,
                    'attributes': rel.attributes
                })
```

### Entity Deduplication

```python
async def _find_similar_entity(
    self,
    session,
    kb_id: UUID,
    entity_type: str,
    entity_name: str
) -> Optional[Dict]:
    """Find existing entity by name similarity."""
    query = f"""
    MATCH (n:{entity_type} {{kb_id: $kb_id}})
    WHERE toLower(n.name) = toLower($name)
       OR apoc.text.jaroWinklerDistance(toLower(n.name), toLower($name)) > 0.9
    RETURN n.id as id, n.name as name
    LIMIT 1
    """

    result = await session.run(query, {
        'kb_id': str(kb_id),
        'name': entity_name
    })

    record = await result.single()
    return dict(record) if record else None
```

---

## Definition of Done

- [ ] Extraction prompt template designed
- [ ] LLM integration via LiteLLM
- [ ] Neo4j entity storage implemented
- [ ] Neo4j relationship storage implemented
- [ ] Entity deduplication logic
- [ ] Confidence score tracking
- [ ] Source reference tracking (document, chunk)
- [ ] KB isolation (entities scoped to KB)
- [ ] Error handling for LLM failures
- [ ] Unit tests with mocked LLM
- [ ] Integration tests with Neo4j
- [ ] Performance baseline (extractions/second)

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-1 (Neo4j), Story 8-7 (KB-Domain Linking), Story 7-9 (Model Registry)
**Next Story:** Story 8-9 (Document Processing Graph Integration)
