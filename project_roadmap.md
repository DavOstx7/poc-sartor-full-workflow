# Sartor Ad Engine: Project Roadmap

> **Version:** 1.1  
> **Date:** 2026-01-09  
> **Status:** Active Development  

---

## Project Context

**What We're Building:**  
An automated multi-agent system that generates high-fidelity static advertisements for **eCommerce products** personalized for distinct customer segments (ICPs).

> [!NOTE]
> **Scope:** Physical goods sold via eCommerce (DTC brands, online retailers, marketplaces). SaaS, services, and digital-only products are out of scope.

**Core Architecture:**  
5 LLM agents + 1 deterministic composition module, orchestrated via LangGraph:

```
Product Input → Segmentation → Strategy → Concept → Copy → Design → Composition → Final Ads
```

**Key Architectural Decisions:**
1. Strategy before creative execution
2. Full accumulated state (no context loss between agents)
3. Actual product images from catalog (not AI-generated products)
4. Deterministic text/product composition (not image-gen rendered text)
5. ICP-parallel, step-sequential processing
6. **Flexible brand model** (supports DTC single-brand and multi-brand retailers with explicit brand strategy)

**Reference Document:**  
[`project_architecture.md`](file:///C:/Users/DELL/Documents/poc-sartor-full-workflow/project_architecture.md) — The authoritative technical specification. Read this first in any session.

---

## Prerequisites

Before starting development phases, ensure access to:

| Requirement | Purpose | Notes |
|-------------|---------|-------|
| **LLM API Key** | Agents 1-4 | Gemini API or Anthropic API (or both) |
| **Image Gen API Key** | Design Agent | Imagen 3 (Google) or Flux API |
| **Python 3.11+** | Runtime | Required for modern type hints |
| **Node.js** (optional) | If using HTML/CSS templates for composition | Only if chosen for Composition Module |

---

## Phase Overview

| Phase | Name | Status | Dependencies |
|-------|------|--------|--------------|
| 0 | Architecture Design | ✅ Complete | — |
| 1 | Agent Prompt Engineering | ✅ Complete | Phase 0 |
| 2 | Project Scaffolding | ✅ Complete | Phase 0 |
| 3 | Agent Implementation | ✅ Complete | Phase 1, 2 |
| 4 | Composition Module | ✅ Complete | Phase 2 |
| 5 | Orchestration Layer | ✅ Complete | Phase 3, 4 |
| 6 | End-to-End Testing | 🔲 Not Started | Phase 5 |
| 7 | Iteration & Refinement | 🔲 Not Started | Phase 6 |

> [!TIP]
> **Phase 1 and Phase 2 can run in parallel.** They have no dependencies on each other—only on Phase 0. This enables team parallelization if desired.

---

## Phase 0: Architecture Design ✅

> **Status:** Complete

**Deliverable:** [`project_architecture.md`](file:///C:/Users/DELL/Documents/poc-sartor-full-workflow/project_architecture.md)

This document defines:
- System input schemas (Product, Store Brand, Product Brand, Brand Strategy, Channel, Store Context)
- Agent definitions with missions, inputs, outputs, and JSON schemas
- State management strategy
- Technical stack recommendations
- Key architectural decisions with rationale (including brand flexibility)

---

## Phase 1: Agent Prompt Engineering

> **Role:** You are an Expert Prompt Engineer specializing in multi-agent LLM systems for creative and marketing workflows.

### Goal

Create production-quality system prompts for each of the 5 agents that will reliably produce high-quality, schema-compliant outputs.

### Inputs Required

- `project_architecture.md` — Read the full document
- Understand each agent's mission, input context, and output schema

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `agents/segmentation/prompts.py` | System prompt for Segmentation Agent |
| `agents/strategy/prompts.py` | System prompt for Strategy Agent |
| `agents/concept/prompts.py` | System prompt for Concept Agent |
| `agents/copy/prompts.py` | System prompt for Copy Agent |
| `agents/design/prompts.py` | System prompt for Design Agent (image-gen prompt template) |

### Key Requirements

1. **Schema Enforcement:** Prompts must instruct the LLM to output valid JSON matching the defined schemas
2. **Role Clarity:** Each agent must understand its specific mission and boundaries (no overlap)
3. **Context Utilization:** Prompts must reference the accumulated state (product, store brand, product brand, brand strategy, ICP, prior outputs)
4. **Quality Guardrails:** Include constraints to prevent generic, off-brand, or hallucinated outputs
5. **Tone Adaptation:** Copy and Strategy prompts must adapt tone based on ICP preferences AND brand strategy (which brand dominates)
6. **LangChain Compatibility:** Prompts should be designed for use with LangChain's `with_structured_output()` pattern
7. **Brand Strategy Awareness:** Prompts must handle all three brand strategies (store_dominant, product_dominant, co_branded) appropriately

> [!IMPORTANT]
> **Design Agent is different.** Unlike agents 1-4, the Design Agent uses an **image generation prompt template** (for Imagen/Flux), not an LLM system prompt. This is scene-description prompting, not instruction prompting. Handle it separately.

### Success Criteria

- [ ] Each prompt can be tested standalone with mock input and produces valid, high-quality output
- [ ] Outputs are clearly differentiated per ICP (not generic)
- [ ] No schema violations in output JSON
- [ ] Prompts are modular and maintainable (not monolithic walls of text)
- [ ] Design Agent template produces coherent scene descriptions for image generation

---

## Phase 2: Project Scaffolding

> **Role:** You are a Senior Python Engineer setting up a clean, maintainable project structure for a LangGraph-based multi-agent system.

> [!NOTE]
> This phase can run **in parallel with Phase 1**. Coordinate on the `agents/` folder structure if working simultaneously.

### Goal

Create the foundational project structure, shared models, configuration, and dependencies so that agent implementation can proceed smoothly.

### Inputs Required

- `project_architecture.md` — For schema definitions
- Knowledge of LangGraph, Pydantic, and Python best practices

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `pyproject.toml` or `requirements.txt` | Dependencies (langchain, langgraph, pydantic, pillow, etc.) |
| `src/models/` | Pydantic models for all schemas (Product, StoreBrand, ProductBrand, BrandStrategy, ICP, StrategicBrief, etc.) |
| `src/state.py` | `AdCreationState` dataclass for LangGraph state management |
| `src/config.py` | Configuration (API keys, model names, paths) |
| `src/utils/` | Shared utilities (LLM factory, image handling, etc.) |
| `agents/` | Skeleton folders for each agent (empty `__init__.py`, placeholder files) |
| `tests/` | Test folder structure |
| `data/samples/` | Sample input JSON files for testing |

### Key Requirements

1. **Pydantic Models:** All schemas from `project_architecture.md` must be defined as Pydantic models
2. **Type Safety:** Full type hints throughout
3. **Configuration:** API keys and model names must be configurable (env vars or config file)
4. **LangGraph Compatibility:** State object must be compatible with LangGraph's state management
5. **Sample Data:** Include at least 2 sample product inputs with realistic data (one DTC, one multi-brand retailer)
6. **Brand Model:** `BrandContext` model should be reusable for both `store_brand` and `product_brand` fields

### Success Criteria

- [ ] `pip install -e .` or `pip install -r requirements.txt` succeeds
- [ ] All Pydantic models validate correctly with sample data
- [ ] Folder structure is clean and follows Python best practices
- [ ] Config can be loaded from environment variables

---

## Phase 3: Agent Implementation

> **Role:** You are a LangGraph/LangChain Developer implementing the individual agent nodes for a multi-agent advertising workflow.

### Goal

Implement each of the 5 agents as LangGraph-compatible nodes that consume state, call an LLM, and return structured outputs.

### Inputs Required

- `project_architecture.md` — Agent definitions and schemas
- `agents/*/prompts.py` — System prompts from Phase 1
- `src/models/` — Pydantic models from Phase 2
- `src/state.py` — State object from Phase 2

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `agents/segmentation/agent.py` | Segmentation Agent node implementation |
| `agents/strategy/agent.py` | Strategy Agent node implementation |
| `agents/concept/agent.py` | Concept Agent node implementation |
| `agents/copy/agent.py` | Copy Agent node implementation |
| `agents/design/agent.py` | Design Agent node implementation (calls image-gen API) |

### Key Requirements

1. **LangGraph Node Pattern:** Each agent is a function that takes state, processes, and returns updated state
2. **Structured Output:** Use LangChain's structured output parsing to guarantee schema compliance
3. **Error Handling:** Graceful handling of LLM failures, malformed outputs, API errors
4. **Logging:** Clear logging of inputs, prompts, and outputs for debugging
5. **Testability:** Each agent should be testable in isolation

### Agent-Specific Notes

| Agent | Special Considerations |
|-------|------------------------|
| **Segmentation** | May need web search tool for market research |
| **Strategy** | Runs once per ICP (loop over ICPs); must respect `brand_strategy` for tone |
| **Concept** | Must output `product_placement` directives for Composition; visual style from dominant brand |
| **Copy** | Must enforce character limits from `channel.text_constraints`; voice from dominant brand |
| **Design** | Calls image generation API (Imagen/Flux), returns image path; aesthetic from dominant brand |

### Success Criteria

- [ ] Each agent can be run standalone with mock state
- [ ] Outputs match defined Pydantic schemas
- [ ] Different ICPs produce meaningfully different outputs
- [ ] Error cases are handled gracefully (no crashes)

---

## Phase 4: Composition Module

> **Role:** You are a Python Developer specializing in image processing and programmatic design systems.

### Goal

Implement the deterministic Composition Module that combines the background scene, actual product image, and text to produce the final ad.

### Inputs Required

- `project_architecture.md` — Composition Module requirements
- `src/models/` — `CreativeConcept`, `AdCopy`, `BrandContext` models
- Understanding of Pillow (PIL) or similar image processing library

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `src/composition/compositor.py` | Main composition logic |
| `src/composition/text_renderer.py` | Text overlay with font/color/position handling |
| `src/composition/product_placer.py` | Product image placement with background removal |
| `src/composition/templates/` | Layout templates for different archetypes (optional) |
| `assets/fonts/` | Brand-approved fonts |

### Key Requirements

1. **Product Image Handling:** 
   - Load product image from URL or path
   - Remove background if needed (using `rembg` or similar)
   - Place according to `concept.product_placement` directives

2. **Text Rendering:**
   - Render headline, body, CTA with brand fonts and colors (from **dominant brand** per `brand_strategy`)
   - Respect layout archetype positioning
   - Handle text wrapping for long copy
   - Add logo(s) based on `brand_strategy`:
     - `store_dominant`: Store logo prominent
     - `product_dominant`: Product brand logo prominent, "Available at [Store]" text
     - `co_branded`: Both logos visible

3. **Output:**
   - Export final image at exact `channel.dimensions`
   - Support PNG and JPEG output

4. **Layout Archetypes:**
   - "Hero Product with Stat Overlay"
   - "Problem/Solution Split"
   - "Lifestyle Context Shot"
   - (Add more as needed)

### Success Criteria

- [ ] Given a background image, product image, and copy, produces a correctly composed ad
- [ ] Text is legible and correctly positioned
- [ ] Product is correctly placed per directives
- [ ] Output dimensions match channel requirements
- [ ] Works with various product image formats (with/without transparency)

---

## Phase 5: Orchestration Layer

> **Role:** You are a LangGraph Architect wiring together a multi-agent workflow with parallel processing and state management.

### Goal

Connect all agents and the Composition Module into a complete LangGraph workflow that processes a product input and outputs personalized ads for each ICP.

### Inputs Required

- `project_architecture.md` — Execution flow and parallelization strategy
- All implemented agents from Phase 3
- Composition Module from Phase 4
- `src/state.py` — State object

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `src/graph.py` | LangGraph workflow definition |
| `src/runner.py` | CLI or script to execute the full pipeline |
| `src/checkpoints.py` | (Optional) Checkpoint/resume logic |

### Key Requirements

1. **Workflow Structure:**
   ```
   START → Segmentation → [Fan-out to ICPs] → Strategy → Concept → Copy → Design → Composition → END
   ```

2. **Parallelization:**
   - Different ICPs should process in parallel (or configurable)
   - Steps within an ICP are sequential

3. **State Flow:**
   - Single `AdCreationState` object accumulates all outputs
   - Each agent reads full state, writes to its designated field

4. **Error Handling:**
   - If one ICP fails, others should still complete
   - Errors logged to `state.errors`

5. **Observability:**
   - Log entry/exit of each node
   - Track timing per agent

### Success Criteria

- [ ] Full pipeline runs from product input to final ads
- [ ] Multiple ICPs are processed (serially or in parallel)
- [ ] State is correctly accumulated and accessible at each step
- [ ] Failures in one ICP don't crash the entire run
- [ ] Can run via CLI with a sample product JSON

---

## Phase 6: End-to-End Testing

> **Role:** You are a QA Engineer validating the complete ad generation pipeline with diverse inputs.

### Goal

Run the full pipeline with multiple test products across different categories and validate that outputs meet quality standards.

### Inputs Required

- Complete working pipeline from Phase 5
- Sample product data (create diverse test cases)

### Test Cases to Execute

| Test Case | Product Category | Brand Type | Expected Validation |
|-----------|------------------|------------|---------------------|
| TC-01 | Electronics (Headphones) | Premium | Multiple ICPs, premium tone |
| TC-02 | Skincare (Serum) | Luxury | Aspirational messaging |
| TC-03 | Fashion (Sneakers) | Streetwear | Youth-oriented, bold visuals |
| TC-04 | Home (Candle) | Artisanal | Warm, lifestyle imagery |
| TC-05 | Tech (Smartwatch) | Mass-market | Feature-focused, accessible |

### Validation Checklist (Per Output)

- [ ] ICP profiles are distinct and plausible
- [ ] Strategy addresses specific ICP pain points
- [ ] Concept is creative and aligned with strategy
- [ ] Copy is within character limits
- [ ] Copy tone matches ICP preferences
- [ ] Final ad has correct dimensions
- [ ] Product is accurately represented (actual catalog image)
- [ ] Text is legible and well-positioned
- [ ] Brand colors and logo are correctly applied

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| `tests/e2e/` | End-to-end test scripts |
| `output/` | Generated ads organized by product/ICP |
| `docs/test_results.md` | Summary of test runs with pass/fail and notes |

### Success Criteria

- [ ] All test cases run without errors
- [ ] At least 80% of outputs pass visual/quality review
- [ ] Edge cases documented (what fails and why)

---

## Phase 7: Iteration & Refinement

> **Role:** You are an AI Quality Engineer tuning prompts and fixing edge cases based on test results.

### Goal

Analyze outputs from Phase 6, identify quality issues, and refine prompts/logic to improve output quality.

### Inputs Required

- Test results from Phase 6
- Generated outputs (ads, intermediate JSON)
- Understanding of common failure modes

### Common Issues to Address

| Issue | Likely Cause | Fix Location |
|-------|--------------|--------------|
| Generic messaging | Weak prompt constraints | `prompts.py` |
| ICP overlap | Segmentation not differentiating | Segmentation prompt |
| Off-brand tone | Tone not enforced | Strategy/Copy prompts |
| Text overlap in image | Bad layout logic | Composition Module |
| Product placement wrong | Placement directives unclear | Concept prompt + Compositor |

### Iteration Process

1. **Diagnose:** Identify which agent caused the quality issue
2. **Hypothesize:** What prompt change or logic fix would help?
3. **Implement:** Make targeted change
4. **Validate:** Re-run affected test cases
5. **Document:** Log what was changed and why

### Outputs to Produce

| Deliverable | Description |
|-------------|-------------|
| Updated `prompts.py` files | Refined prompts based on learnings |
| Updated `compositor.py` | Bug fixes or improvements |
| `docs/iteration_log.md` | Log of changes made and their impact |

### Success Criteria

- [ ] Pass rate increases from Phase 6 baseline
- [ ] Known issues resolved
- [ ] No regressions introduced
- [ ] Lessons documented for future reference

---

## Quick Reference: File Structure

```
poc-sartor-full-workflow/
├── project_architecture.md     # Technical specification (READ FIRST)
├── project_roadmap.md          # This document
├── pyproject.toml              # Dependencies
├── src/
│   ├── models/                 # Pydantic schemas
│   ├── state.py                # AdCreationState
│   ├── config.py               # Configuration
│   ├── graph.py                # LangGraph workflow
│   ├── runner.py               # CLI entry point
│   ├── composition/            # Composition Module
│   └── utils/                  # Shared utilities
├── agents/
│   ├── segmentation/
│   │   ├── prompts.py
│   │   └── agent.py
│   ├── strategy/
│   │   ├── prompts.py
│   │   └── agent.py
│   ├── concept/
│   │   ├── prompts.py
│   │   └── agent.py
│   ├── copy/
│   │   ├── prompts.py
│   │   └── agent.py
│   └── design/
│       ├── prompts.py
│       └── agent.py
├── assets/
│   └── fonts/
├── data/
│   └── samples/                # Sample product inputs
├── output/                     # Generated ads
├── tests/
│   └── e2e/
└── docs/
    ├── test_results.md
    └── iteration_log.md
```

---

## Session Handoff Checklist

When starting a new session for any phase, ensure:

1. ✅ Read `project_architecture.md` first
2. ✅ Read the relevant phase section in this roadmap
3. ✅ Check the "Status" column to confirm dependencies are complete
4. ✅ Review any outputs from prior phases (prompts, models, etc.)
5. ✅ Confirm success criteria before marking phase complete

---

*Document maintained by: [Team Lead Name]*  
*Last updated: 2026-01-09*
