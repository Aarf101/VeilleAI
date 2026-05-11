import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import urllib.parse
from html.parser import HTMLParser

def clean_text(text):
    if not text:
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    # Clean whitespace
    text = ' '.join(text.split())
    return text[:200]

def get_real_url(article):
    url = article.get('url','') or \
          article.get('link','') or ''
    
    # If it's a Google News RSS link
    # try to get the real source URL
    if 'news.google.com/rss/articles' in url:
        # Try to get from feedparser's source
        source_url = article.get('source_url','')
        if source_url:
            return source_url
        # Otherwise return the google news link
        # but display it differently
        return url
    return url

def call_llm(prompt, config):
    def get_config_value(config, *keys, default=''):
        for key in keys:
            if key in config and config[key]:
                return config[key]
        return default

    provider = get_config_value(config, 'provider', 'api_provider', default='groq')
    model    = get_config_value(config, 'model', 'api_model', default='')
    
    if provider == 'gemini':
        import os
        import importlib
        genai = importlib.import_module('google.genai')
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model or 'gemini-2.0-flash',
            contents=prompt
        )
        return resp.text
    
    elif provider == 'groq':
        from groq import Groq
        import os
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        client = Groq(api_key=api_key)
        resp   = client.chat.completions.create(
            model=model or 'llama-3.3-70b-versatile',
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.5
        )
        return resp.choices[0].message.content
    
    elif provider == 'ollama':
        import requests
        resp = requests.post(
            'http://localhost:11434/api/generate',
            json={
                "model": model or "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return resp.json().get('response', '')
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

import os

def generate_topic_section(topic, articles, config, index):
    if not articles:
        return f"{index}. Technology Watch: {topic}\nNo articles found.\n"
    
    display_articles = [a for a in articles if a.get('relevance_score', 0) >= 0.60][:3]
    if not display_articles:
        display_articles = articles[:3]

    articles_for_llm = ""
    for i, art in enumerate(display_articles, 1):
        title   = (art.get('title','') or '')[:150]
        
        # Add badge to LLM prompt so it realizes the article is hot/trending
        trending = art.get('trending_algorithm')
        if trending:
            title = f"[HOT/FRESH BOOST: {trending}] {title}"
            
        source  = art.get('source','') or 'Unknown source'
        summary = clean_text(
            art.get('summary','') or 
            art.get('description','') or 
            art.get('content','') or ''
        )[:200]
        date_art = (art.get('published','') or '')[:10]
        articles_for_llm += f"[{i}] {title} ({source}, {date_art}): {summary}\n"
    
    prompt = f"""You are an expert analyst in technology watch, focusing on the topic "{topic}".
Here are the major announcements of the week:
{articles_for_llm}

Write EXACTLY 3 paragraphs separated by "|||". No titles, no intro, no bullet points, just the 3 raw texts separated by "|||".
Paragraph 1: Executive summary (synthesis of announcements, 2-3 sentences).
Paragraph 2: Recent context reminder for the field (1-2 sentences).
Paragraph 3: Analysis and implications (consequences and deep trends, 2-3 sentences)."""
    
    try:
        import time
        time.sleep(3)  # Short pause for Groq
        llm_content = call_llm(prompt, config)
        llm_content = re.sub(r'<think>.*?</think>', '', llm_content, flags=re.IGNORECASE | re.DOTALL).strip()
        
        parts = llm_content.split('|||')
        exec_sum = parts[0].strip() if len(parts) > 0 else llm_content
        context_sum = parts[1].strip() if len(parts) > 1 else "Context generation unavailable."
        analysis_sum = parts[2].strip() if len(parts) > 2 else "Analysis generation unavailable."
    except Exception as e:
        exec_sum = f"LLM error during summary generation: {e}"
        context_sum = "N/A"
        analysis_sum = "N/A"
        
    recent_devs = f"{index}.3. Recent Developments\n"
    
    for i, art in enumerate(display_articles, 1):
        title = (art.get('title','') or '')[:150]
        source = art.get('source','') or 'Unknown source'
        date_art = (art.get('published','') or '')[:10]
        url = get_real_url(art)
        
        summary = clean_text(
            art.get('summary','') or 
            art.get('description','') or 
            art.get('content','') or ''
        )[:250]
        
        # Add link directly after title
        link_str = f" [🔗 Source]({url})" if url else ""
        recent_devs += f"{i}. {title}{link_str}\n{summary}... ({source}, {date_art})\n\n"
    
    return f"""{index}. Technology Watch: {topic}

{index}.1. Executive Summary
{exec_sum}

{index}.2. Context
{context_sum}

{recent_devs}{index}.4. Analysis & Implications
{analysis_sum}
"""

def generate_trends(filtered_by_topic, articles):
    dominant = max(
        filtered_by_topic.items(),
        key=lambda x: len(x[1]),
        default=('None', [])
    )[0]
    
    all_titles = " ".join(
        a.get('title','') for arts in 
        filtered_by_topic.values() for a in arts
    ).lower()
    
    alert = "No major alerts"
    if 'hack' in all_titles or 'breach' in all_titles:
        alert = "Security incident detected"
    elif 'crash' in all_titles or 'chute' in all_titles:
        alert = "Market drop detected"
    elif 'launch' in all_titles or 'lancement' in all_titles:
        alert = "Major new launch detected"
    
    return f"""2. Trends of the Week
* **Dominant Topic:** {dominant}
* **Priority Alert:** {alert}
* **Total Articles:** {sum(len(v) for v in filtered_by_topic.values())}
"""


def generate_report(filtered_by_topic, config, llm_client):
    from datetime import datetime
    date = datetime.now().strftime("%B %d, %Y")
    topics = config.get('topics', [])
    
    model = config.get('model') or config.get('api_model', '')
    if not model or model in ['Default', '', None]:
        provider = config.get('provider', 'groq')
        if provider == 'gemini':
            model = 'gemini-2.0-flash'
        else:
            model = 'llama-3.3-70b-versatile'
            
    provider = config.get('provider', 'groq').upper()
    
    report_sections = []
    all_articles = []
    
    for i, topic in enumerate(topics, start=3):
        topic_name = topic['name'] if isinstance(topic, dict) else topic
        articles = filtered_by_topic.get(topic_name, [])
        max_per_topic = 5 # Allowing up to 5 best articles per topic to give the AI more context
        
        top_articles = articles[:max_per_topic]
        all_articles.extend(top_articles)
        
        section_content = generate_topic_section(topic_name, top_articles, config, i)
        report_sections.append(section_content)
            
    # Executive Summary Generation
    total_arts = len(all_articles)
    all_sources = len(set(a.get('source', '') for a in all_articles if a.get('source')))
    
    topic_names = [t['name'] if isinstance(t, dict) else t for t in topics]
    exec_prompt = f"""You are the Editor in Chief. Date: {date}.
We have {total_arts} articles on the following topics: {', '.join(topic_names)}.
Generate ONLY a short executive summary (2-3 sentences) of the global news, without any titles or bullet points."""
    try:
        exec_summary = call_llm(exec_prompt, config)
        import re
        exec_summary = re.sub(r'<think>.*?</think>', '', exec_summary, flags=re.IGNORECASE | re.DOTALL).strip()
    except:
        exec_summary = "Intelligence gathering completed successfully on all configured topics."

    # Trends Generation
    trends = generate_trends(filtered_by_topic, all_articles)
    
    # Sources section
    sources_index = len(topics) + 3
    sources_text = f"{sources_index}. Sources & References\n"
    added_urls = set()
    for art in all_articles:
        title = (art.get('title','') or '')[:150]
        source = art.get('source','') or 'Unknown source'
        date_art = (art.get('published','') or '')[:10]
        url = get_real_url(art)
        
        trending = art.get('trending_algorithm', '')
        trend_badge = f" **[🔥 {trending}]**" if trending else ""
        
        if url and url not in added_urls:
            sources_text += f"* {source} - [{title}]({url}) - {date_art}{trend_badge}\n"
            added_urls.add(url)
        elif not url:
            # If no URL, just print the text
            url_str = str(art.get('url','') or art.get('link',''))
            if url_str not in added_urls:
                sources_text += f"* {source} - \"{title}\" - {date_art}{trend_badge}\n"
                added_urls.add(url_str)

    separator = "\n---\n\n"
    
    full_report = f"""# Intelligence Report — {date}
**Generated by VeilleAI · {provider} · {model}**

---

1. Executive Summary
{exec_summary}

Topics: {', '.join(topic_names)} | Articles: {total_arts} | Sources: {all_sources}

---

{trends}
---

{separator.join(report_sections)}

---

{sources_text}
---
*Report generated on {date} by VeilleAI*
"""
    return full_report

def get_friendly_error(error, provider):
    error_str = str(error).lower()
    
    if 'error: no articles collected!' in error_str:
        return {
            'type':    'no_data',
            'title':   'Aucun article trouvé !',
            'message': 'Le pipeline a terminé sa recherche mais la base de données est vide.',
            'solution': '✓ Vérifie que les "Data Sources" sont activées.\n✓ Vérifie que "Autonomous Web Search" est activé.\n✓ Choisis "Keep existing" ou désactive tes filtres si tu es en mode "Fresh start".'
        }
        
    if '429' in error_str or 'quota' in error_str:
        other = 'groq' if provider == 'gemini' \
                else 'gemini'
        return {
            'type':    'quota',
            'title':   'Limite journalière atteinte',
            'message': f'Tes requêtes {provider} '
                       f'gratuites sont épuisées '
                       f'pour aujourd\'hui.',
            'solution':f'✓ {provider.title()} '
                       f'repart demain matin\n'
                       f'✓ {other.title()} '
                       f'fonctionne maintenant',
            'action':  f'switch_to_{other}',
            'action_label': f'Passer à {other.title()} maintenant'
        }
    
    elif '401' in error_str or 'unauthorized' in error_str:
        key_name = f'{provider.upper()}_API_KEY'
        return {
            'type':    'auth',
            'title':   'Clé API invalide',
            'message': f'Ta {key_name} est incorrecte ou expirée.',
            'solution':f'1. Va sur console.{provider}.com\n'
                       f'2. Copie ta clé\n'
                       f'3. Mets dans .env : {key_name}=ta-clé',
            'action':  None
        }
    
    elif 'decommissioned' in error_str or '400' in error_str:
        defaults = {
            'groq':   'llama-3.3-70b-versatile',
            'gemini': 'gemini-2.0-flash',
        }
        new_model = defaults.get(provider, 
                                 'llama-3.3-70b-versatile')
        return {
            'type':    'model',
            'title':   'Modèle non disponible',
            'message': 'Ce modèle n\'existe plus.',
            'solution':f'Nouveau modèle recommandé : {new_model}',
            'action':  f'fix_model_{new_model}',
            'action_label': 'Corriger automatiquement'
        }
    
    elif 'timeout' in error_str or 'connection' in error_str:
        return {
            'type':    'network',
            'title':   'Pas de connexion',
            'message': 'Impossible de contacter le serveur IA.',
            'solution':'Vérifie ta connexion internet et réessaie.',
            'action':  'retry'
        }
    
    elif 'api_key' in error_str or 'not found' in error_str:
        key_name = f'{provider.upper()}_API_KEY'
        return {
            'type':    'missing_key',
            'title':   'Clé API manquante',
            'message': f'{key_name} introuvable dans ton fichier .env',
            'solution':f'console.{provider}.com → clé gratuite',
            'action':  None
        }
    
    else:
        return {
            'type':    'unknown',
            'title':   'Erreur inattendue',
            'message': str(error)[:100],
            'solution':'Réessaie dans quelques minutes.',
            'action':  'retry'
        }


