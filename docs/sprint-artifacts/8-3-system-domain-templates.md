# Story 8-3: System Domain Templates

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-3
**Priority:** MEDIUM
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Create pre-built domain templates for common enterprise use cases. These system templates are read-only, available to all users, and can be cloned for customization. They provide a quick-start for GraphRAG without requiring manual schema creation.

---

## Acceptance Criteria

### AC1: IT Operations Domain Template
**Given** a user wants to use GraphRAG for IT documentation
**When** they select the IT Operations template
**Then** the following entity types are available:
  - **Server**: hostname, ip_address, os, environment, status
  - **Service**: name, port, protocol, version
  - **Application**: name, version, owner, criticality
  - **Incident**: id, severity, status, resolution
  - **Runbook**: title, author, last_updated
**And** relationships include:
  - Server HOSTS Service
  - Service BELONGS_TO Application
  - Incident AFFECTS Service
  - Runbook RESOLVES Incident

### AC2: Legal/Compliance Domain Template
**Given** a user wants to use GraphRAG for legal documents
**When** they select the Legal template
**Then** the following entity types are available:
  - **Contract**: title, parties, effective_date, expiry_date, value
  - **Clause**: type, section_number, text_summary
  - **Party**: name, type (individual/organization), jurisdiction
  - **Regulation**: name, authority, effective_date
  - **Obligation**: description, due_date, status
**And** relationships include:
  - Contract CONTAINS Clause
  - Contract INVOLVES Party
  - Clause REFERENCES Regulation
  - Contract CREATES Obligation

### AC3: Sales & Marketing Domain Template
**Given** a user wants to use GraphRAG for sales content
**When** they select the Sales template
**Then** the following entity types are available:
  - **Product**: name, sku, category, price_tier
  - **Feature**: name, description, availability
  - **Competitor**: name, market_position
  - **UseCase**: industry, pain_point, solution
  - **Testimonial**: customer, quote, date
**And** relationships include:
  - Product HAS Feature
  - Product COMPETES_WITH Competitor
  - Product SOLVES UseCase
  - Testimonial ENDORSES Product

### AC4: Project Management Domain Template
**Given** a user wants to use GraphRAG for PM documentation
**When** they select the Project Management template
**Then** the following entity types are available:
  - **Project**: name, status, start_date, end_date, budget
  - **Milestone**: name, due_date, status
  - **Task**: name, assignee, priority, status
  - **Risk**: description, probability, impact, mitigation
  - **Decision**: title, date, outcome, rationale
**And** relationships include:
  - Project CONTAINS Milestone
  - Milestone INCLUDES Task
  - Project HAS Risk
  - Decision IMPACTS Project

### AC5: HR/People Domain Template
**Given** a user wants to use GraphRAG for HR documents
**When** they select the HR template
**Then** the following entity types are available:
  - **Role**: title, department, level, salary_band
  - **Skill**: name, category, proficiency_levels
  - **Policy**: name, category, effective_date
  - **Benefit**: name, type, eligibility
  - **Process**: name, steps, owner
**And** relationships include:
  - Role REQUIRES Skill
  - Role FOLLOWS Policy
  - Role ELIGIBLE_FOR Benefit
  - Policy DEFINES Process

### AC6: Template Seeding
**Given** the application starts for the first time
**When** database migrations complete
**Then** all 5 system domain templates are seeded
**And** templates are marked as is_system_template=true
**And** templates are marked as is_public=true
**And** templates cannot be deleted by regular admins

---

## Technical Notes

### Seed Data Structure

```python
# backend/app/seeds/domain_templates.py
SYSTEM_DOMAIN_TEMPLATES = [
    {
        "name": "IT Operations",
        "description": "Infrastructure, services, incidents, and runbooks for IT teams",
        "entity_types": [
            {
                "name": "Server",
                "color": "#3B82F6",
                "icon": "server",
                "attributes": [
                    {"name": "hostname", "type": "string", "required": True},
                    {"name": "ip_address", "type": "string"},
                    {"name": "os", "type": "string"},
                    {"name": "environment", "type": "enum", "values": ["production", "staging", "development"]},
                    {"name": "status", "type": "enum", "values": ["active", "maintenance", "decommissioned"]}
                ],
                "extraction_hints": "Look for server names, IP addresses, hostnames, machine identifiers"
            },
            # ... more entity types
        ],
        "relationship_types": [
            {
                "name": "HOSTS",
                "from_entity": "Server",
                "to_entity": "Service",
                "bidirectional": False
            },
            # ... more relationships
        ]
    },
    # ... other templates
]
```

### Template Cloning

```python
async def clone_domain(domain_id: UUID, new_name: str, user_id: UUID) -> Domain:
    """Clone a system template for user customization."""
    original = await get_domain(domain_id)

    new_domain = Domain(
        name=new_name,
        description=f"Customized from: {original.name}",
        is_system_template=False,
        is_public=False,
        created_by=user_id
    )

    # Clone entity types and relationships
    # ...
```

---

## Definition of Done

- [ ] IT Operations template defined and seeded
- [ ] Legal/Compliance template defined and seeded
- [ ] Sales & Marketing template defined and seeded
- [ ] Project Management template defined and seeded
- [ ] HR/People template defined and seeded
- [ ] Seeding script runs on first migration
- [ ] Templates marked as system and public
- [ ] Clone functionality implemented
- [ ] Unit tests for seeding
- [ ] Template documentation in README

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-2 (Domain Data Model)
**Next Story:** Story 8-4 (LLM Domain Recommendation Service)
