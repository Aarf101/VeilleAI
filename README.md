Veille Automatisée — Prototype (OSS-only)
======================================

Ce prototype utilise uniquement des composants open-source pour les embeddings,
le stockage vectoriel et la génération locale de texte.

Principaux composants:
- Embeddings: `sentence-transformers` (local)
- Vector store: `chromadb` (local) with in-memory fallback
- LLM: local `transformers` pipeline (model configurable)
- Collecte: `feedparser`, `requests`
- Stockage: `SQLite`
- Scheduler: `APScheduler`

Installation minimale:
```bash
pip install -r requirements.txt
```

Notes sur modèles locaux:
- `sentence-transformers` téléchargera automatiquement le modèle `all-MiniLM-L6-v2` la première fois.
- Pour la génération locale, choisissez un modèle HF compatible (ex: `gpt2` pour test, modèles plus grands pour qualité). Installer `transformers` et (optionnel) `accelerate` et `torch`.

Exemples d'exécution:
- Collect once:
  ```bash
  python3 demo/run_collectors.py
  ```
- Start scheduler (initial collect + periodic runs):
  ```bash
  python3 demo/run_scheduler.py
  ```

Fichiers importants:
- `watcher/collectors/*` : collecteurs RSS/API
- `watcher/storage/store.py` : stockage SQLite
- `watcher/storage/vector_store.py` : wrapper ChromaDB (ou fallback)
- `watcher/nlp/embeddings.py` : embeddings locales (sentence-transformers)
- `watcher/agents/filter.py` : scoring et filtrage par similarité
- `watcher/agents/novelty_detector.py` : détection de nouveauté
- `watcher/agents/llm_adapter.py` + `watcher/agents/synthesizer.py` : génération locale

Matériel recommandé:
- Pour inference LLM de qualité, GPU recommandé. CPU quantized setups (llama-cpp) possible but out of scope for this MVP.

Voir `config.yaml` pour ajuster sources et paramètres.
