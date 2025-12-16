# Story 8-10: Graph Query Service

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-10
**Priority:** HIGH
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Implement a service for querying the Neo4j knowledge graph to retrieve entities, relationships, and graph neighborhoods. This service provides the graph data that augments vector search results.

---

## Acceptance Criteria

### AC1: Entity Search by Name
**Given** a search query
**When** entity search is performed
**Then** entities matching the query are returned with:
  - Entity ID, type, and name
  - Attributes
  - Confidence score
  - Source document references
**And** results are scoped to the specified KB

### AC2: Entity Neighborhood Query
**Given** an entity ID
**When** neighborhood query is performed
**Then** the response includes:
  - The entity's direct relationships
  - Connected entities (1-hop neighbors)
  - Relationship types and directions
  - Optionally: 2-hop neighbors

### AC3: Path Finding
**Given** two entity IDs
**When** path query is performed
**Then** the shortest path between entities is returned
**And** all intermediate nodes and relationships are included
**And** max path length is configurable (default: 5)

### AC4: Subgraph Extraction
**Given** a list of entity IDs
**When** subgraph extraction is requested
**Then** the response includes:
  - All specified entities
  - All relationships between them
  - Optionally: 1-hop expansion from each entity

### AC5: KB Scoping
**Given** all graph queries
**When** executed
**Then** results are filtered to the specified KB
**And** users can only query KBs they have read access to
**And** cross-KB queries are not allowed

### AC6: Query Performance
**Given** graph queries
**When** executed against large graphs
**Then** response time is < 500ms for typical queries
**And** result counts are limited (default: 100)
**And** pagination is supported for large result sets

---

## Technical Notes

### Service Implementation

```python
# backend/app/services/graph_query_service.py
from typing import List, Optional
from uuid import UUID

class GraphQueryService:
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

    async def search_entities(
        self,
        kb_id: UUID,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[EntityResult]:
        """Search entities by name within a KB."""
        type_filter = ""
        if entity_types:
            type_filter = f"AND any(label IN labels(n) WHERE label IN {entity_types})"

        cypher = f"""
        MATCH (n)
        WHERE n.kb_id = $kb_id
          AND toLower(n.name) CONTAINS toLower($query)
          {type_filter}
        RETURN n.id as id, labels(n)[0] as type, n.name as name,
               n.confidence as confidence, n.source_documents as sources,
               properties(n) as attributes
        ORDER BY n.confidence DESC
        SKIP $offset
        LIMIT $limit
        """

        async with self.neo4j.session() as session:
            result = await session.run(cypher, {
                'kb_id': str(kb_id),
                'query': query,
                'offset': offset,
                'limit': limit
            })
            return [EntityResult(**record) async for record in result]

    async def get_entity_neighborhood(
        self,
        kb_id: UUID,
        entity_id: UUID,
        depth: int = 1,
        limit: int = 50
    ) -> EntityNeighborhood:
        """Get entity with its relationships and neighbors."""
        cypher = f"""
        MATCH (center {{id: $entity_id, kb_id: $kb_id}})
        OPTIONAL MATCH (center)-[r]-(neighbor)
        WHERE neighbor.kb_id = $kb_id
        WITH center, collect(DISTINCT {{
            relationship: type(r),
            direction: CASE WHEN startNode(r) = center THEN 'outgoing' ELSE 'incoming' END,
            neighbor_id: neighbor.id,
            neighbor_type: labels(neighbor)[0],
            neighbor_name: neighbor.name
        }})[0..$limit] as connections
        RETURN center, connections
        """

        async with self.neo4j.session() as session:
            result = await session.run(cypher, {
                'entity_id': str(entity_id),
                'kb_id': str(kb_id),
                'limit': limit
            })
            record = await result.single()
            return EntityNeighborhood(
                entity=record['center'],
                connections=record['connections']
            )

    async def find_path(
        self,
        kb_id: UUID,
        from_entity_id: UUID,
        to_entity_id: UUID,
        max_depth: int = 5
    ) -> Optional[GraphPath]:
        """Find shortest path between two entities."""
        cypher = f"""
        MATCH path = shortestPath(
            (a {{id: $from_id, kb_id: $kb_id}})-[*1..{max_depth}]-(b {{id: $to_id, kb_id: $kb_id}})
        )
        RETURN nodes(path) as nodes, relationships(path) as rels
        """

        async with self.neo4j.session() as session:
            result = await session.run(cypher, {
                'from_id': str(from_entity_id),
                'to_id': str(to_entity_id),
                'kb_id': str(kb_id)
            })
            record = await result.single()
            if record:
                return GraphPath(
                    nodes=record['nodes'],
                    relationships=record['rels']
                )
            return None

    async def extract_subgraph(
        self,
        kb_id: UUID,
        entity_ids: List[UUID],
        expand_hops: int = 0
    ) -> Subgraph:
        """Extract subgraph containing specified entities."""
        if expand_hops == 0:
            # Just the entities and relationships between them
            cypher = """
            MATCH (n)
            WHERE n.id IN $entity_ids AND n.kb_id = $kb_id
            WITH collect(n) as nodes
            MATCH (a)-[r]-(b)
            WHERE a IN nodes AND b IN nodes
            RETURN nodes, collect(DISTINCT r) as relationships
            """
        else:
            # Expand N hops from each entity
            cypher = f"""
            MATCH (center)
            WHERE center.id IN $entity_ids AND center.kb_id = $kb_id
            CALL {{
                WITH center
                MATCH path = (center)-[*0..{expand_hops}]-(neighbor)
                WHERE neighbor.kb_id = $kb_id
                RETURN collect(DISTINCT neighbor) as expanded
            }}
            WITH center, expanded
            UNWIND (expanded + [center]) as n
            WITH collect(DISTINCT n) as nodes
            MATCH (a)-[r]-(b)
            WHERE a IN nodes AND b IN nodes
            RETURN nodes, collect(DISTINCT r) as relationships
            """

        async with self.neo4j.session() as session:
            result = await session.run(cypher, {
                'entity_ids': [str(eid) for eid in entity_ids],
                'kb_id': str(kb_id)
            })
            record = await result.single()
            return Subgraph(
                nodes=record['nodes'],
                relationships=record['relationships']
            )
```

