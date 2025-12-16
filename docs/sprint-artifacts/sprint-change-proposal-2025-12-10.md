# Sprint Change Proposal - Prompt Templates & Response Language

**Date:** 2025-12-10
**Triggered By:** User feedback during KB Settings Prompts Tab review
**Scope:** Minor - Direct implementation by dev team
**Estimated Effort:** 2-3 hours

---

## Section 1: Issue Summary

### Issue 1: Missing `{query}` Variable in Prompt Templates
The UI documents `{query}` as an available variable in the "Available Variables" help section, but none of the prompt templates actually use this variable. This creates user confusion when they see the variable documented but not utilized.

### Issue 2: Response Language Input → Dropdown
The response language field is currently a free-text input expecting ISO 639-1 codes. User requests:
- Change to dropdown/select with EN and VI options
- Prompts should automatically use the same language as the selected response language

---

## Section 2: Impact Analysis

| Area | Impact Level | Description |
|------|--------------|-------------|
| Frontend Templates | Low | 4 templates need `{query}` variable added |
| Frontend UI | Low | Response language Input → Select dropdown |
| Frontend Templates | Medium | Add bilingual template variants (EN/VI) |
| Backend Presets | Low | 5 presets need variable placeholders |
| Tests | Low | Unit tests for new language options |

### Files Affected:
- `frontend/src/lib/prompt-templates.ts`
- `frontend/src/components/kb/settings/prompts-panel.tsx`
- `backend/app/core/kb_presets.py`

---

## Section 3: Recommended Approach

**Direct Adjustment** - Modify existing code within current sprint plan.

**Rationale:**
- Changes are localized to specific files
- No architectural changes required
- Backwards compatible (existing saved prompts continue to work)
- Improves UX consistency

---

## Section 4: Detailed Change Proposals

### Change 1: Frontend Prompt Templates - Add `{query}`

**File:** `frontend/src/lib/prompt-templates.ts`

**Pattern to apply to all 4 templates:**

```
OLD:
Context:
{context}

Instructions:
...

NEW:
Context:
{context}

User Question:
{query}

Instructions:
...
```

**Templates to update:**
1. `default_rag`
2. `strict_citations`
3. `conversational`
4. `technical_documentation`

---

### Change 2: Add Supported Languages Constant

**File:** `frontend/src/lib/prompt-templates.ts`

```typescript
// Add at top of file
export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'vi', label: 'Tiếng Việt' },
] as const;

export type SupportedLanguageCode = typeof SUPPORTED_LANGUAGES[number]['code'];
```

---

### Change 3: Add Bilingual Template Structure

**File:** `frontend/src/lib/prompt-templates.ts`

```typescript
export const PROMPT_TEMPLATES_BY_LANGUAGE: Record<SupportedLanguageCode, Record<string, PromptTemplate>> = {
  en: {
    default_rag: {
      id: 'default_rag',
      name: 'Default RAG',
      description: 'Balanced approach for general knowledge base queries',
      system_prompt: `You are a helpful assistant for {kb_name}. Use the following context to answer the user's question.

Context:
{context}

User Question:
{query}

