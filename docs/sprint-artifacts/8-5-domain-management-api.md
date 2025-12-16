# Story 8-5: Domain Management API

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-5
**Priority:** HIGH
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Implement CRUD API endpoints for managing domains, entity types, and relationship types. This provides the backend foundation for the Domain Management UI (Story 8-6).

---

## Acceptance Criteria

### AC1: Domain CRUD Endpoints
**Given** an authenticated user
**When** they make domain API requests
**Then** the following endpoints are available:
  - `POST /api/v1/domains` - Create domain
  - `GET /api/v1/domains` - List domains (user's + public)
  - `GET /api/v1/domains/{id}` - Get domain details
  - `PUT /api/v1/domains/{id}` - Update domain
  - `DELETE /api/v1/domains/{id}` - Delete domain
  - `POST /api/v1/domains/{id}/clone` - Clone domain

### AC2: Entity Type Management
**Given** a domain exists
**When** managing entity types
**Then** the following operations are supported:
  - `POST /api/v1/domains/{id}/entity-types` - Add entity type
  - `PUT /api/v1/domains/{id}/entity-types/{type_id}` - Update entity type
  - `DELETE /api/v1/domains/{id}/entity-types/{type_id}` - Remove entity type
  - `PATCH /api/v1/domains/{id}/entity-types/reorder` - Reorder entity types

### AC3: Relationship Type Management
**Given** a domain has entity types
**When** managing relationship types
**Then** the following operations are supported:
  - `POST /api/v1/domains/{id}/relationship-types` - Add relationship
  - `PUT /api/v1/domains/{id}/relationship-types/{rel_id}` - Update relationship
  - `DELETE /api/v1/domains/{id}/relationship-types/{rel_id}` - Remove relationship

### AC4: Access Control
**Given** domains have ownership
**When** a user attempts to modify a domain
**Then** only the domain owner or admin can modify
**And** system templates cannot be modified (return 403)
**And** public domains are readable by all authenticated users
**And** private domains are only visible to the owner

### AC5: Validation Rules
**Given** domain data is submitted
**When** validation runs
**Then** the following rules are enforced:
  - Domain name: unique, 3-100 characters
  - Entity type name: unique within domain, 2-50 characters
  - Entity type attributes: valid JSON schema format
  - Relationship types: must reference valid entity types within domain
  - Color: valid hex code (#RRGGBB)

### AC6: System Template Protection
**Given** a system template exists
**When** modification is attempted
**Then** updates return 403 Forbidden
**And** deletes return 403 Forbidden
**And** cloning is allowed and creates user-owned copy

---

## Technical Notes

### API Endpoint Details

```python
# backend/app/api/v1/domains.py

@router.post("/", response_model=DomainResponse)
async def create_domain(
    domain: DomainCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new domain schema."""
    service = DomainService(db)
    return await service.create(domain, current_user.id)

@router.get("/", response_model=DomainListResponse)
async def list_domains(
    include_public: bool = True,
    include_system: bool = True,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List domains accessible to user."""
    service = DomainService(db)
    return await service.list_accessible(
        user_id=current_user.id,
        include_public=include_public,
        include_system=include_system,
        skip=skip,
        limit=limit
    )

@router.post("/{domain_id}/clone", response_model=DomainResponse)
async def clone_domain(
    domain_id: UUID,
    clone_request: DomainCloneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clone a domain (including system templates)."""
    service = DomainService(db)
    return await service.clone(
        domain_id=domain_id,
        new_name=clone_request.name,
        user_id=current_user.id
    )
```

### Pydantic Schemas

```python
# backend/app/schemas/domain.py
class DomainCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    entity_types: Optional[List[EntityTypeCreate]] = None
    relationship_types: Optional[List[RelationshipTypeCreate]] = None

class EntityTypeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    attributes: List[AttributeDefinition] = []
    color: str = Field(default="#6B7280", regex=r"^#[0-9A-Fa-f]{6}$")
    icon: str = "circle"
    extraction_hints: Optional[str] = None
    sort_order: int = 0

class AttributeDefinition(BaseModel):
    name: str
    type: Literal["string", "number", "boolean", "date", "enum"]
    required: bool = False
    values: Optional[List[str]] = None  # For enum type

class RelationshipTypeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    from_entity_type_name: str
    to_entity_type_name: str
    attributes: List[AttributeDefinition] = []
    bidirectional: bool = False
```

### Service Layer

```python
# backend/app/services/domain_service.py
class DomainService:
    async def create(self, data: DomainCreate, user_id: UUID) -> Domain:
        # Validate unique name
        existing = await self._get_by_name(data.name)
        if existing:
            raise HTTPException(409, f"Domain '{data.name}' already exists")

        domain = Domain(
            name=data.name,
            description=data.description,
            is_public=data.is_public,
            created_by=user_id
        )
        self.db.add(domain)
        await self.db.flush()

        # Create entity types
        if data.entity_types:
            for et_data in data.entity_types:
                await self._create_entity_type(domain.id, et_data)

        # Create relationship types
        if data.relationship_types:
            for rt_data in data.relationship_types:
                await self._create_relationship_type(domain.id, rt_data)

        await self.db.commit()
        return domain
```

---

## Definition of Done

- [ ] Domain CRUD endpoints implemented
- [ ] Entity type CRUD endpoints implemented
- [ ] Relationship type CRUD endpoints implemented
- [ ] Clone functionality working
- [ ] Reorder functionality for entity types
- [ ] Access control enforced
- [ ] Validation rules implemented
- [ ] System template protection
- [ ] Audit logging for domain changes
- [ ] Unit tests for service layer
- [ ] Integration tests for API endpoints
- [ ] OpenAPI documentation updated

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-2 (Domain Data Model)
**Next Story:** Story 8-6 (Domain Management UI)
