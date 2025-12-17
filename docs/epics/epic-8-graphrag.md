# Epic 8: GraphRAG Integration

**Goal:** Enhance chat response quality through domain-driven knowledge graphs with per-KB schemas for context-aware entity relationships.

**User Value:** Users receive more accurate, contextually-aware answers that understand entity relationships across documents. Each Knowledge Base can define its own domain-specific entity types and relationships, enabling tailored knowledge graphs for IT Operations, Legal, Sales, Project Management, and other domains.

**FRs Covered:** FR78-FR92 (new FRs for GraphRAG capabilities)

**Technical Foundation:**
- Neo4j Community Edition for graph storage
- LLM-based entity extraction via LiteLLM (NER model type)
- Per-KB domain schemas with reusable domain definitions
- Vector-first + Graph-augment retrieval strategy
- Designed for future Parallel Merge upgrade path

**Key Architectural Decisions:**
- **Graph Database:** Neo4j Community Edition - proven, great Python driver, Docker-ready
- **Entity Extraction:** LLM-based via existing LiteLLM proxy with new NER model type
- **Retrieval Strategy:** Vector-first + Graph-augment (Phase 1), designed for Parallel Merge (Phase 2)
- **Schema Model:** Per-KB domain schemas with reusable domain definitions across KBs

---

## Story 8.0: History-Aware Query Rewriting

**Description:** As a user, I want my follow-up questions to understand conversation context so that pronouns and references ("he", "it", "that") are resolved correctly before search.

**Story Points:** 5

**User Value:** Users can have natural multi-turn conversations where follow-up questions like "How old is he?" correctly resolve to "What is Tim Cook's age?" based on conversation history. This dramatically improves chat quality without requiring GraphRAG infrastructure.

**Acceptance Criteria:**

**AC-8.0.1: Query rewriting service created**
**Given** a user query and conversation history
**When** QueryRewriterService.rewrite_with_history() is called
**Then** the query is reformulated to be standalone (all pronouns and references resolved)
**And** if no history exists, original query is returned unchanged

**AC-8.0.2: Cheap LLM model configuration in admin UI**
**Given** I navigate to Admin > System Configuration
**Then** I see a "Query Rewriting Model" dropdown in the LLM Settings section
**And** dropdown shows available models from model registry (filtered by type: chat/completion)
**And** recommended models are highlighted (e.g., gpt-3.5-turbo, ollama/llama3.2, claude-3-haiku)

**AC-8.0.3: System config stores rewriter model**
**Given** I select a model in "Query Rewriting Model" dropdown
**When** I save configuration
**Then** the setting is persisted to system_config table
**And** backend uses this model for query rewriting

**AC-8.0.4: Integration with conversation flow**
**Given** conversation_service.send_message() is called
**When** chat_history contains previous messages
**Then** query is rewritten BEFORE search is executed
**And** search uses the rewritten query
**And** original query is preserved for display to user

**AC-8.0.5: Rewriter prompt engineering**
**Given** a query with conversation history
**Then** rewriter prompt instructs LLM to:
- Reformulate to standalone question
- Resolve pronouns (he/she/it/they) to specific entities
- Expand implicit references ("the same thing" → actual topic)
- NOT answer the question, only reformulate it
- Return original if already standalone

**AC-8.0.6: Debug mode shows rewritten query**
**Given** KB has debug_mode=true
**When** query rewriting occurs
**Then** DebugInfo SSE event includes:
- original_query: "How old is he?"
- rewritten_query: "What is Tim Cook's age?"
- rewriter_model: "ollama/llama3.2"
- rewrite_latency_ms: 150

**AC-8.0.7: Performance constraints**
**Given** query rewriting is enabled
**Then** rewriting completes in < 500ms (p95)
**And** cheap model is used to minimize cost
**And** timeout is configurable (default: 5 seconds)

**AC-8.0.8: Graceful degradation**
**Given** query rewriting fails (timeout, model unavailable)
**Then** original query is used for search
**And** warning is logged
**And** user experience is not degraded

**AC-8.0.9: Skip rewriting when not needed**
**Given** conversation has no history (first message)
**Or** query is already standalone (no pronouns/references detected)
**Then** rewriting step is skipped
**And** latency is not added

**AC-8.0.10: Observability integration**
**Given** query rewriting executes
**Then** Langfuse trace includes "query_rewrite" span with:
- input_query, output_query, model_used, latency_ms
**And** metrics emitted: lumikb_query_rewrite_duration_seconds, lumikb_query_rewrite_skipped_total

