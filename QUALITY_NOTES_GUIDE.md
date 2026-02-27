# AMÉLIORATION QUALITÉ DES NOTES - GUIDE DE CONFIGURATION

## 🎯 Objectif : Qualité > Quantité

**Philosophie**: Mieux vaut 3 notes excellentes que 10 notes médiocres.

Le système a été optimisé pour générer des notes de veille technologique de qualité professionnelle, adaptées aux décideurs techniques et business.

---

## 📋 Structure des Notes (Modèle Français Professionnel)

Les notes suivent maintenant une structure en 5 sections inspirée des meilleures pratiques de veille stratégique:

### 1. RÉSUMÉ EXÉCUTIF
- Paragraphe de 4-6 phrases
- Identifie les 2-3 annonces/développements MAJEURS
- Dégage la tendance principale
- Présente l'impact stratégique
- PAS une simple liste de titres

### 2. RAPPEL DU CONTEXTE
- Période précédente: qu'observions-nous?
- Évolution du contexte
- Enjeux actuels
- Focus de cette période
- **Intégration automatique du contexte historique**

### 3. NOUVEAUTÉS DE LA PÉRIODE
Pour chaque développement majeur (3-5 articles maximum):
- Description détaillée
- Contexte technologique
- Données quantitatives (performances, benchmarks)
- Source et date complètes

### 4. ANALYSE ET IMPLICATIONS
**Convergences et tendances émergentes:**
- Patterns entre les articles
- Direction de l'industrie
- Technologies convergentes/concurrentes

**Implications techniques:**
- Nouvelles capacités disponibles
- Changements d'architecture suggérés
- Risques et opportunités techniques

**Implications business:**
- Impact sur compétitivité
- Opportunités de différenciation
- Risques de disruption

**Recommandations d'action:**
- Court terme (0-3 mois)
- Moyen terme (3-12 mois)
- Questions stratégiques à approfondir

### 5. SOURCES ET RÉFÉRENCES
Liste complète avec format professionnel:
- Nom source - "Titre complet" - Date - URL

---

## ⚙️ Paramètres de Qualité Optimisés

### Configuration dans `config.yaml`

```yaml
# FILTRAGE - Augmenté pour plus de sélectivité
filter_threshold: 0.5  # Précédemment 0.2
# → Ne garde que les articles les PLUS pertinents

# COLLECTION - Réduit pour focus qualité
max_items_per_feed: 5  # Précédemment 10
# → Top 5 articles par source uniquement

# LLM - Recommandé pour qualité maximale
use_api_llm: true
api_provider: gemini  # ou groq, ollama
api_model: gemini-2.5-flash  # Modèle hybrid reasoning
```

### Paramètres du Synthesizer

**Articles analysés**: 8 maximum (précédemment 15)
- Focus sur les PLUS importants
- Analyse approfondie de chacun

**Contenu par article**: 2000 caractères (précédemment 1200)
- Permet une analyse plus riche
- LLM a plus de contexte pour insights

**Contexte historique**: Enrichi automatiquement
- Thèmes principaux de la période précédente
- Sources principales
- Exemples de titres clés

---

## 🔄 Workflow de Qualité

```
1. COLLECTION (Limitée)
   ↓
   5 articles max par source
   
2. FILTRAGE (Strict)
   ↓
   Seuil 0.5 → Articles hautement pertinents seulement
   
3. SÉLECTION (Top N)
   ↓
   8 meilleurs articles seulement
   
4. ANALYSE PROFONDE
   ↓
   2000 chars de contenu par article
   Contexte historique riche
   
5. SYNTHÈSE PROFESSIONNELLE
   ↓
   5 sections structurées
   Analyse multi-niveau
   Insights actionnables
```

---

## 🎨 Exemple de Prompting LLM

Le nouveau prompt LLM insiste sur:

✅ **PROFONDEUR**: Analyse détaillée, pas de paraphrase
✅ **SYNTHÈSE**: Tendances transversales entre articles
✅ **INSIGHTS**: Conclusions non évidentes et actionnables
✅ **DONNÉES**: Chiffres, benchmarks, résultats concrets
✅ **CONTEXTE**: Positionnement dans l'écosystème
✅ **IMPACT**: Pourquoi c'est important et pour qui
✅ **PROSPECTIVE**: Implications futures
✅ **CLARTÉ**: Style professionnel et accessible

❌ **ÉVITE**: 
- Listes de titres sans analyse
- Généralités creuses
- Répétition mécanique du contenu

---

## 📊 Résultats Attendus

### Avant (Quantité)
- 10-15 articles traités
- Résumés superficiels
- Listes de titres
- Peu d'analyse
- Contexte minimal

### Après (Qualité)
- 5-8 articles soigneusement sélectionnés
- Analyse approfondie de chaque article
- Synthèse transversale des tendances
- Insights stratégiques
- Contexte historique riche
- Recommandations actionnables

---

## 🚀 Utilisation

### Générer un rapport de haute qualité

```bash
# Pipeline complet avec nouvelle configuration
python run_full_pipeline.py

# Ou via Streamlit
streamlit run streamlit_app.py
```

### Vérifier les paramètres actifs

```bash
cat config.yaml | grep -E "(filter_threshold|max_items_per_feed|use_api_llm|api_model)"
```

---

## 🔧 Ajustements Possibles

### Pour encore plus de qualité
```yaml
filter_threshold: 0.6  # Encore plus strict
max_items_per_feed: 3  # Top 3 par source
```

### Pour plus de volume (si nécessaire)
```yaml
filter_threshold: 0.4  # Plus inclusif
max_items_per_feed: 7  # Plus d'articles
```

Dans le synthesizer, ajuster dans le code:
```python
items_to_process = items[:10]  # Au lieu de 8
content[:2500]  # Plus de contenu par article
```

---

## 📈 Métriques de Qualité

Pour évaluer la qualité des notes:

1. **Profondeur d'analyse**
   - Chaque article a-t-il une explication détaillée?
   - Y a-t-il du contexte technique?

2. **Synthèse transversale**
   - Les tendances sont-elles identifiées?
   - Les patterns entre articles sont-ils relevés?

3. **Insights actionnables**
   - Y a-t-il des recommandations concrètes?
   - Les implications business/tech sont-elles claires?

4. **Contexte historique**
   - Le rappel de période précédente est-il présent?
   - L'évolution est-elle expliquée?

5. **Format professionnel**
   - Les 5 sections sont-elles présentes?
   - Le style est-il adapté aux décideurs?

---

## 💡 Bonnes Pratiques

1. **Exécuter moins fréquemment**
   - Plutôt que toutes les 15 minutes
   - Une fois par jour ou par semaine
   - Permet d'accumuler plus d'articles de qualité

2. **Réviser manuellement**
   - Vérifier les top 8 articles sélectionnés
   - Ajuster le threshold si nécessaire

3. **Utiliser le meilleur LLM**
   - Gemini 2.5 Flash (1M context, hybrid reasoning)
   - Groq GPT-OSS 120B (gratuit, performant)
   - Éviter les modèles locaux pour qualité max

4. **Archiver les meilleures notes**
   - Les rapports sont dans `reports/`
   - Comparer la qualité au fil du temps

---

## 🎓 Références

Format inspiré de:
- Guides de veille stratégique professionnelle
- Notes de synthèse en intelligence économique
- Rapports de consulting technique

Adapté pour:
- Décideurs techniques (CTO, architectes)
- Décideurs business (CEO, product managers)
- Équipes R&D et innovation
