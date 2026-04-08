# SEEING THE AGENTS IN ACTION

## Quick Start

Run either demo from VS Code terminal (Ctrl+`):

```powershell
# Demo 1: Basic orchestration (5 min read)
.\venv\Scripts\python.exe QUICK_DEMO.py

# Demo 2: Advanced scenarios (10 min read)
.\venv\Scripts\python.exe DEMO_ADVANCED.py
```

---

## What You're Seeing

### DEMO 1: QUICK_DEMO.py

This shows **one complete processing cycle** through all 4 agents:

```
[STAGE 1] COLLECTION
  > Collecting 5 articles from RSS feeds...
  OK> Collected 5 items
```
**What's happening:** Collector Agent gathers raw data. In real project, this fetches from RSS feeds. Here it creates 5 mock articles.

```
[STAGE 2] FILTERING
  > Filtering 5 items against 4 topics...
    Topics: AI, Machine Learning, Cloud Computing, Security
    - Article  1: FAIL (score=0.50)
    + Article  2: PASS (score=0.70)
    - Article  3: FAIL (score=0.50)
    + Article  4: PASS (score=0.70)
    - Article  5: FAIL (score=0.50)
  OK> 2 items passed threshold
```
**What's happening:** Filter Agent scores each item's relevance to topics. Uses embeddings (in real project). Threshold=0.65, so only items with score >= 0.65 pass. Result: 5 items → 2 items.

```
[STAGE 3] ANALYSIS
  > Analyzing 2 items for novelty...
    + Article  2: NOVEL - Category: announcement
    + Article  4: NOVEL - Category: trend
  OK> 2 items identified as novel
```
**What's happening:** Analysis Agent checks if these 2 items are novel (not seen before). Assigns categories: announcement, trend, analysis, event, etc. Result: 2 items analyzed → 2 items marked novel.

```
[STAGE 4] SYNTHESIS
  > Condition met: 2 items >= 1 required
  > Generating synthesis from 2 items...
  OK> Synthesis generated (383 chars)
```
**What's happening:** Synthesizer creates a summary. **Conditional decision**: Only runs if `len(novel_items) >= min_novel_for_synthesis`. Here 2 >= 1, so it runs.

```
Summary:
  - Collected: 5 items
  - Filtered:  2 items passed threshold
  - Novel:     2 items identified as novel
  - Synthesis: Generated
```
**This is the Orchestrator reporting** on the entire cycle.

---

### DEMO 2: DEMO_ADVANCED.py

Shows **3 different scenarios** to demonstrate Orchestrator decision-making:

#### Scenario 1: Synthesis Triggered
- Collected: 5
- Filtered: 3 (60% pass rate)
- Novel: 3 (all filtered items are novel)
- **Synthesis: RAN** ✓
- **Decision:** 3 items >= 1 minimum required → Execute synthesis

#### Scenario 2: Synthesis Skipped ⚠️
- Collected: 5
- Filtered: 0 (0% pass rate - all items rejected)
- Novel: 0
- **Synthesis: SKIPPED** ✗
- **Decision:** 0 items < 2 minimum required → Skip synthesis (saves resources)

#### Scenario 3: Heavy Filtering
- Collected: 10
- Filtered: 2 (20% pass rate - heavy filtering)
- Novel: 2
- **Synthesis: RAN** ✓
- **Decision:** 2 items >= 1 minimum required → Execute synthesis

---

## The Key Insight: Orchestration vs. Pipeline

### Old Way (Pipeline)
```
Input → [Collect] → [Filter] → [Analyze] → [Synthesize] → Output
        (Automatic, no decisions, no coordination)
```
Everything flows through. Synthesis always runs, even with 0 items.

### New Way (Agentic System)
```
                    ORCHESTRATOR
                   (Makes Decisions)
                         |
    _____ Coordinates flow between stages _____
    |         |          |         |          |
[Collect] [Filter]  [Analyze] [Synthesize] [Report]
    |         |          |         |          |
    Decision: "Should I run synthesis?"
              → Check: len(novel_items) >= min_required
              → If NO: Skip synthesis (efficient!)
              → If YES: Run synthesis (process output)
```

---

## Key Agents Explained

### 1. COLLECTOR AGENT
- **Job:** Gather raw articles from RSS feeds
- **Input:** None (reads from config)
- **Output:** List of articles with metadata
- **Decision:** None (just collects)

### 2. FILTER AGENT ⭐ STATELESS
- **Job:** Score each article's relevance to topics
- **Input:** (articles, topics, threshold)
- **Output:** Articles that pass relevance threshold
- **Decision:** Yes/No for each item based on score
- **Key Feature:** STATELESS = Same input always gives same output

### 3. ANALYSIS AGENT
- **Job:** Detect if articles are novel (new)
- **Input:** Filtered articles
- **Output:** Novel articles + categories
- **Decision:** Is this article new? Assign category

### 4. SYNTHESIZER
- **Job:** Create summary/report from novel articles
- **Input:** Novel articles
- **Output:** Structured synthesis text
- **Decision:** None (just generates)

### 5. ORCHESTRATOR ⭐ NEW - Central Controller
- **Job:** Coordinate all other agents
- **Input:** Configuration (topics, thresholds, min_items)
- **Output:** Processing cycle results
- **Decisions:**
  - What order to run agents?
  - Should I skip synthesis? (efficiency)
  - Report current status?

---

## Orchestrator Decision Logic

The Orchestrator makes ONE key decision:

```python
if len(novel_items) >= min_novel_for_synthesis:
    # SYNTHESIS RUNS
    synthesis = synthesizer.synthesize(novel_items)
else:
    # SYNTHESIS SKIPPED
    synthesis = None
    logger.info("Skipping synthesis - not enough novel items")
```

This is **agentic behavior**: Not just executing steps, but making intelligent decisions based on state.

---

## How to Customize

### Change the threshold
In QUICK_DEMO.py:
```python
results = orchestrator.run(
    filter_threshold=0.50,  # Lower = more items pass
    min_novel_for_synthesis=2  # Higher = synthesis runs less often
)
```

### Change number of items
In DEMO_ADVANCED.py:
```python
orchestrator.run(num_items=20, pass_rate=0.3, min_novel=1)
```
- `num_items`: How many articles to collect
- `pass_rate`: What fraction pass filtering (0.0 = none, 1.0 = all)
- `min_novel`: Minimum novel items before synthesis runs

---

## Real Project Integration

These demos use **mock agents**. The real project in `watcher/agents/` has:

- **Real Collector:** Fetches from RSS feeds (feedparser)
- **Real Filter:** Uses sentence-transformers embeddings (384-dim)
- **Real Analysis:** Compares against ChromaDB vector store
- **Real Synthesizer:** Uses Flan-T5 LLM (configurable)
- **Real Orchestrator:** Coordinates all above with state management

To run the real system:
```powershell
.\venv\Scripts\python.exe demo_orchestrated_system.py
```

---

## Summary

You're now seeing:

✅ **Orchestration** - Central coordinator making decisions
✅ **Conditional execution** - Synthesis only when needed
✅ **State tracking** - Items flowing through pipeline
✅ **Multi-agent coordination** - Not just a pipeline
✅ **Agentic behavior** - Making decisions, not just executing

This is a **true multi-agent system**, not a simple pipeline.