**Prerequisites:** Story 7.9 (LLM Model Registry), Story 9.15 (Debug Mode)

**Technical Notes:**
- Create backend/app/services/query_rewriter_service.py
- Update backend/app/services/conversation_service.py (insert rewrite step before search)
- Add query_rewriting_model_id column to system_config or use settings JSONB
- Frontend: Add dropdown to frontend/src/app/(protected)/admin/config/page.tsx
- Use existing LiteLLMEmbeddingClient.chat_completion() for rewriting
- Consider caching rewritten queries (same history + query = same rewrite)

---

## Story 8.1: Neo4j Docker Infrastructure

**Description:** As a developer, I want Neo4j added to the Docker infrastructure so GraphRAG can store and query knowledge graphs.

**Story Points:** 2

**Acceptance Criteria:**

**AC-8.1.1: Neo4j in docker-compose**
**Given** I run docker-compose up
**Then** Neo4j Community Edition starts alongside other services
**And** exposes Bolt port (7687) and HTTP port (7474)

**AC-8.1.2: Health check endpoint**
**Given** Neo4j is running
**Then** /health endpoint returns healthy status
**And** orchestrator can verify graph database availability

**AC-8.1.3: Connection pooling**
**Given** backend connects to Neo4j
**Then** connection pool is configured (min: 5, max: 50)
**And** connections are reused efficiently

**AC-8.1.4: Persistent storage**
**Given** docker-compose is restarted
**Then** Neo4j data persists via mounted volume
**And** no graph data is lost

**AC-8.1.5: Environment configuration**
**Given** deployment environment
**Then** Neo4j credentials are configurable via environment variables
**And** no hardcoded credentials exist

**Prerequisites:** None

**Technical Notes:**
- Add neo4j service to infrastructure/docker/docker-compose.yml
- Create backend/app/integrations/neo4j_client.py
- Add NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD to config

---

## Story 8.2: Domain Data Model & Migrations

**Description:** As a developer, I want database tables for domain definitions so entity types and relationships can be stored and managed.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.2.1: Domains table created**
**Given** I run alembic upgrade
**Then** `domains` table exists with columns: id, name, description, is_system_template, is_public, created_by, created_at, updated_at

**AC-8.2.2: Entity types table created**
**Given** I run alembic upgrade
**Then** `domain_entity_types` table exists with columns: id, domain_id, name, description, attributes (JSONB), color, icon, extraction_hints, sort_order

**AC-8.2.3: Relationship types table created**
**Given** I run alembic upgrade
**Then** `domain_relationship_types` table exists with columns: id, domain_id, name, description, from_entity_type_id, to_entity_type_id, attributes (JSONB), bidirectional, extraction_hints

**AC-8.2.4: Domain versions table created**
**Given** I run alembic upgrade
**Then** `domain_versions` table exists for schema version history

**AC-8.2.5: KB-Domain link**
**Given** I run alembic upgrade
**Then** `knowledge_bases` table has `domain_id` foreign key column

**AC-8.2.6: Document graph status**
**Given** I run alembic upgrade
**Then** `documents` table has `graph_extraction_status`, `graph_extracted_at`, `graph_schema_version` columns

**Prerequisites:** None

**Technical Notes:**
- Alembic migration for all new tables
- SQLAlchemy models in backend/app/models/domain.py
- Pydantic schemas in backend/app/schemas/domain.py

---

## Story 8.3: System Domain Templates

**Description:** As an admin, I want pre-built domain templates so users can quickly start with common domain schemas.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.3.1: IT Operations template**
**Given** I view domain templates
**Then** I see "IT Operations" with entities: Server, Application, Incident, Team, Service, Database, SLA
**And** relationships: hosts, depends_on, assigned_to, connects_to, affects, has_sla

**AC-8.3.2: Legal/Contracts template**
**Given** I view domain templates
**Then** I see "Legal" with entities: Contract, Party, Clause, Obligation, Jurisdiction, Date
**And** relationships: binds, references, amends, governs, signed_by, expires_on

**AC-8.3.3: Sales & Marketing template**
**Given** I view domain templates
**Then** I see "Sales & Marketing" with entities: Campaign, Lead, Account, Product, Competitor, Channel
**And** relationships: targets, converts, competes_with, influences, runs_on

