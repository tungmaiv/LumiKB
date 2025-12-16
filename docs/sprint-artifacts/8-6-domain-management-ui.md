# Story 8-6: Domain Management UI

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-6
**Priority:** HIGH
**Estimated Effort:** 8 story points
**Status:** BACKLOG

---

## Overview

Create the frontend interface for domain management, allowing users to create, edit, and visualize domain schemas with entity types and relationships. Includes LLM-assisted schema recommendations and visual schema builder.

---

## Acceptance Criteria

### AC1: Domain List View
**Given** a user navigates to domain management
**When** the page loads
**Then** they see:
  - List of their own domains
  - List of public domains
  - List of system templates (with "System" badge)
  - Search/filter functionality
  - "Create Domain" button

### AC2: Domain Creation Wizard
**Given** a user clicks "Create Domain"
**When** the wizard opens
**Then** they can choose:
  - **Start from scratch** - Empty domain
  - **Clone template** - Copy from system template
  - **AI-assisted** - LLM recommendations
**And** each path leads to the schema editor

### AC3: LLM Recommendation Flow
**Given** a user selects "AI-assisted" creation
**When** they provide KB description or sample documents
**Then** the UI shows:
  - Loading state while LLM processes
  - Recommended entity types with confidence scores
  - Recommended relationships
  - Template matches (if any)
  - "Accept All" / "Select & Edit" options

### AC4: Visual Schema Editor
**Given** a domain is being edited
**When** the schema editor is displayed
**Then** the user can:
  - Add/edit/remove entity types
  - Define attributes for each entity type
  - Set colors and icons for entity types
  - Add/edit/remove relationship types
  - Drag-and-drop reordering
  - Preview schema as a graph visualization

### AC5: Entity Type Editor
**Given** an entity type is being edited
**When** the editor modal is open
**Then** the user can configure:
  - Name (validated, unique within domain)
  - Description
  - Attributes (name, type, required flag)
  - Color picker
  - Icon selector
  - Extraction hints (multiline text)

### AC6: Relationship Type Editor
**Given** a relationship type is being edited
**When** the editor modal is open
**Then** the user can configure:
  - Relationship name (verb-based)
  - Source entity type (dropdown)
  - Target entity type (dropdown)
  - Bidirectional toggle
  - Optional attributes

### AC7: Schema Visualization
**Given** a domain has entity types and relationships
**When** the visualization panel is shown
**Then** a graph diagram displays:
  - Entity types as colored nodes
  - Relationships as directed/bidirectional edges
  - Labels on nodes and edges
  - Interactive (click to select, hover for details)

### AC8: Save and Validation
**Given** the user makes changes to a domain
**When** they click "Save"
**Then** validation runs:
  - Required fields checked
  - Unique names validated
  - Relationship references validated
**And** errors are displayed inline
**And** successful save shows confirmation

---

## Technical Notes

### Component Structure

```
src/components/domains/
├── DomainListPage.tsx
├── DomainCard.tsx
├── CreateDomainWizard.tsx
├── LLMRecommendationPanel.tsx
├── SchemaEditor.tsx
├── EntityTypeCard.tsx
├── EntityTypeModal.tsx
├── RelationshipTypeCard.tsx
├── RelationshipTypeModal.tsx
├── SchemaVisualization.tsx
├── AttributeEditor.tsx
├── ColorPicker.tsx
└── IconSelector.tsx
```

### React Query Hooks

```typescript
// src/hooks/useDomains.ts
export function useDomains(options?: { includePublic?: boolean; includeSystem?: boolean }) {
  return useQuery({
    queryKey: ['domains', options],
    queryFn: () => api.get('/domains', { params: options }),
    staleTime: 5 * 60 * 1000
  });
}

export function useDomain(domainId: string) {
  return useQuery({
    queryKey: ['domain', domainId],
    queryFn: () => api.get(`/domains/${domainId}`)
  });
}

export function useDomainRecommendations() {
  return useMutation({
    mutationFn: (params: { description?: string; sampleDocuments?: string[] }) =>
      api.post('/domains/recommend', params)
  });
}

export function useCreateDomain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DomainCreate) => api.post('/domains', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['domains'] })
  });
}
```

### Schema Visualization (react-force-graph or similar)

```typescript
// SchemaVisualization.tsx
import ForceGraph2D from 'react-force-graph-2d';

interface SchemaVisualizationProps {
  entityTypes: EntityType[];
  relationshipTypes: RelationshipType[];
  onNodeClick?: (entityType: EntityType) => void;
}

export function SchemaVisualization({ entityTypes, relationshipTypes, onNodeClick }: SchemaVisualizationProps) {
  const graphData = useMemo(() => ({
    nodes: entityTypes.map(et => ({
      id: et.id,
      name: et.name,
      color: et.color,
      icon: et.icon
    })),
    links: relationshipTypes.map(rt => ({
      source: rt.from_entity_type_id,
      target: rt.to_entity_type_id,
      name: rt.name,
      bidirectional: rt.bidirectional
    }))
  }), [entityTypes, relationshipTypes]);

  return (
    <ForceGraph2D
      graphData={graphData}
      nodeLabel="name"
      linkLabel="name"
      nodeColor={node => node.color}
      linkDirectionalArrowLength={6}
      onNodeClick={onNodeClick}
    />
  );
}
```

### State Management

```typescript
// Domain editor uses local state with form library (react-hook-form)
interface DomainEditorState {
  domain: DomainDraft;
  selectedEntityType: EntityType | null;
  selectedRelationshipType: RelationshipType | null;
  isDirty: boolean;
  validationErrors: ValidationError[];
}
```

---

## Definition of Done

- [ ] Domain list page with filtering
- [ ] Create domain wizard (3 paths)
- [ ] LLM recommendation integration
- [ ] Visual schema editor
- [ ] Entity type CRUD UI
- [ ] Relationship type CRUD UI
- [ ] Schema visualization graph
- [ ] Form validation with error display
- [ ] Loading states and error handling
- [ ] Responsive design (desktop focus)
- [ ] Unit tests for components
- [ ] E2E test for domain creation flow
- [ ] Accessibility (keyboard navigation)

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-5 (Domain Management API), Story 8-4 (LLM Recommendations)
**Next Story:** Story 8-7 (KB-Domain Linking)
