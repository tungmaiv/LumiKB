# Story 8-4: LLM Domain Recommendation Service

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-4
**Priority:** HIGH
**Estimated Effort:** 5 story points
**Status:** BACKLOG

---

## Overview

Create an LLM-powered service that analyzes sample documents or KB descriptions and recommends appropriate entity types and relationships for a new domain schema. This enables intelligent domain creation without requiring users to define schemas manually.

---

## Acceptance Criteria

### AC1: Document Analysis Endpoint
**Given** a user uploads sample documents for a new KB
**When** they request domain recommendations
**Then** the LLM analyzes document content
**And** returns recommended entity types with:
  - Suggested names and descriptions
  - Recommended attributes per entity type
  - Confidence scores (0.0-1.0)
  - Extraction hints for the entity type

### AC2: Description-Based Recommendations
**Given** a user provides a text description of their KB purpose
**When** they request domain recommendations
**Then** the LLM generates suggestions based on:
  - The stated purpose/use case
  - Industry/domain keywords
  - Similar system templates
**And** returns a ranked list of recommendations

### AC3: Relationship Inference
**Given** entity types have been recommended or selected
**When** relationship recommendations are requested
**Then** the LLM suggests relationships between entities including:
  - Relationship name (verb-based, e.g., MANAGES, CONTAINS)
  - Source and target entity types
  - Whether bidirectional
  - Confidence score

### AC4: Template Matching
**Given** system domain templates exist
**When** recommendations are generated
**Then** the service identifies if an existing template closely matches
**And** suggests template selection with customization notes
**And** provides a match score (percentage)

### AC5: LiteLLM Integration
**Given** the LLM Model Registry (Story 7-9) has NER models registered
**When** domain recommendations are generated
**Then** the configured NER model is used via LiteLLM
**And** the request includes appropriate system prompts
**And** structured output (JSON) is requested

---

## Technical Notes

### API Endpoints

```
POST /api/v1/domains/recommend
{
  "description": "Optional text description of KB purpose",
  "sample_documents": ["doc_id_1", "doc_id_2"],  // Optional
  "max_entity_types": 10,
  "max_relationships": 15
}

Response:
{
  "entity_types": [
    {
      "name": "Server",
      "description": "Physical or virtual computing resources",
      "confidence": 0.92,
      "attributes": [
        {"name": "hostname", "type": "string", "required": true},
        {"name": "ip_address", "type": "string"}
      ],
      "extraction_hints": "Look for server names, hostnames, machine identifiers"
    }
  ],
  "relationships": [
    {
      "name": "HOSTS",
      "from_entity": "Server",
      "to_entity": "Service",
      "bidirectional": false,
      "confidence": 0.88
    }
  ],
  "template_matches": [
    {
      "template_id": "uuid",
      "template_name": "IT Operations",
      "match_score": 0.85,
      "customization_notes": "Add 'Container' entity type for your Kubernetes docs"
    }
  ]
}
```

### LLM Prompt Structure

```python
DOMAIN_RECOMMENDATION_PROMPT = """
Analyze the following content and recommend a knowledge graph schema.

Content Description: {description}
Sample Content: {sample_text}

Generate entity types that would be useful for building a knowledge graph.
For each entity type, suggest:
1. A clear, noun-based name (e.g., "Server", "Contract", "Person")
2. A brief description of what this entity represents
3. Key attributes that instances would have
4. Extraction hints for identifying this entity in text

Also suggest relationships between the entity types using verb-based names
(e.g., "MANAGES", "CONTAINS", "BELONGS_TO").

Return the response as JSON with the following structure:
{
  "entity_types": [...],
  "relationships": [...],
  "reasoning": "Brief explanation of the recommended schema"
}
"""
```

### Service Implementation

```python
# backend/app/services/domain_recommendation_service.py
class DomainRecommendationService:
    def __init__(self, litellm_client: LiteLLMClient, model_registry: ModelRegistry):
        self.llm = litellm_client
        self.models = model_registry

    async def recommend_schema(
        self,
        description: Optional[str] = None,
        sample_documents: Optional[List[UUID]] = None,
        max_entity_types: int = 10
    ) -> DomainRecommendation:
        # Get configured NER model
        ner_model = await self.models.get_active_model("ner")

        # Build prompt with description and/or document samples
        prompt = self._build_prompt(description, sample_documents)

        # Call LLM with structured output
        response = await self.llm.chat_completion(
            model=ner_model.model_id,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return self._parse_recommendation(response)

    async def match_templates(
        self,
        entity_types: List[str]
    ) -> List[TemplateMatch]:
        """Find system templates that match recommended entity types."""
        templates = await self._get_system_templates()
        matches = []

        for template in templates:
            score = self._calculate_match_score(entity_types, template)
            if score > 0.5:  # Threshold for relevance
                matches.append(TemplateMatch(
                    template_id=template.id,
                    template_name=template.name,
                    match_score=score
                ))

        return sorted(matches, key=lambda m: m.match_score, reverse=True)
```

---

## Definition of Done

- [ ] Document analysis endpoint implemented
- [ ] Description-based recommendations working
- [ ] Relationship inference implemented
- [ ] Template matching with scores
- [ ] LiteLLM integration with NER model
- [ ] Structured JSON output parsing
- [ ] Error handling for LLM failures
- [ ] Unit tests with mocked LLM responses
- [ ] Integration test with real LLM
- [ ] API documentation updated

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-3 (System Templates), Story 7-9 (Model Registry)
**Next Story:** Story 8-5 (Domain Management API)