**AC-8.3.4: Project Management template**
**Given** I view domain templates
**Then** I see "Project Management" with entities: Project, Task, Milestone, Resource, Risk, Deliverable
**And** relationships: contains, blocks, assigned_to, mitigates, delivers, depends_on

**AC-8.3.5: HR/People template**
**Given** I view domain templates
**Then** I see "HR/People" with entities: Employee, Department, Role, Skill, Policy, Training
**And** relationships: reports_to, has_skill, member_of, governs, completed

**AC-8.3.6: Templates marked as system**
**Given** templates are loaded
**Then** all templates have is_system_template=true
**And** cannot be deleted by users

**Prerequisites:** Story 8.2 (Domain Data Model)

**Technical Notes:**
- Seed data in backend/app/seeds/domain_templates.py
- Load via alembic data migration or startup script
- Each template includes extraction_hints for LLM guidance

---

## Story 8.4: LLM Domain Recommendation Service

**Description:** As a user, I want LLM-powered domain schema recommendations so I can quickly define appropriate entities and relationships for my KB.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.4.1: Recommendation from description**
**Given** I provide a domain name and description
**When** I request LLM recommendations
**Then** I receive suggested entity types with descriptions
**And** suggested relationship types with from/to entity mappings

**AC-8.4.2: Uses NER model from registry**
**Given** NER model is configured in model registry
**When** recommendation is requested
**Then** the configured NER model is used via LiteLLM

**AC-8.4.3: Structured output**
**Given** LLM generates recommendations
**Then** output is parsed into valid EntityType and RelationshipType schemas
**And** includes extraction_hints for each type

**AC-8.4.4: Template matching**
**Given** description matches a known domain (e.g., "IT infrastructure")
**When** recommendations are generated
**Then** system suggests starting from matching template
**And** provides additional custom recommendations

**AC-8.4.5: Confidence scores**
**Given** recommendations are generated
**Then** each entity/relationship includes confidence score (0-1)
**And** user can filter by minimum confidence

**Prerequisites:** Story 7.9 (LLM Model Registry with NER type)

**Technical Notes:**
- backend/app/services/domain_recommendation_service.py
- Prompt engineering for structured entity/relationship extraction
- JSON mode output for reliable parsing

---

## Story 8.5: Domain Management API

**Description:** As a developer, I want CRUD API endpoints for domains so the frontend can manage domain definitions.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.5.1: List domains**
**Given** I call GET /api/v1/domains
**Then** I receive list of domains with entity/relationship counts
**And** can filter by is_system_template, is_public

**AC-8.5.2: Get domain details**
**Given** I call GET /api/v1/domains/{id}
**Then** I receive full domain with all entity types and relationship types

**AC-8.5.3: Create domain**
**Given** I call POST /api/v1/domains with name, description, entity_types, relationship_types
**Then** domain is created and returned with ID

**AC-8.5.4: Update domain**
**Given** I call PUT /api/v1/domains/{id}
**Then** domain is updated
**And** version history entry is created

**AC-8.5.5: Delete domain**
**Given** I call DELETE /api/v1/domains/{id}
**When** no KBs are using this domain
**Then** domain is deleted

**AC-8.5.6: Clone domain**
**Given** I call POST /api/v1/domains/{id}/clone
**Then** new domain is created with copied schema
**And** is_system_template is set to false

**AC-8.5.7: Get recommendations**
**Given** I call POST /api/v1/domains/recommend with name, description
**Then** I receive LLM-generated entity and relationship suggestions

**AC-8.5.8: Entity type CRUD**
**Given** I call POST/PUT/DELETE /api/v1/domains/{id}/entity-types
**Then** entity types are managed within domain

**AC-8.5.9: Relationship type CRUD**
**Given** I call POST/PUT/DELETE /api/v1/domains/{id}/relationship-types
**Then** relationship types are managed within domain

**Prerequisites:** Story 8.2, 8.4

**Technical Notes:**
- backend/app/api/v1/domains.py
- backend/app/services/domain_service.py
- Permission: Admin can manage all, users can manage own domains

---

## Story 8.6: Domain Management UI

**Description:** As an admin, I want a UI for creating and editing domains so I can define entity types and relationships visually.

**Story Points:** 8

**Acceptance Criteria:**

**AC-8.6.1: Domain list page**
**Given** I navigate to Admin > Domains
**Then** I see list of all domains with name, entity count, relationship count, KB usage count

