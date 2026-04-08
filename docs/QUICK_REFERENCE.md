# QUICK REFERENCE - Commands & Files

## 🎬 Run Commands (Copy-Paste Ready)

### Demo 1: Basic Orchestration (30 sec)
```powershell
.\venv\Scripts\python.exe QUICK_DEMO.py
```
Shows: 5 articles → 2 filtered → 2 novel → 1 synthesis

### Demo 2: Advanced Scenarios (1 min)
```powershell
.\venv\Scripts\python.exe DEMO_ADVANCED.py
```
Shows: 3 scenarios with conditional logic

### Demo 3: Real Data (30 sec)
```powershell
.\venv\Scripts\python.exe DEMO_WITH_REAL_DATA.py
```
Shows: Real articles from watcher.db being processed

### Real System (Full Integration)
```powershell
python demo_orchestrated_system.py
```
Uses: Real embeddings, ChromaDB, Flan-T5 LLM

### Web UI (Streamlit)
```powershell
streamlit run streamlit_app.py
```
Shows: Interactive dashboard

---

## 📖 Documentation Files

### Quick Start (Read First)
- **START_HERE.md** - Overview & 30-sec quick start
- **COMPLETE_OVERVIEW.md** - Full system overview

### Detailed Guides (Read After Running)
- **README_RUNNABLE_AGENTS.md** - Full guide with examples
- **VSCODE_STEP_BY_STEP.md** - Step-by-step walkthrough
- **SEEING_AGENTS_IN_ACTION.md** - Deep explanations
- **ARCHITECTURE_REFACTOR.md** - System design document

### Summary
- **DELIVERY_SUMMARY.md** - What was delivered

---

## 📁 File Structure

```
AgenticNotes-aarf102/
├── START_HERE.md                    ← Read this first!
│
├── QUICK_DEMO.py                    ← Run this first (30 sec)
├── DEMO_ADVANCED.py                 ← Run this second (1 min)
├── DEMO_WITH_REAL_DATA.py          ← Run this third (30 sec)
│
├── COMPLETE_OVERVIEW.md             ← Quick overview
├── README_RUNNABLE_AGENTS.md        ← Full guide
├── VSCODE_STEP_BY_STEP.md          ← Detailed steps
├── SEEING_AGENTS_IN_ACTION.md      ← Deep dive
├── ARCHITECTURE_REFACTOR.md        ← Design doc
├── DELIVERY_SUMMARY.md             ← What you got
│
└── watcher/agents/
    ├── orchestrator.py              ✨ NEW - Central coordinator
    ├── collector.py                 ✨ NEW - Data gathering
    ├── filter_agent.py              ✨ NEW - Stateless filtering
    └── analysis.py                  ✨ REFACTORED - Novelty detection
```

---

## ⚡ 60-Second Start

1. Open terminal (Ctrl+`)
2. Run: `.\venv\Scripts\python.exe QUICK_DEMO.py`
3. See agents working
4. Read: `START_HERE.md`

---

## 🎓 Learning Path

### Path 1: Impatient (5 min)
1. Run QUICK_DEMO.py
2. That's it!

### Path 2: Curious (15 min)
1. Run QUICK_DEMO.py
2. Run DEMO_ADVANCED.py
3. Run DEMO_WITH_REAL_DATA.py

### Path 3: Thorough (1 hour)
1. Run all 3 demos
2. Read START_HERE.md
3. Read COMPLETE_OVERVIEW.md
4. Read VSCODE_STEP_BY_STEP.md
5. Read SEEING_AGENTS_IN_ACTION.md

### Path 4: Deep Dive (2+ hours)
1. Do Path 3
2. Read ARCHITECTURE_REFACTOR.md
3. Read agent code
4. Run real system
5. Launch UI

---

## 🔍 What Each File Does

### QUICK_DEMO.py
- One complete cycle
- 4 agents working
- Clear output
- 30 seconds

### DEMO_ADVANCED.py
- 3 scenarios
- Decision logic
- Conditional execution
- 1 minute

### DEMO_WITH_REAL_DATA.py
- Real database
- Real articles
- Real processing
- 30 seconds

### START_HERE.md
- Quick overview
- Reading order
- 30-sec quick start

### COMPLETE_OVERVIEW.md
- Full summary
- Architecture explained
- Example outputs

### README_RUNNABLE_AGENTS.md
- Comprehensive guide
- What each agent does
- How to customize

### VSCODE_STEP_BY_STEP.md
- Line-by-line explanation
- Visual diagrams
- Detailed walkthrough
- Troubleshooting

### SEEING_AGENTS_IN_ACTION.md
- Agent responsibilities
- Workflow examples
- Design principles

### ARCHITECTURE_REFACTOR.md
- System design
- Academic defense
- Before/after comparison

### DELIVERY_SUMMARY.md
- What was delivered
- Files created
- Verification checklist

---

## 🚀 Key Concepts

### Orchestration
```
ORCHESTRATOR (Central Coordinator)
  ├─ Controls order
  ├─ Manages flow
  ├─ Makes decisions
  └─ Reports state
```

### Pipeline vs Agentic
```
Pipeline:  Input → [A] → [B] → [C] → Output
           (linear, no decisions)

Agentic:   ORCHESTRATOR
           (decides, coordinates, optimizes)
```

### Stateless Filter
```
Same input → Same output (always)
Predictable, testable, fast
```

### Conditional Synthesis
```
if novel_items >= minimum:
    synthesize()  YES
else:
    skip()        NO (efficient)
```

---

## 📊 By The Numbers

| Metric | Count |
|--------|-------|
| Runnable Demos | 3 |
| Documentation Files | 7 |
| New Agent Files | 3 |
| Refactored Agent Files | 1 |
| Total Lines of Demo Code | ~800 |
| Total Lines of Documentation | ~2,000 |
| Total Size | ~77 KB |
| Runtime (All Demos) | ~2 minutes |

---

## ✅ Verification

After running demos, you should see:

✅ Agents executing in order
✅ Data flowing through stages
✅ Filtering removing items
✅ Analysis categorizing items
✅ Synthesis decision made
✅ Final report displayed
✅ No errors

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No module named watcher" | Check directory: `cd C:\Users\user\Downloads\AgenticNotes-aarf102\AgenticNotes-aarf102` |
| "No such table: items" | Collect articles: `python demo/run_collectors.py` |
| Python not found | Activate venv: `.\venv\Scripts\Activate.ps1` |
| Can't see output | Make terminal bigger |
| Too much output | Redirect: `... > output.txt` |

---

## 🎯 Next Steps

- [ ] Run QUICK_DEMO.py
- [ ] Run DEMO_ADVANCED.py
- [ ] Run DEMO_WITH_REAL_DATA.py
- [ ] Read START_HERE.md
- [ ] Read COMPLETE_OVERVIEW.md
- [ ] Explore documentation
- [ ] Run real system
- [ ] Launch UI
- [ ] Customize agents

---

## 📝 Notes

- All demos tested and working
- No external API calls required
- No paid services needed
- Uses only installed packages
- Runs on Windows PowerShell
- Complete documentation provided

---

## 🎬 Start Now

```powershell
cd C:\Users\user\Downloads\AgenticNotes-aarf102\AgenticNotes-aarf102
.\venv\Scripts\python.exe QUICK_DEMO.py
```

**See agents working in 30 seconds!**