Instructions:
- Answer based only on the provided context
- Cite sources using [1], [2] notation
- If the answer isn't in the context, say so`,
      citation_style: CitationStyle.INLINE,
      uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
    },
    strict_citations: {
      id: 'strict_citations',
      name: 'Strict Citations',
      description: 'Every claim must be explicitly supported by a citation',
      system_prompt: `You are a precise assistant for {kb_name}. Every claim must be supported by a citation.

Context:
{context}

User Question:
{query}

Instructions:
- Every factual statement must include a citation
- Use [Source X] notation after each cited fact
- Do not make any claims without explicit source support
- If you cannot find supporting evidence, state that clearly`,
      citation_style: CitationStyle.INLINE,
      uncertainty_handling: UncertaintyHandling.REFUSE,
    },
    conversational: {
      id: 'conversational',
      name: 'Conversational',
      description: 'Friendly and approachable tone for user exploration',
      system_prompt: `You are a friendly assistant helping users explore {kb_name}.

Context:
{context}

User Question:
{query}

Instructions:
- Respond in a warm, conversational tone
- Provide helpful context and suggestions
- Feel free to expand on related topics when relevant
- Keep responses engaging and easy to understand`,
      citation_style: CitationStyle.NONE,
      uncertainty_handling: UncertaintyHandling.BEST_EFFORT,
    },
    technical_documentation: {
      id: 'technical_documentation',
      name: 'Technical Documentation',
      description: 'Precise technical answers with code examples and footnotes',
      system_prompt: `You are a technical documentation assistant for {kb_name}.

Context:
{context}

User Question:
{query}

Instructions:
- Provide precise, technical answers
- Include code examples when relevant
- Use footnote citations for source reference
- Maintain formal, documentation-style tone
- Include relevant API details or configuration options`,
      citation_style: CitationStyle.FOOTNOTE,
      uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
    },
  },
  vi: {
    default_rag: {
      id: 'default_rag',
      name: 'RAG Mặc định',
      description: 'Cách tiếp cận cân bằng cho các truy vấn cơ sở kiến thức',
      system_prompt: `Bạn là trợ lý hữu ích cho {kb_name}. Sử dụng ngữ cảnh sau để trả lời câu hỏi của người dùng.

Ngữ cảnh:
{context}

Câu hỏi:
{query}

Hướng dẫn:
- Chỉ trả lời dựa trên ngữ cảnh được cung cấp
- Trích dẫn nguồn bằng ký hiệu [1], [2]
- Nếu câu trả lời không có trong ngữ cảnh, hãy nói rõ`,
      citation_style: CitationStyle.INLINE,
      uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
    },
    strict_citations: {
      id: 'strict_citations',
      name: 'Trích dẫn nghiêm ngặt',
      description: 'Mọi khẳng định phải được hỗ trợ rõ ràng bởi trích dẫn',
      system_prompt: `Bạn là trợ lý chính xác cho {kb_name}. Mọi khẳng định phải được hỗ trợ bởi trích dẫn.

Ngữ cảnh:
{context}

Câu hỏi:
{query}

Hướng dẫn:
- Mọi phát biểu thực tế phải bao gồm trích dẫn
- Sử dụng ký hiệu [Nguồn X] sau mỗi thông tin được trích dẫn
- Không đưa ra khẳng định nào mà không có bằng chứng rõ ràng
- Nếu không tìm thấy bằng chứng hỗ trợ, hãy nói rõ điều đó`,
      citation_style: CitationStyle.INLINE,
      uncertainty_handling: UncertaintyHandling.REFUSE,
    },
    conversational: {
      id: 'conversational',
      name: 'Hội thoại',
      description: 'Giọng điệu thân thiện và dễ tiếp cận',
      system_prompt: `Bạn là trợ lý thân thiện giúp người dùng khám phá {kb_name}.

Ngữ cảnh:
{context}

Câu hỏi:
{query}

Hướng dẫn:
- Trả lời với giọng điệu ấm áp, thân thiện
- Cung cấp ngữ cảnh và gợi ý hữu ích
- Thoải mái mở rộng các chủ đề liên quan khi phù hợp
- Giữ câu trả lời hấp dẫn và dễ hiểu`,
      citation_style: CitationStyle.NONE,
      uncertainty_handling: UncertaintyHandling.BEST_EFFORT,
    },
    technical_documentation: {
      id: 'technical_documentation',
      name: 'Tài liệu kỹ thuật',
      description: 'Câu trả lời kỹ thuật chính xác với ví dụ code và chú thích',
      system_prompt: `Bạn là trợ lý tài liệu kỹ thuật cho {kb_name}.

Ngữ cảnh:
{context}

Câu hỏi:
{query}

Hướng dẫn:
- Cung cấp câu trả lời kỹ thuật chính xác
- Bao gồm ví dụ code khi liên quan
- Sử dụng trích dẫn chú thích cuối trang để tham chiếu nguồn
- Duy trì giọng điệu trang trọng, phong cách tài liệu
- Bao gồm chi tiết API hoặc tùy chọn cấu hình liên quan`,
      citation_style: CitationStyle.FOOTNOTE,
      uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
    },
  },
};

// Update helper functions
export function getTemplateOptions(language: SupportedLanguageCode = 'en'): Array<{ id: string; name: string; description: string }> {
  const templates = PROMPT_TEMPLATES_BY_LANGUAGE[language] || PROMPT_TEMPLATES_BY_LANGUAGE['en'];
  return Object.values(templates).map((t) => ({
    id: t.id,
    name: t.name,
    description: t.description,
  }));
}