**AC-8.6.2: Create domain form**
**Given** I click "Create Domain"
**Then** I see form with name, description fields
**And** "Get LLM Recommendations" button

**AC-8.6.3: LLM recommendation integration**
**Given** I click "Get LLM Recommendations"
**Then** loading indicator shows
**And** suggested entities and relationships populate the form

**AC-8.6.4: Entity type editor**
**Given** I am editing a domain
**Then** I can add/edit/delete entity types
**And** configure: name, description, color, icon, attributes, extraction_hints

**AC-8.6.5: Relationship type editor**
**Given** I am editing a domain
**Then** I can add/edit/delete relationship types
**And** configure: name, from_type, to_type, description, bidirectional, extraction_hints

**AC-8.6.6: Visual relationship diagram**
**Given** I am viewing a domain
**Then** I see visual diagram showing entities as nodes and relationships as edges

**AC-8.6.7: Template selection**
**Given** I am creating a domain
**Then** I can start from a system template
**And** template schema is copied to new domain

**AC-8.6.8: Validation**
**Given** I save a domain
**Then** validation ensures: unique entity names, valid relationship references, no orphan types

**AC-8.6.9: Delete protection**
**Given** a domain is used by KBs
**When** I try to delete it
**Then** I see warning with list of dependent KBs
**And** deletion is blocked

**Prerequisites:** Story 8.5

**Technical Notes:**
- frontend/src/app/(protected)/admin/domains/page.tsx
- frontend/src/components/admin/domain-editor.tsx
- Use react-flow or similar for visual diagram

---

## Story 8.7: KB-Domain Linking

**Description:** As a KB creator, I want to associate my Knowledge Base with a domain so documents are extracted using the appropriate schema.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.7.1: Domain selection in KB creation**
**Given** I am creating a new Knowledge Base
**Then** I see domain selection dropdown with options:
- System templates
- My domains
- Public domains
- "Create New Domain..."
- "No Domain (skip GraphRAG)"

**AC-8.7.2: Domain preview**
**Given** I select a domain
**Then** I see preview of entity types and relationship types

**AC-8.7.3: Create domain inline**
**Given** I select "Create New Domain..."
**Then** domain creation modal opens
**And** new domain is linked after creation

**AC-8.7.4: KB settings shows domain**
**Given** I view KB settings
**Then** I see linked domain with link to domain details

**AC-8.7.5: Change domain warning**
**Given** KB has documents with graph extractions
**When** I try to change domain
**Then** I see warning: "Changing domain requires re-extraction of all documents"
**And** I must confirm to proceed

**AC-8.7.6: No domain option**
**Given** I select "No Domain"
**Then** KB is created without GraphRAG capabilities
**And** documents are processed with vector-only (existing behavior)

**Prerequisites:** Story 8.6

**Technical Notes:**
- Update frontend/src/components/kb/kb-create-modal.tsx
- Add domain_id to KB creation/update API calls

---

## Story 8.8: Per-KB Entity Extraction Service

**Description:** As a system, I want to extract entities from documents using the KB's domain schema so knowledge graphs are domain-specific.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.8.1: Load KB domain schema**
**Given** a document is being processed
**When** entity extraction starts
**Then** KB's linked domain schema is loaded

**AC-8.8.2: Schema-aware extraction prompt**
**Given** domain schema is loaded
**Then** LLM prompt includes:
- List of valid entity types with descriptions
- List of valid relationship types with from/to constraints
- Extraction hints from schema

**AC-8.8.3: Extract entities from chunks**
**Given** document chunks are available
**When** extraction runs
**Then** entities are extracted with: type, name, attributes, source_chunk_id

**AC-8.8.4: Extract relationships**
**Given** entities are extracted
**When** relationship extraction runs
**Then** relationships are extracted with: type, from_entity, to_entity, attributes

**AC-8.8.5: Handle unknown entities**
**Given** LLM finds entity not matching schema
**Then** entity is tagged as "unmatched" for later review
**And** suggested type is recorded

**AC-8.8.6: Batch processing**
**Given** large document with many chunks
**Then** extraction is batched (configurable batch_size)
**And** progress is tracked

**AC-8.8.7: Extraction metrics**
**Given** extraction completes
**Then** metrics are recorded: entities_found, relationships_found, unmatched_count, processing_time

**Prerequisites:** Story 8.4, 8.7

**Technical Notes:**
- backend/app/services/entity_extraction_service.py
- Prompt template in backend/app/prompts/entity_extraction.py
- Uses NER model from model registry

