# Agent Collecteur – Implémentation

## Vue d'ensemble

L'Agent Collecteur est responsable de :

1. **Collecter** les données brutes depuis les flux RSS et APIs configurés
2. **Extraire** les champs structurés (titre, URL, date, source, résumé, contenu)
3. **Dédupliquer** par URL et par titre (vérification locale en DB)
4. **Persister** uniquement les nouveaux éléments via Storage

## Fichiers modifiés

### `watcher/agents/collector.py`

- **Classe** `CollectorAgent`
- **Méthode clé** :
  - `collect_new()` : collecte RSS + APIs, déduplique, retourne les nouveaux items

**Comportement** :
- Charge la config depuis `config.yaml` (flux RSS et APIs)
- Récupère les items avec `fetch_rss()` et `fetch_json_api()`
- Normalise les clés de chaque entry pour uniformité
- Vérifie les doublons par URL via `Storage.save_item()`
- Vérifie les doublons par titre via `Storage.title_exists()`
- Retourne uniquement les items nouvellement insérés

### `watcher/storage/store.py`

- **Méthode ajoutée** : `title_exists(title: str) -> bool`
- Vérifie rapidement si un titre identique existe déjà en DB (requête SQL simple)
- Utilisée par le collecteur avant d'appeler `save_item()`

## Configuration

Dans `config.yaml` :

```yaml
feeds:
  - https://news.ycombinator.com/rss
  
apis:
  - url: https://api.example.com/items
    items_path: data.items
    
max_items_per_feed: 10
```

## Flux de données

```
RSS/APIs → fetch_rss() / fetch_json_api()
     ↓
normalize fields (title, link, published, summary, content, source)
     ↓
check by URL (Storage.save_item)
     ↓
check by title (Storage.title_exists)
     ↓
persist (Storage.save_item returns {duplicate: bool})
     ↓
return new_items list
```

## Testing

Un test unitaire valide le comportement de déduplication :

```bash
cd AgenticNotes-aarf102am
py -m pytest tests/test_collector.py -v
```

**Test** : `test_collector_inserts_only_unique_items`
- Mock des flux RSS et API
- Vérifie que les doublons par titre sont skippés
- Vérifie que 3 items uniques sont insérés en DB

**Résultat** : PASSED ✓

## Exécution

Pour tester localement :

```bash
cd AgenticNotes-aarf102am
py demo/run_collectors.py
```

**Dernière exécution** (2026-02-10) :
- Flux RSS collecté : Hacker News
- Résultat : 10 nouveaux items insérés

## Prochaines étapes

1. Intégrer l'output de `collect_new()` au **Filter Agent** pour le filtrage intelligent
2. Connecter le Filter Agent au **Synthesizer Agent** pour agrégation/résumé
3. Mettre en place un scheduler (APScheduler) pour collecte périodique

## Notes

- Le collecteur est **passif** — il ne fait aucune analyse ni décision
- Tous les champs bruts sont transmis aux agents suivants pour traitement
- Les doublons évitent l'insertion en DB et ne sont pas retournés
- Aucune dépendance heavy ML/embeddings dans le collecteur lui-même (ChromaDB optionnel)