export function getTemplateById(id: string, language: SupportedLanguageCode = 'en'): PromptTemplate | undefined {
  const templates = PROMPT_TEMPLATES_BY_LANGUAGE[language] || PROMPT_TEMPLATES_BY_LANGUAGE['en'];
  return templates[id];
}
```

---

### Change 4: Response Language Dropdown in Prompts Panel

**File:** `frontend/src/components/kb/settings/prompts-panel.tsx`

**Add import:**
```typescript
import { SUPPORTED_LANGUAGES, type SupportedLanguageCode } from '@/lib/prompt-templates';
```

**Replace Input with Select (lines 349-370):**

```tsx
{/* Response Language Dropdown */}
<FormField
  control={form.control}
  name="prompts.response_language"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Response Language</FormLabel>
      <Select
        onValueChange={field.onChange}
        value={field.value || 'en'}
        disabled={disabled}
      >
        <FormControl>
          <SelectTrigger className="max-w-[200px]" data-testid="response-language-trigger">
            <SelectValue placeholder="Select language" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          {SUPPORTED_LANGUAGES.map((lang) => (
            <SelectItem key={lang.code} value={lang.code}>
              {lang.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <FormDescription>
        AI responses and prompt templates will use this language
      </FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

**Update template loading to be language-aware:**

```tsx
const currentLanguage = (form.watch('prompts.response_language') || 'en') as SupportedLanguageCode;

const applyTemplate = (templateId: string) => {
  const template = getTemplateById(templateId, currentLanguage);
  if (template) {
    form.setValue('prompts.system_prompt', template.system_prompt, { shouldDirty: true });
    form.setValue('prompts.citation_style', template.citation_style, { shouldDirty: true });
    form.setValue('prompts.uncertainty_handling', template.uncertainty_handling, { shouldDirty: true });
  }
  setPendingTemplate(null);
};

// Update template dropdown to show language-specific names
{getTemplateOptions(currentLanguage).map((template) => (
  <SelectItem key={template.id} value={template.id}>
    {template.name}
  </SelectItem>
))}
```

---

### Change 5: Backend Presets - Add Variables

**File:** `backend/app/core/kb_presets.py`

Update each preset's `system_prompt` to include `{kb_name}`, `{context}`, and `{query}`:

**Legal preset:**
```python
system_prompt="""You are a precise legal document assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Cite every claim with footnote notation [1], [2], etc.
- Never speculate beyond the provided documents
- Emphasize accuracy and exact wording from sources
- When uncertain, clearly state limitations
- Maintain formal, professional legal language
- Reference specific document sections when available

Format citations as footnotes at the end of each relevant statement.""",
```

**Technical preset:**
```python
system_prompt="""You are a technical documentation assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide precise, technical answers
- Include code examples when relevant
- Use inline citations [1], [2] to reference sources
- Explain concepts clearly with examples
- Reference specific documentation sections
- Use technical terminology appropriately

Format responses with clear structure using headers and code blocks when needed.""",
```

**Creative preset:**
```python
system_prompt="""You are a creative assistant exploring {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide insightful, creative interpretations
- Make connections between different ideas
- Feel free to suggest new perspectives
- Be conversational and engaging
- Offer possibilities and alternatives
- Encourage exploration and discovery

Respond in an approachable, conversational tone.""",
```

**Code preset:**
```python
system_prompt="""You are a code assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide accurate code with correct syntax
- Explain code functionality clearly
- Reference specific files and line numbers using [1], [2] citations
- Follow established patterns in the codebase
- Suggest best practices when relevant
- Include working code examples

Format code blocks with appropriate language syntax highlighting.""",
```

---

## Section 5: Implementation Handoff

**Scope Classification:** Minor

**Route to:** Development team for direct implementation

**Deliverables:**
1. Updated `frontend/src/lib/prompt-templates.ts` with:
   - `{query}` variable in all templates
   - `SUPPORTED_LANGUAGES` constant
   - `PROMPT_TEMPLATES_BY_LANGUAGE` with EN/VI variants
   - Updated helper functions with language parameter

2. Updated `frontend/src/components/kb/settings/prompts-panel.tsx` with:
   - Response language Select dropdown (replacing Input)
   - Language-aware template loading

3. Updated `backend/app/core/kb_presets.py` with:
   - Variable placeholders in all 5 presets

**Success Criteria:**
- [ ] All 4 frontend templates include `{query}` variable
- [ ] Response language is a dropdown with EN and VI options
- [ ] Loading a template uses the selected language
- [ ] Backend presets include `{kb_name}`, `{context}`, `{query}` variables
- [ ] Existing saved prompts continue to work (backwards compatible)
- [ ] Unit tests pass

---

**Approved by:** Tung Vu
**Date:** 2025-12-10