---

## Story 8.9: Document Processing Graph Integration

**Description:** As a system, I want entity extraction integrated into the document processing pipeline so graphs are built during ingestion.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.9.1: Graph extraction step added**
**Given** document processing pipeline
**Then** new step "graph_extraction" follows embedding step

**AC-8.9.2: Skip if no domain**
**Given** KB has no linked domain
**When** document is processed
**Then** graph extraction step is skipped
**And** status shows "skipped - no domain"

**AC-8.9.3: Store entities in Neo4j**
**Given** entities are extracted
**Then** nodes are created in Neo4j with:
- Label: `Entity_{kb_id}`
- Properties: type, name, attributes, document_id, chunk_id

**AC-8.9.4: Store relationships in Neo4j**
**Given** relationships are extracted
**Then** edges are created in Neo4j with:
- Type: relationship_name
- Properties: attributes, document_id, confidence

**AC-8.9.5: Update document status**
**Given** graph extraction completes
**Then** document.graph_extraction_status = "completed"
**And** document.graph_extracted_at = now()
**And** document.graph_schema_version = domain.version

**AC-8.9.6: Handle extraction failure**
**Given** graph extraction fails
**Then** document.graph_extraction_status = "failed"
**And** error is logged
**And** document processing continues (vector search still works)

**AC-8.9.7: Processing status includes graph**
**Given** I view document processing status
**Then** I see graph extraction step with status

**Prerequisites:** Story 8.1, 8.8

**Technical Notes:**
- Update backend/app/workers/document_tasks.py
- Add graph extraction to Celery task chain
- Graceful degradation on graph failure

---

## Story 8.10: Graph Query Service

**Description:** As a developer, I want a service for querying the knowledge graph so retrieval can traverse entity relationships.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.10.1: Find entities by name**
**Given** I query for entity by name/partial match
**Then** matching entities are returned with type and attributes

**AC-8.10.2: Traverse relationships**
**Given** I have an entity
**When** I request traversal with max_hops
**Then** related entities are returned up to max_hops distance

**AC-8.10.3: Filter by relationship type**
**Given** I traverse from an entity
**Then** I can filter by specific relationship types

**AC-8.10.4: Get entity's chunks**
**Given** I have an entity
**Then** I can retrieve source chunk IDs for that entity

**AC-8.10.5: KB-scoped queries**
**Given** I query the graph
**Then** results are scoped to the specified KB's entities

**AC-8.10.6: Query performance**
**Given** graph with 100k entities
**Then** traversal queries return in < 100ms

**Prerequisites:** Story 8.9

**Technical Notes:**
- backend/app/services/graph_query_service.py
- Cypher queries for Neo4j
- Index entities by name and type for fast lookup

---

## Story 8.11: Graph-Augmented Retrieval

**Description:** As a user, I want my search results enhanced with graph context so related entities are included in the response.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.11.1: Vector search first**
**Given** user submits a query
**Then** standard vector search returns top-K chunks

**AC-8.11.2: Extract entities from results**
**Given** vector results are available
**Then** entities mentioned in top chunks are identified

**AC-8.11.3: Graph traversal**
**Given** entities are identified
**Then** graph is traversed (1-2 hops) to find related entities

**AC-8.11.4: Fetch related chunks**
**Given** related entities are found
**Then** chunks containing those entities are retrieved

**AC-8.11.5: Merge and dedupe**
**Given** vector chunks and graph chunks are available
**Then** results are merged with duplicates removed

**AC-8.11.6: Rerank combined results**
**Given** merged results
**Then** results are reranked by relevance to original query
**And** final top-K returned to LLM

**AC-8.11.7: Graceful degradation**
**Given** graph query fails
**Then** vector results are returned without graph augmentation
**And** warning is logged

**AC-8.11.8: Performance target**
**Given** query with graph augmentation
**Then** total retrieval time < 200ms additional latency

**Prerequisites:** Story 8.10

**Technical Notes:**
- Update backend/app/services/search_service.py
- Add graph_augmentation optional parameter
- Enabled by default for KBs with domains

---

## Story 8.12: Retrieval Strategy Abstraction

**Description:** As a developer, I want a retrieval strategy abstraction so future retrieval methods (Parallel Merge) can be added easily.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.12.1: Strategy interface**
**Given** I implement a new retrieval strategy
**Then** I extend RetrievalStrategy base class with retrieve() method