### API Endpoints

```python
# backend/app/api/v1/graph.py

@router.get("/entities/search")
async def search_entities(
    kb_id: UUID,
    q: str,
    entity_types: Optional[List[str]] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search entities in KB knowledge graph."""
    await verify_kb_read_access(kb_id, current_user, db)

    service = GraphQueryService(get_neo4j())
    return await service.search_entities(kb_id, q, entity_types, limit, offset)

@router.get("/entities/{entity_id}/neighborhood")
async def get_neighborhood(
    entity_id: UUID,
    kb_id: UUID,
    depth: int = Query(1, le=3),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get entity neighborhood (connected entities and relationships)."""
    await verify_kb_read_access(kb_id, current_user, db)

    service = GraphQueryService(get_neo4j())
    return await service.get_entity_neighborhood(kb_id, entity_id, depth, limit)

@router.get("/path")
async def find_path(
    kb_id: UUID,
    from_entity: UUID,
    to_entity: UUID,
    max_depth: int = Query(5, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Find shortest path between two entities."""
    await verify_kb_read_access(kb_id, current_user, db)

    service = GraphQueryService(get_neo4j())
    path = await service.find_path(kb_id, from_entity, to_entity, max_depth)

    if not path:
        raise HTTPException(404, "No path found between entities")

    return path
```

### Response Schemas

```python
# backend/app/schemas/graph.py
class EntityResult(BaseModel):
    id: UUID
    type: str
    name: str
    attributes: Dict[str, Any]
    confidence: float
    source_documents: List[UUID]

class EntityNeighborhood(BaseModel):
    entity: EntityResult
    connections: List[ConnectionInfo]

class ConnectionInfo(BaseModel):
    relationship: str
    direction: Literal["incoming", "outgoing"]
    neighbor_id: UUID
    neighbor_type: str
    neighbor_name: str

class GraphPath(BaseModel):
    nodes: List[EntityResult]
    relationships: List[RelationshipInfo]
    length: int

class Subgraph(BaseModel):
    nodes: List[EntityResult]
    relationships: List[RelationshipInfo]
```

---

## Definition of Done

- [ ] Entity search endpoint implemented
- [ ] Neighborhood query endpoint implemented
- [ ] Path finding endpoint implemented
- [ ] Subgraph extraction endpoint implemented
- [ ] KB access control enforced
- [ ] Query limits and pagination
- [ ] Response schemas defined
- [ ] Performance < 500ms for typical queries
- [ ] Unit tests for query service
- [ ] Integration tests with Neo4j
- [ ] API documentation updated

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-8 (Entity Extraction), Story 8-1 (Neo4j Infrastructure)
**Next Story:** Story 8-11 (Graph-Augmented Retrieval)
