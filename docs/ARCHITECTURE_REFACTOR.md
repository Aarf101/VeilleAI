# AGENTICNOTES - REFACTORED MULTI-AGENT ARCHITECTURE

## Executive Summary

The AgenticNotes project has been refactored from a simple **pipeline** into a true **multi-agent agentic system** with clear separation of concerns and central orchestration.

---

## Architecture Overview

```
ORCHESTRATOR (Central Coordinator)
    |
    +---> COLLECTOR (Raw Data Acquisition)
    |
    +---> FILTER AGENT (Stateless Semantic Scoring)
    |
    +---> ANALYSIS AGENT (Novelty + Categorization)
    |
    +---> SYNTHESIZER (Structured Output Generation)
```

### Key Principle
The **Orchestrator** doesn't just pipe data; it:
- Controls execution order
- Makes workflow decisions
- Triggers synthesis conditionally
- Maintains state across the entire cycle

---

## Agent Responsibilities (Revised)

### 1. **COLLECTOR AGENT** (Simplified)
- **Responsibility**: Raw data acquisition + basic metadata extraction
- **Input**: Configuration (RSS feeds, APIs)
- **Output**: List of collected items with basic structure
- **NO**: Filtering, novelty detection, decision logic

```python
{
    'url': str,
    'title': str,
    'content': str,
    'summary': str,
    'source': str,
    'published': str,
    'fetched_at': str
}
```

### 2. **FILTER AGENT** (Stateless)
- **Responsibility**: Semantic relevance scoring against topics
- **Key Feature**: STATELESS - each call is independent
- **Input**: (items, topics, threshold)
- **Output**: [(item, score)] for items passing threshold
- **NO**: State, memory, novelty detection

**Principle**: Pure function for semantic similarity
```python
(item, topics) -> score [0, 1]
```

### 3. **ANALYSIS AGENT** (Fixed Scope)
- **Responsibility**: 
  - Novelty detection (vs. previous period only)
  - Simple categorization (keyword-based)
- **Input**: Filtered items from Filter Agent
- **Output**: [(item, category)] for novel items only
- **NO**: Long-term trend prediction, complex prognosis

**Categories**: `announcement`, `event`, `trend`, `analysis`, `regulation`, `other`

### 4. **SYNTHESIZER** (Unchanged)
- **Responsibility**: Structured note generation from novel items
- **Input**: Novel items + context
- **Output**: Formatted markdown summary
- **Modes**: Fast (template) or LLM-based

### 5. **ORCHESTRATOR** (NEW - Central Coordinator)
- **Responsibility**: 
  - Workflow management and sequencing
  - Data flow coordination
  - Conditional synthesis triggering
  - Cycle state maintenance
- **Key Decisions**:
  - Only trigger synthesis if novelty threshold met
  - Manage computational resources
  - Handle errors gracefully

**Workflow Stages**:
1. **COLLECTING** → Call Collector
2. **FILTERING** → Call Filter Agent (stateless)
3. **ANALYZING** → Call Analysis Agent
4. **SYNTHESIZING** (conditional) → Call Synthesizer if items >= min_threshold
5. **COMPLETE** → Return results

---

## Key Design Principles

### 1. **Clear Separation of Concerns**
Each agent has ONE responsibility:
- Collector: Data acquisition
- Filter: Relevance scoring
- Analysis: Novelty + categorization
- Synthesizer: Output generation
- Orchestrator: Coordination

No overlapping responsibilities = no confusion about who does what.

### 2. **Stateless Filtering**
The Filter Agent has **NO memory**:
- Each scoring pass is independent
- Same input always produces same output
- Removes ambiguity and improves testability
- Purely functional computation

### 3. **Realistic Scope**
- NO long-term trend prediction
- NO autonomous decision making
- NO out-of-scope AI claims
- Academically defensible and implementable

### 4. **Conditional Execution**
Synthesis is NOT automatic:
```python
if len(novel_items) >= min_novel_items_for_synthesis:
    synthesizer.synthesize(...)
else:
    logger.info("Synthesis skipped - insufficient novel items")
```

This prevents wasteful processing and allows workflow optimization.

---

## Workflow Example

```
CYCLE START
    |
    v
COLLECT: 100 raw items from RSS feeds
    |
    v
FILTER: Score against topics (threshold=0.5)
    --> 45 items pass relevance threshold
    |
    v
ANALYZE: Check novelty vs previous period
    --> 12 items identified as novel
    |
    v
SYNTHESIZE? Check: 12 >= 1 required
    --> YES - Generate synthesis
    |
    v
CYCLE COMPLETE
    --> Report: 100 collected, 45 filtered, 12 novel, 1 synthesis generated
```

---

## Code Structure

```
watcher/agents/
├── orchestrator.py      # NEW - Central coordinator
├── collector.py         # REFACTORED - Data acquisition only
├── filter_agent.py      # NEW - Stateless semantic filtering
├── analysis.py          # REFACTORED - Novelty + categorization
├── synthesizer.py       # UNCHANGED - Output generation
└── llm_adapter.py       # UNCHANGED - LLM access

watcher/
├── storage/
│   ├── store.py         # SQLite persistence
│   └── vector_store.py  # ChromaDB wrapper
├── nlp/
│   └── embeddings.py    # Sentence transformers
└── collectors/
    ├── rss.py
    └── api.py
```

---

## Running the Orchestrated System

```powershell
# Demo the orchestrated workflow
.\venv\Scripts\python.exe demo_orchestrated_system.py

# Or use individual agents
.\venv\Scripts\python.exe demo_agents.py
```

---

## Files Created/Modified

| File | Status | Notes |
|------|--------|-------|
| `watcher/agents/orchestrator.py` | NEW | Central coordinator |
| `watcher/agents/collector.py` | NEW | Simplified collector |
| `watcher/agents/filter_agent.py` | NEW | Stateless filter |
| `watcher/agents/analysis.py` | NEW | Refactored analysis |
| `demo_orchestrated_system.py` | NEW | Demo with orchestration |
| `AGENTS_GUIDE.md` | NEW | Complete documentation |

---

## Academic Defensibility

This architecture is realistic and defensible because:

✓ **Clear scope boundaries** - No overstated AI claims
✓ **Stateless operations** - Filter is purely functional
✓ **Limited novelty** - Only vs. previous period, not long-term
✓ **No prediction** - Only categorization and filtering
✓ **Explainable** - All decisions based on embeddings or keywords
✓ **Measurable** - Each stage output can be quantified
✓ **Realistic** - No autonomous decision-making or complex reasoning

---

## Comparison: Pipeline vs. Agentic System

### Before (Pipeline)
```
Input → [Process 1] → [Process 2] → [Process 3] → Output
  (Sequential, no coordination, no decision gates)
```

### After (Agentic System)
```
ORCHESTRATOR
    ├─ [Collector] ──data──→
    ├─ [Filter] ────scores──→
    ├─ [Analysis] ─results──→
    └─ [Synthesizer] ────conditional
  (Coordinated, decision gates, state management)
```

---

## Next Steps

1. **Integration Testing**: Verify agents work together via Orchestrator
2. **Performance Tuning**: Optimize embedding caching and filtering
3. **Advanced Features** (Future): Multi-topic analysis, advanced categorization
4. **UI Enhancement**: Dashboard showing each agent's output
5. **Academic Documentation**: Thesis-ready architecture explanation

---

## Questions or Customization?

See `AGENTS_GUIDE.md` for detailed examples and customization options.