**AC-8.12.2: Vector-only strategy**
**Given** KB has no domain
**Then** VectorOnlyStrategy is used

**AC-8.12.3: Graph-augment strategy**
**Given** KB has domain
**Then** GraphAugmentStrategy is used by default

**AC-8.12.4: Strategy selection**
**Given** retrieval is requested
**Then** appropriate strategy is selected based on KB configuration

**AC-8.12.5: Feature flag ready**
**Given** new strategy is implemented
**Then** feature flag can switch between strategies

**AC-8.12.6: Strategy metrics**
**Given** retrieval completes
**Then** metrics include strategy used and timing breakdown

**Prerequisites:** Story 8.11

**Technical Notes:**
- backend/app/services/retrieval/base.py - RetrievalStrategy ABC
- backend/app/services/retrieval/vector_only.py
- backend/app/services/retrieval/graph_augment.py
- Factory pattern for strategy selection

---

## Story 8.13: LLM Schema Enrichment Suggestions

**Description:** As an admin, I want LLM-suggested schema enrichments so domains can evolve based on document content.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.13.1: Track unmatched entities**
**Given** entity extraction finds entities not matching schema
**Then** unmatched entities are stored with suggested type and frequency

**AC-8.13.2: Aggregate suggestions**
**Given** multiple documents have unmatched entities
**Then** suggestions are aggregated by suggested type with total counts

**AC-8.13.3: Suggestion notification**
**Given** unmatched entity count exceeds threshold (e.g., 10)
**Then** admin notification is triggered
**And** badge appears on domain in UI

**AC-8.13.4: Review suggestions UI**
**Given** I view domain with suggestions
**Then** I see list of suggested new entity types with:
- Suggested name
- Example values found
- Document count
- Accept/Reject buttons

**AC-8.13.5: Accept suggestion**
**Given** I accept a suggested entity type
**Then** new entity type is added to domain
**And** unmatched entities are reclassified

**AC-8.13.6: Relationship suggestions**
**Given** new entity types are accepted
**Then** LLM suggests potential relationships to existing types

**AC-8.13.7: Suggestion threshold config**
**Given** I configure domain
**Then** I can set minimum frequency for suggestions

**Prerequisites:** Story 8.8, 8.6

**Technical Notes:**
- Store unmatched entities in separate table
- Batch LLM analysis for relationship suggestions
- frontend/src/components/admin/schema-suggestions.tsx

---

## Story 8.14: Schema Evolution & Re-extraction

**Description:** As an admin, I want to trigger re-extraction when domain schema changes so existing documents reflect the updated schema.

**Story Points:** 5

**Acceptance Criteria:**

**AC-8.14.1: Schema version tracking**
**Given** domain is updated
**Then** version is incremented
**And** snapshot is saved to domain_versions table

**AC-8.14.2: Detect outdated documents**
**Given** domain version changes
**Then** documents with older graph_schema_version are identified

**AC-8.14.3: Re-extraction prompt**
**Given** domain is updated
**Then** admin sees prompt: "X documents need re-extraction. Trigger now?"

**AC-8.14.4: Selective re-extraction**
**Given** I trigger re-extraction
**Then** I can choose: all documents, specific documents, or schedule for later

**AC-8.14.5: Queue re-extraction jobs**
**Given** re-extraction is triggered
**Then** jobs are queued with lower priority than new uploads

**AC-8.14.6: Progress tracking**
**Given** re-extraction is running
**Then** I see progress: X of Y documents completed

**AC-8.14.7: Rollback capability**
**Given** re-extraction causes issues
**Then** I can rollback to previous schema version
**And** trigger re-extraction with old schema

**Prerequisites:** Story 8.9, 8.6

**Technical Notes:**
- Re-extraction clears existing graph nodes for document before re-processing
- Use Celery task with rate limiting
- Track re-extraction jobs in documents table

---

## Story 8.15: Batch Re-processing Worker

**Description:** As an admin, I want a batch worker for re-processing existing documents so GraphRAG can be enabled for legacy KBs.

**Story Points:** 3

**Acceptance Criteria:**

**AC-8.15.1: Trigger batch processing**
**Given** I enable GraphRAG on existing KB (add domain)
**Then** I can trigger batch re-processing for all documents

**AC-8.15.2: Queue management**
**Given** batch processing starts
**Then** documents are queued in chunks (e.g., 50 at a time)
**And** rate limiting prevents system overload

