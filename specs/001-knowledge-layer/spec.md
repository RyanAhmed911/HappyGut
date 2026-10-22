# Feature Specification: Knowledge layer

**Feature Branch**: `001-knowledge-layer`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Knowledge layer: Bangladeshi food knowledge graph, guideline Rule Cards and contextual hybrid RAG"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Look up what is in a Bangladeshi dish (Priority: P1)

When the meal check names a dish ("kacchi biryani", "কাচ্চি", "kachchi"), the system finds the matching dish and returns its typical ingredients and gut-relevant components (fat, insoluble fibre, lactose, fermentable carbohydrates, spice, skins/seeds/nuts), each with the source it came from.

**Why this priority**: Without dish knowledge there is no verdict. This is the foundation of the hero flow.

**Independent Test**: Query the knowledge layer with English, Bangla and Banglish names for 20 seeded dishes and check that the right dish, components and sources come back.

**Acceptance Scenarios**:

1. **Given** an approved seeded dish, **When** it is looked up by its English name, Bangla name or a listed Banglish alias, **Then** the same canonical dish is returned with its components and sources.
2. **Given** a misspelt Banglish name within a small edit distance of an alias, **When** it is looked up, **Then** the right dish is the top candidate, together with a match confidence.
3. **Given** a dish name that isn't in the knowledge base, **When** it is looked up, **Then** no dish is returned with high confidence, and the name is recorded in a knowledge-gap list.

---

### User Story 2 - Find the guideline rules that apply (Priority: P1)

Given a component, its level, the patient's diagnosis, phenotype and disease state, the system returns the applicable Rule Cards. Each Rule Card has a severity, a hard-rule flag, a Bangla and English recommendation, and a citation with the exact supporting quote.

**Why this priority**: Verdicts must be grounded in published IBD guidance (Constitution IV). The stricturing hard rules are a safety requirement (Constitution II).

**Independent Test**: For a fixed set of (component, level, diagnosis, phenotype, state) inputs, check that the returned Rule Cards match a hand-made expected table.

**Acceptance Scenarios**:

1. **Given** stricturing Crohn's and a dish with insoluble fibre at medium or higher, **When** rules are requested, **Then** a hard Rule Card is returned.
2. **Given** remission and a component with no applicable rule, **When** rules are requested, **Then** no rule is returned (and nothing is invented).
3. **Given** any returned Rule Card, **Then** it has a citation, a licence and a quote, and its status is approved.

---

### User Story 3 - Retrieve supporting guideline passages (Priority: P2)

For an explanation, the system retrieves the top supporting passages from licensed guideline text. Each passage carries a short context header and a source ID, and Bangla queries can find English passages.

**Why this priority**: Gives explanations richer, cited context beyond the Rule Card itself. It's also needed for the contextual RAG and ablation evidence.

**Independent Test**: Run a 30-question guideline Q&A set and measure how often the gold passage appears in the top 5.

**Acceptance Scenarios**:

1. **Given** a structured query (component + phenotype + state), **When** retrieval runs, **Then** at most 5 reranked passages are returned, each with a source ID and a licence.
2. **Given** a Bangla query, **When** retrieval runs, **Then** relevant English guideline passages are returned.
3. **Given** a query with no relevant passages, **Then** the top reranked score is below the evidence threshold and the result is flagged as weak evidence.

---

### User Story 4 - Gentler alternatives (Priority: P2)

For a dish judged risky, the system can suggest one or two familiar dishes with lower risk for the same patient.

**Independent Test**: Every seeded dish with a high-risk component has at least one alternative that exists and has a lower component risk.

---

### Edge Cases
- A dish has several regional names or spellings → all resolve through aliases.
- A source's licence doesn't allow storing full text → only the Rule Card (structured rule + short quote + citation) is stored.
- A composition value is missing → the component is marked unknown, not guessed. Unknown lowers confidence.
- Neo4j is unreachable → lookups fail fast with a clear error; the meal check returns ⚪ "Not sure".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST hold at least 50 approved Bangladeshi dishes, each with English and Bangla names, Banglish aliases, ingredients, component levels and sources.
- **FR-002**: Component levels MUST use the controlled vocabulary and levels defined in `.claude/skills/add-dish`.
- **FR-003**: The system MUST hold at least 25 approved Rule Cards drawn from ESPEN, IOIBD, AGA and FODMAP literature, each with a severity, hard flag, Bangla and English recommendation, citation, licence and exact quote.
- **FR-004**: Dish lookup MUST accept English, Bangla and Banglish input and return candidates with match confidence.
- **FR-005**: Rule lookup MUST filter by component, level, diagnosis, phenotype and disease state.
- **FR-006**: Guideline passage retrieval MUST combine keyword and semantic search, rerank the results, and return at most 5 passages with source IDs.
- **FR-007**: Each guideline chunk MUST carry a generated context header, which is used for both keyword and semantic indexing.
- **FR-008**: Only items with `status: approved` MUST be loaded; every loaded item MUST keep its source and licence.
- **FR-009**: Unknown dish names MUST be recorded to a knowledge-gap list.
- **FR-010**: The knowledge layer MUST be exposed to agents as read-only MCP tools (`search_dish`, `get_components`, `explain_verdict_path`).
- **FR-011**: The knowledge build MUST be re-runnable from seed files without manual steps.

### Key Entities
- **Dish**: canonical ID, names (en/bn), aliases, cuisine, preparation, ingredients, components, gentler alternatives, sources.
- **Ingredient**: ID, name, food-composition code (Bangladesh table or USDA), components per 100 g.
- **Component**: one of the controlled vocabulary terms.
- **Rule Card**: component, minimum level, applicability (diagnosis, phenotype, state), severity, hard flag, recommendations, source.
- **Paper / Source**: citation, DOI/PMID, licence.
- **Guideline chunk**: text, context header, source ID, licence, section.

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: ≥ 50 approved dishes and ≥ 25 approved Rule Cards loaded, each with sources and licences.
- **SC-002**: Dish resolution top-1 accuracy ≥ 90% on a 100-name English/Bangla/Banglish test set.
- **SC-003**: Rule lookup matches the expected table for 100% of the hand-made cases, including all stricturing hard rules.
- **SC-004**: Guideline retrieval Recall@5 ≥ 0.8 on the 30-question Q&A set, and contextual hybrid retrieval beats naive vector retrieval (ablation recorded).
- **SC-005**: A full rebuild from seeds finishes in under 30 minutes on a laptop CPU (no GPU needed).

## Assumptions
- Dishes are curated by the team with LLM help and reviewed by a human; scale is quality over quantity for the prototype.
- Guideline text is stored only where the licence allows; otherwise Rule Cards carry short quotes with citations.
- Component levels are typical-recipe estimates, documented as such.
- Embeddings are computed on CPU; context headers use a free cloud LLM tier (or local models in an optional one-off GPU session).
