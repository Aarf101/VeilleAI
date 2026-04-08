# 🤖 AgenticNotes - Agent System Guide

## Quick View of Each Agent

Run the complete demo:
```powershell
.\venv\Scripts\python.exe demo_agents.py
```

---

## 🎯 Agent Pipeline Overview

```
📰 Collected Articles → 🔍 Filter Agent → 🆕 Novelty Detector → ✍️ Synthesizer
```

---

## 1️⃣ **FILTER AGENT** - Topic Relevance Scoring

**Purpose:** Score each article against configured topics using semantic similarity.

**What it does:**
- Embeds article text (content → summary → title)
- Embeds configured topics
- Computes cosine similarity between article and each topic
- Returns max similarity score (0-1)
- Filters articles by threshold (default: 0.5)

**How to use:**
```python
from watcher.agents.filter import filter_items
from watcher.nlp.embeddings import EmbeddingProvider

articles = [...]  # list of dicts with 'title', 'content', 'summary'
topics = ["artificial intelligence", "machine learning"]

results = filter_items(articles, topics, threshold=0.65)
# Returns: [(item, score, passed), ...]
```

**Output from demo:**
```
✅ Passed threshold (0.5): 0/10
✗ FAIL | Score: 0.17 | The first signs of burnout...
✗ FAIL | Score: 0.26 | Databricks CEO says SaaS...
✗ FAIL | Score: 0.21 | Anthropic's India expansion...
```

**Configuration:**
- Edit `config.yaml` `topics:` section
- Adjust `threshold` parameter (0.5-0.9 typical)

---

## 2️⃣ **NOVELTY DETECTOR** - Duplicate/Similar Content Detection

**Purpose:** Identify new/unique articles vs. similar ones already in database.

**What it does:**
- Embeds candidate article
- Compares against recent stored items (~200 lookback)
- Computes max similarity score
- Flags as novel if max_sim < threshold (default: 0.75)
- Also categorizes article (announcement, event, trend, analysis, regulation, other)

**How to use:**
```python
from watcher.agents.novelty_detector import is_novel, categorize_item
from watcher.storage.store import Storage

article = {...}  # dict with content/title/summary
store = Storage()
provider = EmbeddingProvider()

is_novel_flag, max_similarity = is_novel(article, store, provider, sim_threshold=0.75)
category = categorize_item(article)
```

**Output from demo:**
```
[1] 🔁 SIMILAR | Similarity: 1.00 | Category: autre
     Title: The first signs of burnout are coming...
[2] 🔁 SIMILAR | Similarity: 1.00 | Category: tendance
     Title: Databricks CEO says SaaS...
```

**Categories available:**
- `annonce` - Announcements
- `événement` - Events/conferences
- `tendance` - Trends
- `analyse` - Analysis/reports
- `régulation` - Laws/regulations
- `autre` - Other

---

## 3️⃣ **SYNTHESIZER** - Structured Note Generation

**Purpose:** Create executive summaries and structured notes from articles.

**Two modes:**

### Mode A: Template (Fast, Instant)
```python
from watcher.agents.synthesizer import Synthesizer

synthesizer = Synthesizer(use_llm=False)  # Template mode
note = synthesizer.synthesize(
    topic="AI & Technology",
    period="Daily Brief",
    context="Latest news on artificial intelligence",
    items=articles[:3],
    max_new_tokens=512
)
```

Output:
```
# RÉSUMÉ EXÉCUTIF
Analyse de 3 articles sur la période spécifiée. 
Points clés: The first signs of burnout..., Databricks CEO says...

# CONTEXTE
Sujet: AI & Technology
Période: Daily Brief
Nombre d'articles analysés: 3

# NOUVEAUTÉS PRINCIPALES
• The first signs of burnout from AI adoption
• SaaS industry transformation...
```

### Mode B: LLM (Sophisticated, Slower)
```python
synthesizer = Synthesizer(use_llm=True, model_name='google/flan-t5-base')
note = synthesizer.synthesize(...)  # Uses transformer model
```

**Configuration:**
- Set `use_llm: true/false` in code or config
- Edit `config.yaml`:
  ```yaml
  synthesizer_model: google/flan-t5-base
  synthesizer_task: text2text-generation
  synthesizer_max_new_tokens: 512
  ```

---

## 4️⃣ **LLM ADAPTER** - Text Generation

**Purpose:** General-purpose text generation using local models.

**What it does:**
- Loads HuggingFace transformer model
- Generates text from prompts
- Supports custom tasks (summarization, translation, etc.)