**AC-8.15.3: Progress API**
**Given** batch processing is running
**Then** API returns: total, completed, failed, remaining

**AC-8.15.4: Error handling**
**Given** individual document fails
**Then** error is logged
**And** processing continues with next document
**And** failed documents can be retried

**AC-8.15.5: Cancel batch**
**Given** batch processing is running
**Then** I can cancel remaining jobs
**And** completed work is preserved

**AC-8.15.6: Batch completion notification**
**Given** batch processing completes
**Then** admin is notified with summary: completed, failed, time elapsed

**Prerequisites:** Story 8.9

**Technical Notes:**
- backend/app/workers/graph_batch_tasks.py
- Celery chord for parallel processing with callback
- Admin UI shows batch status on KB settings page

---

## Story 8.16: E2E Test Automation

**Description:** As a developer, I want E2E test automation on top of Docker infrastructure so tests can run in CI/CD and validate all epics.

**Story Points:** 5

**Split From:** Story 7.1 (Docker E2E Testing Infrastructure)

**Acceptance Criteria:**
(See specification at docs/sprint-artifacts/8-16-e2e-test-automation.md)

**Prerequisites:** Story 7.1 (Docker E2E Infrastructure), Stories 8.1-8.15 (GraphRAG features to test)

**Technical Notes:**
- Playwright Docker configuration (playwright.config.e2e.ts)
- Dockerfile.playwright for test runner container
- GitHub Actions E2E workflow (.github/workflows/e2e-tests.yml)
- 70+ E2E tests covering Epic 3-8 features
- Test artifacts uploaded on CI runs

---

## Story 8.17: Hybrid BM25 + Vector Retrieval

**Description:** As a user, I want search to combine lexical (BM25) and semantic (vector) retrieval so that exact keyword matches and semantic similarity both contribute to finding relevant content.

**Story Points:** 8

**User Value:** Users get better search results for queries that contain specific terms (product names, error codes, technical terminology) that may not have good semantic embeddings, while still benefiting from semantic understanding for conceptual queries.

**Acceptance Criteria:**

**AC-8.17.1: Elasticsearch/OpenSearch added to Docker infrastructure**
**Given** I run docker-compose up
**Then** Elasticsearch (or OpenSearch) starts alongside other services
**And** exposes HTTP port (9200)
**And** data persists via mounted volume

**AC-8.17.2: BM25 index per Knowledge Base**
**Given** a Knowledge Base exists
**Then** a corresponding Elasticsearch index exists: `lumikb_kb_{kb_id}`
**And** index is configured with appropriate analyzers (standard, english)

**AC-8.17.3: Document chunks indexed in BM25**
**Given** document processing completes
**Then** chunks are indexed in both Qdrant (vector) AND Elasticsearch (BM25)
**And** BM25 index contains: chunk_id, text, document_id, kb_id, metadata

**AC-8.17.4: Hybrid retrieval strategy registered**
**Given** RetrievalStrategyRegistry is initialized
**Then** "hybrid_bm25_vector" strategy is registered
**And** can be selected via KB configuration or API parameter

**AC-8.17.5: Parallel search execution**
**Given** hybrid retrieval is triggered
**Then** BM25 search and vector search execute in parallel (async)
**And** combined latency is approximately max(bm25_time, vector_time), not sum

**AC-8.17.6: Result fusion with configurable weights**
**Given** BM25 results and vector results are available
**Then** results are merged using Reciprocal Rank Fusion (RRF) or weighted scoring
**And** weights are configurable: bm25_weight (default: 0.3), vector_weight (default: 0.7)
**And** duplicates are deduplicated by chunk_id

**AC-8.17.7: KB-level hybrid configuration**
**Given** I configure a Knowledge Base
**Then** I can enable/disable hybrid retrieval for that KB
**And** I can adjust BM25/vector weights per KB
**And** defaults to vector-only if Elasticsearch is unavailable

**AC-8.17.8: Admin UI configuration**
**Given** I navigate to Admin > System Configuration
**Then** I see "Hybrid Retrieval" section with:
- Enable/disable toggle
- BM25 weight slider (0.0 - 1.0)
- Vector weight slider (0.0 - 1.0)
**And** KB settings can override system defaults

**AC-8.17.9: Graceful degradation**
**Given** Elasticsearch is unavailable
**Then** system falls back to vector-only retrieval
**And** warning is logged
**And** user experience is not degraded

