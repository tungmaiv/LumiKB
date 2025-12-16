# Story 8-1: Neo4j Docker Infrastructure

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-1
**Priority:** HIGH (Foundation)
**Estimated Effort:** 2 story points
**Status:** BACKLOG

---

## Overview

Add Neo4j Community Edition to the Docker Compose development environment as the graph database foundation for GraphRAG. This establishes the infrastructure required for all subsequent Epic 8 stories.

---

## Acceptance Criteria

### AC1: Neo4j Service Configuration
**Given** a developer sets up the LumiKB development environment
**When** they run `docker compose up`
**Then** Neo4j Community Edition starts alongside existing services
**And** Neo4j is accessible on standard ports (7474 HTTP, 7687 Bolt)
**And** data persists across container restarts via named volume

### AC2: Python Driver Integration
**Given** the backend application starts
**When** it initializes database connections
**Then** a Neo4j Python driver connection is established
**And** the connection is verified with a health check
**And** connection pooling is configured for efficient reuse

### AC3: Health Check Endpoint
**Given** the application is running
**When** a health check request is made
**Then** Neo4j connectivity status is included in the response
**And** connection latency is reported

### AC4: Environment Configuration
**Given** Neo4j is configured in docker-compose
**When** environment variables are set
**Then** the following are configurable:
  - NEO4J_URI (default: bolt://neo4j:7687)
  - NEO4J_USER (default: neo4j)
  - NEO4J_PASSWORD (required, no default)
  - NEO4J_DATABASE (default: neo4j)
  - NEO4J_MAX_POOL_SIZE (default: 50)

---

## Technical Notes

### Docker Compose Addition

```yaml
neo4j:
  image: neo4j:5-community
  container_name: lumikb-neo4j
  ports:
    - "7474:7474"  # HTTP
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-lumikb_dev_password}
    - NEO4J_PLUGINS=["apoc"]
    - NEO4J_dbms_security_procedures_unrestricted=apoc.*
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

volumes:
  lumikb-neo4j-data:
  lumikb-neo4j-logs:
```

### Python Integration

```python
# backend/app/integrations/neo4j_client.py
from neo4j import GraphDatabase, AsyncGraphDatabase

class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def verify_connectivity(self) -> bool:
        """Health check for Neo4j connection."""
        with self._driver.session(database=self._database) as session:
            result = session.run("RETURN 1 AS connected")
            return result.single()["connected"] == 1

    def close(self):
        self._driver.close()
```

### Dependencies

Add to `pyproject.toml`:
```toml
neo4j = "^5.26.0"
```

---

## Definition of Done

- [ ] Neo4j service added to docker-compose.yml
- [ ] Named volumes configured for persistence
- [ ] Health check configured in Docker
- [ ] Python neo4j driver added to dependencies
- [ ] Neo4jClient class implemented with connection pooling
- [ ] Health check endpoint extended to include Neo4j
- [ ] Environment variables documented
- [ ] README updated with Neo4j setup instructions
- [ ] Integration test for Neo4j connectivity

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** None (Foundation story)
**Next Story:** Story 8-2 (Domain Data Model & Migrations)