**How to use:**
```python
from watcher.agents.llm_adapter import LocalLLMAdapter

adapter = LocalLLMAdapter(
    model_name='google/flan-t5-small',
    task='text2text-generation'
)

result = adapter.generate(
    "Summarize: Recent AI advances include language models and autonomous systems",
    max_new_tokens=100
)
print(result)  # → Generated text
```

---

## 📊 Complete Agent Pipeline Example

```python
from watcher.agents.filter import filter_items
from watcher.agents.novelty_detector import is_novel, categorize_item
from watcher.agents.synthesizer import Synthesizer
from watcher.storage.store import Storage
from watcher.nlp.embeddings import EmbeddingProvider
import sqlite3

# 1. Get articles
conn = sqlite3.connect('watcher.db')
c = conn.cursor()
c.execute("SELECT * FROM items LIMIT 10")
articles = [dict(row) for row in c.fetchall()]
conn.close()

# 2. Filter by topic
provider = EmbeddingProvider()
topics = ["artificial intelligence", "machine learning"]
filtered = filter_items(articles, topics, threshold=0.65, provider=provider)
passed_items = [item for item, score, passed in filtered if passed]

# 3. Check novelty
store = Storage()
novel_items = []
for item in passed_items:
    is_novel_flag, sim = is_novel(item, store, provider)
    if is_novel_flag:
        novel_items.append(item)
        print(f"🆕 Novel: {item['title']}")

# 4. Synthesize
if novel_items:
    synthesizer = Synthesizer(use_llm=False)
    note = synthesizer.synthesize(
        topic="AI News",
        period="Today",
        context="Daily AI briefing",
        items=novel_items[:5]
    )
    print(note)
```

---

## 🚀 Running the Full Workflow

```powershell
# 1. Collect articles (one-time)
.\venv\Scripts\python.exe demo/run_collectors.py

# 2. See all agents working
.\venv\Scripts\python.exe demo_agents.py

# 3. Run scheduler for continuous collection (background)
.\venv\Scripts\python.exe demo/run_scheduler.py

# 4. Start web UI
.\venv\Scripts\streamlit run streamlit_app.py
```

---

## 📈 Performance Notes

| Agent | Speed | Memory | Notes |
|-------|-------|--------|-------|
| Filter | Fast | ~500MB | Embeddings cached per topic |
| Novelty | Fast | ~500MB | Embeddings on-the-fly |
| Synthesizer (Template) | Very Fast | ~300MB | Instant output |
| Synthesizer (LLM) | Slow | ~2GB+ | ~10-30 sec per note |
| LLM Adapter | Slow | ~2GB+ | Model loading overhead |

---

## 🔧 Customization

### Change Topics
Edit `config.yaml`:
```yaml
topics:
  - "artificial intelligence"
  - "machine learning"
  - "your custom topic here"
```

### Change Filter Threshold
```python
filter_items(articles, topics, threshold=0.75)  # 0.5-0.9 typical
```

### Change Novelty Threshold
```python
is_novel(item, store, provider, sim_threshold=0.8)  # 0.7-0.9 typical
```

### Change Synthesizer Model
```yaml
# config.yaml
synthesizer_model: google/flan-t5-large  # or gpt2, mistral-7b, etc.
synthesizer_max_new_tokens: 1024
```

---

## ✅ Verification Commands

```powershell
# Check database
.\venv\Scripts\python.exe verify_project.py

# Run agent demo
.\venv\Scripts\python.exe demo_agents.py

# Quick count
.\venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('watcher.db'); print('Articles:', conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]); conn.close()"
```

---

## 📝 Architecture

```
watcher/
├── agents/
│   ├── filter.py           ← Topic filtering & scoring
│   ├── novelty_detector.py ← Duplicate detection & categorization
│   ├── synthesizer.py      ← Note generation (template & LLM modes)
│   └── llm_adapter.py      ← Local model text generation
├── nlp/
│   └── embeddings.py       ← Sentence transformers (all-MiniLM-L6-v2)
├── storage/
│   ├── store.py            ← SQLite database
│   └── vector_store.py     ← ChromaDB wrapper
└── collectors/
    ├── rss.py              ← RSS feed collection
    └── api.py              ← API collection
```

---

## 🆘 Troubleshooting

**Q: Why is similarity always 1.00 in novelty detector?**
- A: Items are being compared to themselves. This is normal on first run.

**Q: Why do topics get low scores?**
- A: Adjust threshold lower (0.3-0.5) or use more specific topic keywords.

**Q: Synthesizer is slow?**
- A: Use template mode (`use_llm=False`) for instant output.

**Q: Out of memory errors?**
- A: Reduce batch size or use smaller model (flan-t5-small instead of base/large).

---

## 📚 More Info

See individual files in `watcher/agents/` for detailed docstrings and function signatures.

Happy analyzing! 🚀