**AC-8.17.10: Chunk synchronization**
**Given** a document is deleted or updated
**Then** corresponding BM25 entries are deleted/updated
**And** BM25 and Qdrant remain in sync

**AC-8.17.11: Performance targets**
**Given** hybrid retrieval executes
**Then** total retrieval time < 150ms additional latency over vector-only
**And** BM25 queries return in < 50ms (p95)

**AC-8.17.12: Observability integration**
**Given** hybrid retrieval executes
**Then** metrics emitted:
- lumikb_bm25_query_duration_seconds
- lumikb_hybrid_retrieval_duration_seconds
- lumikb_retrieval_strategy_used (label: strategy_name)
**And** Langfuse trace includes "bm25_search" and "vector_search" spans

**Prerequisites:** Story 8.12 (Retrieval Strategy Abstraction)

**Technical Notes:**
- Add elasticsearch service to infrastructure/docker/docker-compose.yml
- Create backend/app/integrations/elasticsearch_client.py
- Create backend/app/services/retrieval/hybrid_bm25_vector.py
- Update document processing pipeline to dual-index chunks
- Consider using OpenSearch as open-source alternative to Elasticsearch
- RRF formula: score = Σ 1/(k + rank_i) where k=60 typically
- Alternative: Linear combination with normalized scores

**Infrastructure Addition:**
```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  container_name: lumikb-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - ES_JAVA_OPTS=-Xms512m -Xmx512m
  ports:
    - "9200:9200"
  volumes:
    - lumikb-elasticsearch-data:/usr/share/elasticsearch/data
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
    interval: 10s
    timeout: 5s
    retries: 5
```

---

## Summary

Epic 8 establishes the GraphRAG integration for enhanced semantic retrieval in LumiKB:

| Story | Points | Key Deliverable | Priority |
|-------|--------|-----------------|----------|
| **8.0** | **5** | **History-aware query rewriting (chat memory)** | **P0 - Immediate** |
| 8.1 | 2 | Neo4j Docker infrastructure | P1 - Foundation |
| 8.2 | 3 | Domain data model & migrations | P1 - Foundation |
| 8.3 | 3 | System domain templates | P1 - Foundation |
| 8.4 | 5 | LLM domain recommendation service | P1 - Foundation |
| 8.5 | 5 | Domain management API | P1 - Foundation |
| 8.6 | 8 | Domain management UI | P1 - Foundation |
| 8.7 | 3 | KB-Domain linking | P1 - Foundation |
| 8.8 | 5 | Per-KB entity extraction service | P2 - Extraction |
| 8.9 | 5 | Document processing graph integration | P2 - Extraction |
| 8.10 | 3 | Graph query service | P2 - Extraction |
| 8.11 | 5 | Graph-augmented retrieval | P3 - Retrieval |
| 8.12 | 3 | Retrieval strategy abstraction | P3 - Retrieval |
| 8.13 | 5 | LLM schema enrichment suggestions | P4 - Evolution |
| 8.14 | 5 | Schema evolution & re-extraction | P4 - Evolution |
| 8.15 | 3 | Batch re-processing worker | P4 - Evolution |
| 8.16 | 5 | E2E test automation | P4 - Evolution |
| **8.17** | **8** | **Hybrid BM25 + Vector retrieval** | **P5 - Advanced** |

**Total Stories:** 18
**Total Story Points:** 81

### Execution Phases

**Phase 0: Chat Memory Enhancement (Story 8.0)** - 5 SP
- Can start immediately, no GraphRAG dependencies
- Delivers immediate value for multi-turn conversations
- Uses existing LiteLLM infrastructure

**Phase 1: GraphRAG Foundation (Stories 8.1-8.7)** - 29 SP
- Neo4j infrastructure and domain management
- Prerequisites for entity extraction

**Phase 2: Graph Extraction (Stories 8.8-8.10)** - 13 SP
- Entity and relationship extraction pipeline
- Graph query capabilities

**Phase 3: Retrieval Enhancement (Stories 8.11-8.12)** - 8 SP
- Graph-augmented search
- Strategy abstraction for extensibility

**Phase 4: Schema Evolution (Stories 8.13-8.16)** - 18 SP
- Schema suggestions and versioning
- Batch re-processing and E2E tests

**Phase 5: Advanced Retrieval (Story 8.17)** - 8 SP
- Hybrid BM25 + Vector search
- Evaluate after GraphRAG proven

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
