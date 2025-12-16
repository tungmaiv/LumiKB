# Story 8-2: Domain Data Model & Migrations

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-2
**Priority:** HIGH (Foundation)
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Create the PostgreSQL schema for domain management, including domains, entity types, and relationship types. Domains define the knowledge graph schema that can be reused across multiple Knowledge Bases.

---

## Acceptance Criteria

### AC1: Domain Model
**Given** an administrator creates a new domain
**When** the domain is saved
**Then** the following fields are stored:
  - id (UUID, primary key)
  - name (unique, required)
  - description (optional)
  - is_system_template (boolean, default false)
  - is_public (boolean, default false)
  - created_by (references users)
  - created_at, updated_at (timestamps)

### AC2: Entity Type Model
**Given** a domain has entity types defined
**When** entity types are saved
**Then** each entity type includes:
  - id (UUID, primary key)
  - domain_id (references domains)
  - name (unique within domain)
  - description
  - attributes (JSONB array of attribute definitions)
  - color (hex color code for visualization)
  - icon (icon identifier)
  - extraction_hints (text prompts for LLM extraction)
  - sort_order (display ordering)

### AC3: Relationship Type Model
**Given** a domain has relationship types defined
**When** relationship types are saved
**Then** each relationship type includes:
  - id (UUID, primary key)
  - domain_id (references domains)
  - name (unique within domain)
  - from_entity_type_id (references entity types)
  - to_entity_type_id (references entity types)
  - attributes (JSONB array)
  - bidirectional (boolean)

### AC4: KB-Domain Junction Table
**Given** a Knowledge Base can use a domain schema
**When** a domain is linked to a KB
**Then** the kb_domains table stores:
  - kb_id (references knowledge_bases)
  - domain_id (references domains)
  - linked_at (timestamp)
  - linked_by (references users)

### AC5: Alembic Migration
**Given** the schema is defined
**When** `alembic upgrade head` is run
**Then** all tables are created with proper:
  - Foreign key constraints
  - Indexes on frequently queried columns
  - Cascade delete rules

---

## Technical Notes

### Database Schema

```sql
-- Domains table
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_system_template BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Domain Entity Types
CREATE TABLE domain_entity_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    attributes JSONB DEFAULT '[]'::jsonb,
    color VARCHAR(7) DEFAULT '#6B7280',
    icon VARCHAR(50) DEFAULT 'circle',
    extraction_hints TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- Domain Relationship Types
CREATE TABLE domain_relationship_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    from_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE CASCADE,
    to_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE CASCADE,
    attributes JSONB DEFAULT '[]'::jsonb,
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- KB-Domain linking
CREATE TABLE kb_domains (
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    linked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (kb_id, domain_id)
);

-- Indexes
CREATE INDEX idx_entity_types_domain ON domain_entity_types(domain_id);
CREATE INDEX idx_relationship_types_domain ON domain_relationship_types(domain_id);
CREATE INDEX idx_kb_domains_kb ON kb_domains(kb_id);
CREATE INDEX idx_kb_domains_domain ON kb_domains(domain_id);
```

### SQLAlchemy Models

```python
# backend/app/models/domain.py
class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system_template: Mapped[bool] = mapped_column(default=False)
    is_public: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity_types: Mapped[List["DomainEntityType"]] = relationship(back_populates="domain", cascade="all, delete-orphan")
    relationship_types: Mapped[List["DomainRelationshipType"]] = relationship(back_populates="domain", cascade="all, delete-orphan")
```

---

## Definition of Done

- [ ] Domain model created
- [ ] DomainEntityType model created
- [ ] DomainRelationshipType model created
- [ ] KB-Domain junction table created
- [ ] Alembic migration file generated
- [ ] Migration tested up and down
- [ ] Pydantic schemas for API serialization
- [ ] Unit tests for model relationships
- [ ] Index performance verified

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-1 (Neo4j Infrastructure)
**Next Story:** Story 8-3 (System Domain Templates)
