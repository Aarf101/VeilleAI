# RUNNABLE AGENTS - SEE THEM WORKING

## TL;DR - Run These Now

Open VS Code terminal (Ctrl+`) and run:

```powershell
# 1. Basic demo (2 minutes)
.\venv\Scripts\python.exe QUICK_DEMO.py

# 2. Advanced scenarios (3 minutes)
.\venv\Scripts\python.exe DEMO_ADVANCED.py

# 3. Real data from your database (2 minutes)
.\venv\Scripts\python.exe DEMO_WITH_REAL_DATA.py
```

**Each shows the agents working orchestrated.**

---

## What You're Running

### QUICK_DEMO.py
Shows **one complete cycle** through all 4 agents:

```
COLLECTOR (gathers 5 articles)
   ↓ 
FILTER (scores them, 2 pass threshold)
   ↓
ANALYSIS (checks novelty, 2 novel)
   ↓
SYNTHESIZER (generates summary)
   ↓
ORCHESTRATOR (reports final state)
```

**Output:** Clean, easy to follow, shows data flowing through pipeline

### DEMO_ADVANCED.py
Shows **3 scenarios** with different outcomes:

1. **Scenario 1:** Synthesis triggers (enough items) ✅
2. **Scenario 2:** Synthesis skipped (0 items, threshold not met) ⚠️
3. **Scenario 3:** Heavy filtering (only 2 items pass) ✅

**Output:** Demonstrates Orchestrator making conditional decisions

### DEMO_WITH_REAL_DATA.py
Shows **real data** from your watcher.db:

- Loads 10 actual articles you collected
- Shows real article titles and sources
- Filters them using real topics
- Analyzes for novelty
- Makes synthesis decision

**Output:** Proof the system works with YOUR DATA

---

## What Each Agent Does

```
┌─────────────────────────────────────────────────────┐
│          ORCHESTRATOR AGENT                         │
│     (Controls everything, makes decisions)          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Stage 1: COLLECTOR                                │
│  └─> Gathers raw articles from RSS feeds           │
│  └─> Input: RSS feed URLs (from config)            │
│  └─> Output: List of articles                      │
│                                                     │
│  Stage 2: FILTER AGENT (STATELESS)                 │
│  └─> Scores each article against topics            │
│  └─> Input: (articles, topics, threshold)          │
│  └─> Output: Articles passing threshold            │
│  └─> Example: Article1=0.7 PASS, Article2=0.3 FAIL │
│                                                     │
│  Stage 3: ANALYSIS AGENT                           │
│  └─> Checks if articles are novel (new)            │
│  └─> Assigns categories: announcement/trend/etc    │
│  └─> Input: Filtered articles                      │
│  └─> Output: Novel articles + categories           │
│                                                     │
│  Stage 4: SYNTHESIZER                              │
│  └─> Generates summary report                      │
│  └─> Input: Novel articles                         │
│  └─> Output: Structured synthesis text             │
│                                                     │
│  DECISION: Run synthesis only if >= min_items      │
│  └─> If 5 novel items, synthesize ✓               │
│  └─> If 0 novel items, skip synthesis ✗            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Architecture Comparison

### Before (Simple Pipeline)
```
Input → [Process1] → [Process2] → [Process3] → Output
        (everything flows through automatically)
```
- Linear
- No decisions
- Can't skip steps

### After (Multi-Agent Orchestration)
```
              ORCHESTRATOR
            (Makes decisions)
                   |
    [Decision gates at each stage]
                   |
         [Skip synthesis if <threshold]
                   |
         [Report on entire cycle]
```
- Coordinated
- Makes decisions
- Conditional execution
- True agentic behavior

---

## Key Concept: STATELESS FILTER

The Filter Agent is **stateless** = PURE FUNCTION:

```
filter(article, topics, threshold=0.65) → score [0, 1]
```

- Same input → Same output (always)
- No memory, no state
- Super testable
- Easy to parallelize

Example:
```
Input:  article="ChatGPT news", topics=["AI", "ML"]
Output: 0.78 (PASS, above 0.65 threshold)

Input:  article="Sports news", topics=["AI", "ML"]
Output: 0.15 (FAIL, below 0.65 threshold)
```

---

## Workflow Walkthrough (From QUICK_DEMO.py Output)

```
[STAGE 1] COLLECTION
  > Collecting 5 articles from RSS feeds...
  OK> Collected 5 items
```
Collector Agent gathered 5 articles.

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
Filter Agent scored each item. Only 2 passed (score >= 0.65).

```
[STAGE 3] ANALYSIS
  > Analyzing 2 items for novelty...
    + Article  2: NOVEL - Category: announcement
    + Article  4: NOVEL - Category: trend
  OK> 2 items identified as novel
```
Analysis Agent checked novelty. Both are novel. Assigned categories.

```
[STAGE 4] SYNTHESIS
  > Condition met: 2 items >= 1 required
  > Generating synthesis from 2 items...
  OK> Synthesis generated (383 chars)
```
Orchestrator decided: 2 >= 1 required → RUN synthesis.

```
Summary:
  - Collected: 5 items
  - Filtered:  2 items passed threshold
  - Novel:     2 items identified as novel
  - Synthesis: Generated
```
Final report from Orchestrator.

---

## Files Created for Running

| File | What it shows | Run time |
|------|--------------|----------|
| `QUICK_DEMO.py` | Basic orchestrated cycle | ~30 sec |
| `DEMO_ADVANCED.py` | 3 scenarios with decisions | ~1 min |
| `DEMO_WITH_REAL_DATA.py` | Real articles from your DB | ~30 sec |
| `SEEING_AGENTS_IN_ACTION.md` | Detailed explanation | Read |

---

## Real System Integration

The demos use **mock agents** for clarity.

The **real system** (in `watcher/agents/`) has:

```
orchestrator.py ──────────────────────────────────────
                       Central coordinator
    
    ├─ collector.py
    │  └─ Fetches real RSS feeds
    │
    ├─ filter_agent.py
    │  └─ Uses sentence-transformers (384-dim embeddings)
    │  └─ Scores against real topics
    │
    ├─ analysis.py
    │  └─ Compares against ChromaDB vector store
    │  └─ Real novelty detection
    │
    └─ synthesizer.py
       └─ Uses Flan-T5 LLM (real generation)
```

To run the real system:
```powershell
.\venv\Scripts\python.exe demo_orchestrated_system.py
```

---

## Common Questions

**Q: Why stateless filter?**
A: Stateless = predictable, testable, parallelizable. Same input always gives same score.

**Q: Why skip synthesis?**
A: Save resources. No point generating 500-word summary for 0 new items.

**Q: How is this "agentic"?**
A: Orchestrator makes decisions (not just executing). It has goals (find novel items) and adjusts behavior (skip synthesis if not enough items).

**Q: Can I customize the agents?**
A: Yes! Edit the `pass_rate`, `threshold`, `min_novel`, and `num_items` parameters in the demos.

---

## Next Steps

1. ✅ Run QUICK_DEMO.py
2. ✅ Run DEMO_ADVANCED.py
3. ✅ Run DEMO_WITH_REAL_DATA.py
4. Read SEEING_AGENTS_IN_ACTION.md for deep dive
5. Run the real system: `python demo_orchestrated_system.py`
6. Launch UI: `streamlit run streamlit_app.py`

---

## Troubleshooting

**Error: "No module named watcher"**
→ Make sure you're in the project root: `cd c:\Users\user\Downloads\AgenticNotes-aarf102\AgenticNotes-aarf102`

**Error: "No such table: items"**
→ Run: `.\venv\Scripts\python.exe demo/run_collectors.py` first (collects articles)

**Python not found**
→ Make sure venv is activated: `.\venv\Scripts\Activate.ps1`

---

## Summary

You now have:

✅ 3 working demos showing orchestrated agents
✅ Clear visualization of data flow
✅ Real system integration ready
✅ Comprehensive documentation

**Run them now to see the system in action!**

