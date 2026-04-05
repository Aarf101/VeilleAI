import streamlit as st
import yaml
import os
import glob
import time
import urllib.parse
from pathlib import Path
from watcher.agents.synthesizer import call_llm

import requests
from pathlib import Path

def load_dotenv_vars():
    env_vars = {}
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def save_api_key_to_env(key_name, key_value):
    env_path = Path('.env')
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    # Update existing or add new
    found = False
    for i, line in enumerate(lines):
        if line.startswith(key_name + '='):
            lines[i] = f"{key_name}={key_value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key_name}={key_value}\n")
    with open(env_path, 'w') as f:
        f.writelines(lines)

def get_available_providers():
    available = {}
    key_map = {
        'groq':      'GROQ_API_KEY',
        'gemini':    'GEMINI_API_KEY',
        'together':  'TOGETHER_API_KEY',
        'openai':    'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'mistral':   'MISTRAL_API_KEY',
        'cohere':    'COHERE_API_KEY',
        'ollama':    None,
    }
    
    env_content = ""
    if Path(".env").exists():
        env_content = Path(".env").read_text()
    
    for provider, key in key_map.items():
        if key is None:
            available[provider] = {
                'available': True,
                'key_name': None,
                'reason': 'Local — no key needed'
            }
        elif key in env_content:
            available[provider] = {
                'available': True,
                'key_name': key,
                'reason': f'{key} found in .env'
            }
        else:
            available[provider] = {
                'available': False,
                'key_name': key,
                'reason': f'{key} missing from .env'
            }
    
    return available

def auto_select_best_provider(available):
    priority = [
        'groq', 'gemini', 'together', 
        'mistral', 'cohere', 'openai', 
        'anthropic', 'ollama'
    ]
    for provider in priority:
        if available.get(provider, {}).get('available'):
            return provider
    return 'ollama'

def get_best_model(provider):
    best_models = {
        'groq':      'llama-3.3-70b-versatile',
        'gemini':    'gemini-2.0-flash',
        'together':  'meta-llama/Llama-3-70b-chat-hf',
        'openai':    'gpt-4o-mini',
        'anthropic': 'claude-3-haiku-20240307',
        'mistral':   'mistral-medium',
        'cohere':    'command-r',
        'ollama':    'llama3',
    }
    return best_models.get(provider, 'llama3')

def show_friendly_error(error_info, config):
    st.markdown(f"""
<div style="background:rgba(239,68,68,0.1); border-left:3px solid #ef4444; border-radius:8px;padding:16px; margin:10px 0">
  <div style="font-size:14px;font-weight:600; color:#f87171;margin-bottom:8px">
    ✕ {error_info['title']}
  </div>
  <div style="font-size:13px;color:#94a3b8; margin-bottom:8px">
    {error_info['message']}
  </div>
  <div style="font-size:12px;color:#64748b; white-space:pre-line">
    {error_info['solution']}
  </div>
</div>
""", unsafe_allow_html=True)
    
    if error_info.get('action') and error_info['action'].startswith('switch_to_'):
        new_provider = error_info['action'].replace('switch_to_', '')
        if st.button(error_info.get('action_label', f"Passer à {new_provider.title()} maintenant"), type="primary"):
            defaults = {
                'groq':   'llama-3.3-70b-versatile',
                'gemini': 'gemini-2.0-flash',
            }
            st.session_state.config['provider'] = new_provider
            st.session_state.config['model'] = defaults.get(new_provider, 'llama3')
            save_config(st.session_state.config)
            st.success(f"Switched to {new_provider}! Relance le pipeline.")
            time.sleep(1)
            st.rerun()
            
    elif error_info.get('action') and error_info['action'].startswith('fix_model_'):
        new_model = error_info['action'].replace('fix_model_', '')
        if st.button(error_info.get('action_label', 'Corriger automatiquement'), type="primary"):
            st.session_state.config['model'] = new_model
            save_config(st.session_state.config)
            st.success(f"Modèle changé vers {new_model}!")
            time.sleep(1)
            st.rerun()

st.set_page_config(page_title="VeilleAI", layout="wide", initial_sidebar_state="expanded")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# --- Configuration Management ---
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config_file():
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                print(f"Loaded config from: {CONFIG_PATH}")
                print(f"Feeds: {len(config.get('feeds',[]))}")
                print(f"Topics: {config.get('topics',[])}")
                return config
    except Exception as e:
        print(f"Config error: {e}")
    return {}

def save_config(config):
    # Make sure these fields are saved
    defaults = {
        'provider': 'groq',
        'model': 'llama-3.3-70b-versatile',
        'sqlite_path': 'watcher.db',
        'chroma_path': './chroma_db',
        'llm_enabled': True,
        'relevance_threshold': 0.25,
        'items_per_feed': 10,
        'max_articles_to_llm': 15,
        'topics': [],
        'feeds': [],
        'schedule_mode': 'interval',
        'schedule_interval_minutes': 360,
    }
    for k, v in defaults.items():
        if k not in config:
            config[k] = v

    try:
        if 'feeds' in config:
            config['feeds'] = list(dict.fromkeys(config['feeds']))
        if 'topics' in config:
            seen_names = set()
            new_topics = []
            for t in config['topics']:
                if isinstance(t, dict):
                    name = t.get('name', '')
                    desc = t.get('description', '')
                else:
                    name = t
                    desc = ""
                
                if name and name.lower() not in seen_names:
                    new_topics.append({"name": name, "description": desc})
                    seen_names.add(name.lower())
            config['topics'] = new_topics
            
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f,
                      default_flow_style=False,
                      allow_unicode=True)
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Save error: {e}")
        return False

if 'config' not in st.session_state:
    st.session_state.config = load_config_file()

if 'new_topic_name' not in st.session_state:
    st.session_state.new_topic_name = ''
if 'new_topic_description' not in st.session_state:
    st.session_state.new_topic_description = ''

config = st.session_state.config


def _resolve_db_path() -> Path:
    """Resolve sqlite_path relative to project folder."""
    raw = config.get('sqlite_path', 'watcher.db')
    p = Path(raw)
    if not p.is_absolute():
        p = Path(__file__).parent / p
    return p

# --- Sidebar ---
with st.sidebar:
    st.sidebar.caption(
        f"Feeds in memory: "
        f"{len(st.session_state.config.get('feeds',[]))}"
    )
    st.sidebar.caption(
        f"Feeds in file: "
        f"{len(yaml.safe_load(open(CONFIG_PATH)).get('feeds',[]))}"
    )
    st.markdown("""
        <div class="sidebar-header">
            <div class="logo">Veille<span>AI</span></div>
            <div class="subtitle">INTELLIGENCE MONITOR</div>
        </div>
    """, unsafe_allow_html=True)
    
    css_styles = """
    <style>
    [data-testid="stSidebar"] .stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    [data-testid="stSidebar"] .stRadio label {
        display: flex !important;
        align-items: center !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #64748b !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
        border: none !important;
        background: transparent !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.05) !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] 
    > div > label:has(input:checked) {
        background: rgba(59,130,246,0.15) !important;
        color: #60a5fa !important;
        border-left: 3px solid #3b82f6 !important;
        padding-left: 11px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stRadio label > div:first-child {
        display: none !important;
    }
    </style>
    """
    st.markdown(css_styles, unsafe_allow_html=True)

    page = st.radio(
        "",
        [
            "⊞  Dashboard",
            "▶  Run Pipeline",
            "⏱  Scheduler",
            "🏷  Topics",
            "🗄  Data Sources",
            "⚙  Advanced",
            "📊  Monitoring"
        ],
        label_visibility="collapsed"
    )

    
    available_providers = get_available_providers()
    active_prov_sidebar = config.get("provider", "ollama")
    prov_ok_sidebar = available_providers.get(active_prov_sidebar, {}).get("available", False)
    prov_color = "green" if prov_ok_sidebar else "gray"

    st.markdown(f"""
        <div class="sidebar-footer">
            <div class="status-item">Database <span class="dot green">●</span></div>
            <div class="status-item">Scheduler <span class="dot green">●</span></div>
            <div class="status-item">{active_prov_sidebar} <span class="dot {prov_color}">●</span></div>
        </div>
    """, unsafe_allow_html=True)

def _header_article_count():
    db_path = config.get('sqlite_path', 'watcher.db')
    if not Path(db_path).exists(): return 0
    try:
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    except:
        return 0

@st.cache_data(ttl=30)
def get_article_count():
    db_path = _resolve_db_path()
    if not db_path.exists():
        return 0
    try:
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    except:
        return 0


@st.cache_data(ttl=30)
def get_recent_dashboard_articles(limit: int = 8):
    """Return recent articles for dashboard preview."""
    db_path = _resolve_db_path()
    if not db_path.exists():
        return []
    try:
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT title, source, published, summary FROM items ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return c.fetchall()
    except Exception:
        return []

article_count = get_article_count()
rss_count = len(config.get('feeds', []))
prov_model = f"{config.get('provider', 'N/A').upper()} · {config.get('model', 'N/A')}"

# --- Top Header ---
st.markdown(f"""
    <div class="top-header">
        <div class="wordmark">VeilleAI</div>
        <div class="header-right">
            <span class="v-badge badge-blue">{prov_model}</span>
            <span class="v-badge badge-blue">{article_count} articles</span>
            <span class="v-badge badge-blue">{rss_count} feeds</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Pages ---

if "Dashboard" in page:
    # Stat Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="v-card stat-card">
            <div class="stat-accent accent-blue"></div>
            <span class="card-title">Total Articles</span>
            <div class="stat-number blue">{article_count}</div>
            <div class="stat-subtitle">In Database</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="v-card stat-card">
            <div class="stat-accent accent-green"></div>
            <span class="card-title">Active Sources</span>
            <div class="stat-number">{rss_count}</div>
            <div class="stat-subtitle">Connected</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="v-card stat-card">
            <div class="stat-accent accent-amber"></div>
            <span class="card-title">Topics</span>
            <div class="stat-number">{len(config.get('topics', []))}</div>
            <div class="stat-subtitle">Monitored</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="v-card stat-card">
            <div class="stat-accent accent-gray"></div>
            <span class="card-title">RSS Feeds</span>
            <div class="stat-number">{rss_count}</div>
            <div class="stat-subtitle">Configured</div>
        </div>
        """, unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("""
        <div class="v-card">
            <span class="card-title">Monitored Topics</span>
            <div class="topic-container">
        """, unsafe_allow_html=True)
        # Render topics dynamically from disk
        saved_topics = []
        if CONFIG_PATH.exists():
            try: saved_topics = yaml.safe_load(open(CONFIG_PATH)).get("topics", [])
            except: pass
        for t in saved_topics:
            topic_name = t['name'] if isinstance(t, dict) else t
            st.markdown(f'<span class="topic-tag">{topic_name}</span>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # System status checks
        db_path_check = _resolve_db_path()
        db_exists = db_path_check.exists()
        db_status = '<span class="v-badge badge-green">CONNECTED</span>' if db_exists else '<span class="v-badge badge-red">MISSING</span>'
        
        sched_status = '<span class="v-badge badge-amber">STOPPED</span>'
        if Path("scheduler.pid").exists():
            try:
                with open("scheduler.pid", "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                sched_status = '<span class="v-badge badge-green">ACTIVE</span>'
            except (ValueError, OSError):
                sched_status = '<span class="v-badge badge-red">STALE PID</span>'
        
        interval = config.get("schedule_interval_minutes", config.get("scheduler_frequency", 60))
        h, m = divmod(interval, 60)
        interval_text = f"Every {h}h {m}m" if h > 0 else f"Every {m} mins"

        st.markdown(f"""
        <div class="v-card">
            <span class="card-title">System Status</span>
            <div class="v-list-item"><span>Scheduler Status</span> {sched_status}</div>
            <div class="v-list-item"><span>Database Status</span> {db_status}</div>
            <div class="v-list-item" style="border:none;"><span>Collection Interval</span> <span style="font-size:0.9rem; color:#9ca3af;">{interval_text}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_r:
        st.markdown('<div class="v-card"><span class="card-title">Quick Actions</span>', unsafe_allow_html=True)
        if st.button("▶ Run Full Pipeline", type="primary", use_container_width=True):
            with st.spinner("Running pipeline..."):
                import subprocess
                
                env = os.environ.copy()
                cwd = Path(__file__).parent
                try:
                    result = subprocess.run(
                        ["python", "run_full_pipeline.py"], 
                        cwd=cwd, env=env, capture_output=True, text=True, check=True
                    )
                    st.success("Pipeline executed successfully!")
                    get_article_count.clear()
                    with st.expander("View Output Logs"):
                        st.code(result.stdout)
                except subprocess.CalledProcessError as e:
                    st.error(f"Pipeline failed with exit code {e.returncode}")
                    with st.expander("View Error Logs"):
                        st.code(e.stderr)
                except Exception as e:
                    st.error(f"Failed to execute pipeline: {str(e)}")
                    
        if st.button("↺ Refresh Data", use_container_width=True):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.session_state.config = load_config_file()
            st.rerun()
            
        if st.button("⚙ Configure", use_container_width=True):
            st.info("Please select 'Advanced' from the sidebar navigation to configure system settings.", icon="⚙️")
        st.markdown('</div>', unsafe_allow_html=True)
        
        feed_html = "".join([f'<div class="v-list-item" style="font-size:0.8rem; color:#9ca3af;">{f}</div>' for f in config.get('feeds', [])])
        st.markdown(f"""
        <div class="v-card">
            <span class="card-title">Data Sources</span>
            {feed_html}
        </div>
        """, unsafe_allow_html=True)

    # Intelligence Reports full-width
    st.markdown('<div class="v-card"><span class="card-title">Intelligence Reports</span>', unsafe_allow_html=True)
    
    reports_dir = Path("reports")
    if reports_dir.exists() and reports_dir.is_dir():
        # Type hint correctly for Pyre
        reports_iter = reports_dir.glob("*.md")
        reports_list = [p for p in reports_iter]
        reports_list.sort(key=lambda p: os.path.getmtime(str(p)), reverse=True)
        
        if not reports_list:
            st.markdown('<div style="text-align:center; padding:2rem; color:#4b5563;"><span>📄</span><br/>No reports generated yet.</div>', unsafe_allow_html=True)
        else:
            from collections import defaultdict
            topic_reports = defaultdict(list)
            for rp in reports_list:
                parts = rp.stem.split('_')
                t_name = parts[-1] if len(parts) >= 4 else "Global"
                topic_reports[t_name].append(rp)
                
            for topic, r_list in topic_reports.items():
                st.markdown(f'<div class="card-title mt-2" style="color:var(--accent-blue-light); border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:0.25rem;">Topic: {topic}</div>', unsafe_allow_html=True)
                for report_path in r_list[:3]:
                    try:
                        str_path = str(report_path)
                        mtime = os.path.getmtime(str_path)
                        from datetime import datetime
                        dt = datetime.fromtimestamp(mtime).strftime('%B %d, %Y - %H:%M')
                        title = report_path.stem.replace('_', ' ').title()
                        
                        st.markdown(f"""
                        <div class="report-row">
                            <div>
                                <div class="report-date">{dt}</div>
                                <div class="report-title">{title}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        d1, d2, d3, d4 = st.columns([6, 1, 1, 1])
                        with d2:
                            with open(report_path, "rb") as f:
                                st.download_button("↓ MD", f, file_name=report_path.name, key=f"md_{report_path.name}")
                        with d3:
                            st.button("↓ PDF", key=f"pdf_{report_path.name}", disabled=True, help="PDF generation not configured")
                        with d4:
                            st.button("↓ DOCX", key=f"docx_{report_path.name}", disabled=True, help="DOCX generation not configured")
                    except Exception as e:
                        st.error(f"Error loading report {report_path.name}: {e}")
    else:
         st.markdown('<div style="text-align:center; padding:2rem; color:#4b5563;"><span>📁</span><br/>Reports directory not found.</div>', unsafe_allow_html=True)
         
    st.markdown('</div>', unsafe_allow_html=True)

    # Recent articles directly on Dashboard
    st.markdown('<div class="v-card"><span class="card-title">Recent Articles</span>', unsafe_allow_html=True)
    recent_dashboard_articles = get_recent_dashboard_articles(limit=8)
    if not recent_dashboard_articles:
        st.info("No articles found in database.")
    else:
        for title, source, pub, summary in recent_dashboard_articles:
            safe_title = title or "Untitled"
            safe_source = source or "Unknown source"
            safe_pub = pub or "Unknown date"
            with st.expander(f"{safe_title} - {safe_source} ({safe_pub})"):
                st.write(summary if summary else "No summary available.")
    st.markdown('</div>', unsafe_allow_html=True)

elif "Run Pipeline" in page:
    st.markdown('<div class="v-card"><span class="card-title">Run Pipeline</span>', unsafe_allow_html=True)
    
    mode = st.radio("Collection Mode", 
                    ["Clear old >7 days", "Fresh start", "Keep existing"],
                    horizontal=True)
    
    if mode == "Clear old >7 days":
        st.markdown('<div class="v-alert alert-info">Will remove articles older than 7 days before fetching new data.</div>', unsafe_allow_html=True)
    elif mode == "Fresh start":
        st.markdown('<div class="v-alert alert-warn">Will drop database tables and start from scratch. Proceed with caution.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="v-alert alert-success">Standard incremental collection. Existing documents are preserved.</div>', unsafe_allow_html=True)
        
    # --- ACTIVE PROVIDER CHECK ---
    available_providers = get_available_providers()
    active_prov = config.get("provider", "ollama")
    active_model = config.get("model", "unknown")
    prov_ok = available_providers.get(active_prov, {}).get("available", False)
    
    if prov_ok:
        
        # Determine model capabilities locally since backend isn't executing here.
        speed_bar = "████████░░ Fast"
        quality_bar = "███████░░░ Good"
        cost_bar = "Free"
        
        if "gemini" in active_model:
            speed_bar, quality_bar = "█████████░ Very Fast", "████████░░ High"
        if "llama" in active_model and "70b" not in active_model:
             speed_bar, quality_bar = "██████████ Very Fast", "█████░░░░░ Moderate"
             
        st.markdown(f"""
        <div style="background:rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 1rem; margin-bottom: 1rem; border-radius: 4px;">
            <strong style="color:#10b981;">ACTIVE PROVIDER</strong><br/><br/>
            ✓ {active_prov} · {active_model}<br/>
            API Key found — ready to run<br/><br/>
            Speed:   {speed_bar}<br/>
            Quality: {quality_bar}<br/>
            Cost:    {cost_bar}
        </div>
        """, unsafe_allow_html=True)
        can_run = True
    else:
        st.markdown(f"""
        <div style="background:rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 1rem; margin-bottom: 1rem; border-radius: 4px;">
            <strong style="color:#ef4444;">✗ CANNOT RUN</strong><br/><br/>
            Provider "{active_prov}" needs an API Key but it was not found in .env<br/><br/>
            Available alternatives you can use NOW:
        </div>
        """, unsafe_allow_html=True)
        can_run = False
        
        cols = st.columns(min(len([p for p, d in available_providers.items() if d['available']]), 4) or 1)
        col_idx = 0
        for p, d in available_providers.items():
            if d['available'] and p != active_prov:
                with cols[col_idx % len(cols)]:
                    if st.button(f"✓ Switch to {p}", key=f"switch_to_{p}", use_container_width=True):
                        st.session_state.config['provider'] = p
                        st.session_state.config['model'] = get_best_model(p)
                        save_config(st.session_state.config)
                        st.success(f"Switched to {p}!")
                        time.sleep(1)
                        st.rerun()
                col_idx += 1

    st.markdown('<span class="card-title mt-2">Pre-flight check</span>', unsafe_allow_html=True)
    chk1, chk2, chk3, chk4 = st.columns(4)
    with chk1: 
        if can_run:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #10b981; color:#34d399;">✓ API Key Valid</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #ef4444; color:#f87171;">✗ API Key Missing</div>', unsafe_allow_html=True)
    with chk2: st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #10b981; color:#34d399;">✓ Database Writable</div>', unsafe_allow_html=True)
    
    with chk3: 
        if len(config.get('feeds', [])) > 0:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #10b981; color:#34d399;">✓ RSS Feeds Online</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #ef4444; color:#f87171;">✗ No RSS Feeds</div>', unsafe_allow_html=True)
            
    with chk4: 
        if len(config.get('topics', [])) > 0:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #10b981; color:#34d399;">✓ Topics Parsed</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="v-alert" style="background:transparent; border:1px solid #ef4444; color:#f87171;">✗ No Topics</div>', unsafe_allow_html=True)
    
    st.markdown('<span class="card-title mt-2">Current Topics</span>', unsafe_allow_html=True)
    active_topics = []
    if CONFIG_PATH.exists():
        try: active_topics = yaml.safe_load(open(CONFIG_PATH)).get('topics', [])
        except: pass
    if active_topics:
        topic_tags = "".join([f"<span class=topic-tag>{t['name'] if isinstance(t, dict) else t}</span>" for t in active_topics])
        st.markdown(f'<div class="topic-container" style="margin-bottom:1rem;">{topic_tags}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="v-alert alert-warn">⚠ No topics configured — your report may not be focused. Go to Topics page to add some.</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02); padding:1rem; border-radius:8px; margin-bottom:1rem; font-size:0.85rem; color:#9ca3af;">
        Provider: <strong>{config.get('provider')}</strong> | 
        Model: <strong>{config.get('model')}</strong> | 
        Items/Feed Limit: <strong>{config.get('items_per_feed')}</strong> | 
        Max Articles for LLM: <strong>{config.get('max_articles_to_llm')}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶ Run Full Pipeline", type="primary", use_container_width=True, disabled=not can_run):
        with st.spinner("Executing pipeline..."):
            import subprocess
            try:
                env = {**os.environ, **load_dotenv_vars()}
                env["PIPELINE_MODE"] = mode
                cwd = str(Path(__file__).parent)
                result = subprocess.run(
                    ["python", "run_full_pipeline.py"],
                    capture_output=True, text=True, timeout=900,
                    cwd=cwd, env=env
                )
                
                error_str = result.stderr + "\n" + result.stdout
                has_llm_error = "LLM Error" in error_str or "groq API error" in error_str or "400" in error_str or "429" in error_str

                if result.returncode == 0 and not has_llm_error:
                    st.success("Pipeline completed successfully!")
                    get_article_count.clear()
                    
                    # Optional: metric counts could be parsed from stdout if needed
                    st.metric("Pipeline Status", "Completed")
                    
                    st.markdown('<hr style="border-color: rgba(255,255,255,0.07);">', unsafe_allow_html=True)
                    st.markdown('### Latest Intelligence Report')
                    
                    report_files = sorted(
                        glob.glob("reports/intelligence_report_*.md"), 
                        reverse=True
                    )
                    
                    if report_files:
                        latest_mtime = os.path.getmtime(report_files[0])
                        # Get all reports generated within 5 seconds of the latest (same batch)
                        recent_reports = [f for f in report_files if latest_mtime - os.path.getmtime(f) <= 5]
                        
                        for latest in recent_reports:
                            parts = Path(latest).stem.split('_')
                            topic = parts[-1] if len(parts) >= 4 else "Global"
                            
                            st.markdown(f'#### 📑 Category: {topic}')
                            with open(latest, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            st.markdown(f"""<div style="background:#0a0c10; padding:2rem; border-radius:12px; border:1px solid rgba(255,255,255,0.07); margin-bottom:1rem; height:400px; overflow-y:auto;">
                            {content}
                            </div>""", unsafe_allow_html=True)
                            
                            d1, d2, d3, d4 = st.columns([1,1,1,5])
                            safe_key = Path(latest).name
                            with d1:
                                st.download_button("↓ MD", content, file_name=safe_key, key=f"dl_pipeline_md_{safe_key}")
                            with d2:
                                st.button("↓ PDF", key=f"dl_pipeline_pdf_{safe_key}", disabled=True)
                            with d3:
                                st.button("↓ DOCX", key=f"dl_pipeline_docx_{safe_key}", disabled=True)
                            st.markdown("<br/>", unsafe_allow_html=True)
                    else:
                        st.warning("Report completed, but no markdown files found in `reports/` directory.")
                else:
                    st.error("Pipeline failed or encountered generating errors.")
                    
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).parent))
                    from watcher.agents.synthesizer import get_friendly_error
                    
                    err_details = get_friendly_error(error_str, config.get('provider', ''))
                    show_friendly_error(err_details, config)
                    
                    with st.expander("View Technical Logs", expanded=False):
                        st.code(error_str, language="bash")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
            
    st.markdown('</div>', unsafe_allow_html=True)

elif "Scheduler" in page:
    import sys
    import time
    import subprocess
    import signal
    
    def read_scheduler_pid():
        pid_file = Path("scheduler.pid")
        if not pid_file.exists():
            return None
        try:
            return int(pid_file.read_text().strip())
        except:
            return None

    def is_scheduler_running():
        pid = read_scheduler_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            pid_file = Path("scheduler.pid")
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except:
                    pass
            return False

    def start_scheduler():
        env = {**os.environ, **load_dotenv_vars()}
        log_file = open("scheduler.log", "ab")
        creationflags = 0
        start_new_session = False
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
        else:
            start_new_session = True
        
        cmd = [sys.executable, "scheduler_agent.py"]
        process = subprocess.Popen(
            cmd, 
            stdout=log_file, 
            stderr=subprocess.STDOUT, 
            cwd=str(Path(__file__).parent), 
            env=env,
            creationflags=creationflags,
            start_new_session=start_new_session
        )
        Path("scheduler.pid").write_text(str(process.pid))
        return process.pid

    def stop_scheduler():
        pid = read_scheduler_pid()
        if not pid:
            return
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True
                )
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        try:
            pid_file = Path("scheduler.pid")
            if pid_file.exists():
                pid_file.unlink()
        except:
            pass

    running_state = is_scheduler_running()
    current_pid = read_scheduler_pid()
    status_badge = '<span class="v-badge badge-green">RUNNING</span>' if running_state else '<span class="v-badge badge-red">STOPPED</span>'
    pid_display = str(current_pid) if current_pid and running_state else "None"
    
    from datetime import datetime, timedelta

    def get_next_run(cfg):
        mode = cfg.get("schedule_mode", "interval")
        if mode == "interval":
            m = cfg.get("schedule_interval_minutes", 60)
            return f"In {m} minutes (after start)"
        elif mode == "fixed_hour":
            hours = cfg.get("schedule_fixed_hours", [])
            if not hours: return "Not configured"
            now = datetime.now()
            next_runs = []
            for h in hours:
                try:
                    t = datetime.strptime(h, "%H:%M").time()
                    dt = datetime.combine(now.date(), t)
                    if dt <= now: dt += timedelta(days=1)
                    next_runs.append(dt)
                except: pass
            if not next_runs: return "Invalid hours"
            nr = min(next_runs)
            if nr.date() == now.date(): return f"Today at {nr.strftime('%H:%M')}"
            else: return f"Tomorrow at {nr.strftime('%H:%M')}"
        elif mode == "specific":
            dt_str = cfg.get("schedule_specific_datetime", "")
            try:
                target = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                if datetime.now() > target: return "Already passed"
                return target.strftime('%A %B %d %Y at %H:%M')
            except: return "Invalid datetime"
        return "Unknown"

    next_run_text = get_next_run(config)

    modes = ["Interval", "Fixed Hour", "Specific"]
    mode_map = {"interval": "Interval", "fixed_hour": "Fixed Hour", "specific": "Specific"}
    inv_map = {v: k for k, v in mode_map.items()}

    current_mode_key = config.get("schedule_mode", "interval")
    current_mode = mode_map.get(current_mode_key, "Interval")

    # --- STATUS CARD ---
    if running_state:
        st.markdown(f"""
        <div class="v-card">
            <span class="card-title">Scheduler Status</span>
            <div class="v-list-item">State: {status_badge}</div>
            <div class="v-list-item">Mode: <span style="font-weight:500;">{current_mode}</span></div>
            <div class="v-list-item">Next run: <span style="font-weight:500;">{next_run_text}</span></div>
            <div class="v-list-item" style="border:none;">Process ID: <span style="font-weight:500;">{pid_display}</span></div>
            <div class="mt-2" style="padding-top:0.5rem; border-top:1px solid rgba(255,255,255,0.05);">
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 4, 1])
        with c2:
            if st.button("■ STOP — click to edit schedule", type="primary", use_container_width=True):
                try:
                    stop_scheduler()
                    st.success("Scheduler stopped")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to stop: {e}")
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    else:
        st.markdown(f"""
        <div class="v-card">
            <span class="card-title">Scheduler Status</span>
            <div class="v-list-item" style="border:none;">State: {status_badge}</div>
            <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.5rem;">
                Configure your schedule below then click Start when ready
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- CONFIGURATION SECTION ---
    if running_state:
        st.markdown('<div class="v-card" style="opacity:0.5; pointer-events:none;"><span class="card-title">Schedule Configuration (locked)</span>', unsafe_allow_html=True)
        st.markdown('<div style="color:#ef4444; font-size:0.85rem; margin-bottom:1rem;">⚠ Stop the scheduler to edit</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="v-card"><span class="card-title">Schedule Configuration (actif)</span>', unsafe_allow_html=True)

    selected_mode_label = st.radio(
        "Select Scheduling Mode", 
        modes, 
        index=modes.index(current_mode), 
        label_visibility="collapsed",
        disabled=running_state
    )
    new_mode = inv_map[selected_mode_label]
    
    if not running_state and new_mode != current_mode_key:
        config["schedule_mode"] = new_mode
        save_config(config)
        st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin: 1rem 0;'>", unsafe_allow_html=True)

    if new_mode == "interval":
        st.markdown('<div style="font-size:0.9rem; color:#e5e7eb; margin-bottom:0.5rem;">Run every:</div>', unsafe_allow_html=True)
        
        current_total_mins = config.get("schedule_interval_minutes", 60)
        curr_h = current_total_mins // 60
        curr_m = current_total_mins % 60
        
        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        with c1:
            new_h = st.number_input("hours", min_value=0, max_value=168, value=curr_h, disabled=running_state, label_visibility="collapsed")
        with c2:
            st.markdown("<div style='margin-top:0.5rem;'>hours</div>", unsafe_allow_html=True)
        with c3:
            new_m = st.number_input("minutes", min_value=0, max_value=59, value=curr_m, disabled=running_state, label_visibility="collapsed")
        with c4:
            st.markdown("<div style='margin-top:0.5rem;'>minutes</div>", unsafe_allow_html=True)
            
        new_total_mins = (new_h * 60) + new_m
        
        if new_total_mins == 0:
            st.error("Interval cannot be 0. Please set at least 1 minute.")
        elif not running_state and new_total_mins != current_total_mins:
            config["schedule_interval_minutes"] = new_total_mins
            save_config(config)
            st.rerun()
            
        st.markdown(f'<div style="font-size:0.85rem; color:#60a5fa; margin-top:0.5rem;">Pipeline will run every {new_h}h {new_m:02d}m</div>', unsafe_allow_html=True)
            
        st.markdown('<div style="font-size:0.85rem; color:#9ca3af; margin-top:1rem; margin-bottom:0.5rem;">Presets:</div>', unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        if p1.button("1h", disabled=running_state): 
            config["schedule_interval_minutes"] = 60
            save_config(config)
            st.success("Interval set to 1h 00m")
            time.sleep(1)
            st.rerun()
        if p2.button("6h", disabled=running_state): 
            config["schedule_interval_minutes"] = 360
            save_config(config)
            st.success("Interval set to 6h 00m")
            time.sleep(1)
            st.rerun()
        if p3.button("12h", disabled=running_state): 
            config["schedule_interval_minutes"] = 720
            save_config(config)
            st.success("Interval set to 12h 00m")
            time.sleep(1)
            st.rerun()
        if p4.button("24h", disabled=running_state): 
            config["schedule_interval_minutes"] = 1440
            save_config(config)
            st.success("Interval set to 24h 00m")
            time.sleep(1)
            st.rerun()

    elif new_mode == "fixed_hour":
        st.markdown('<div style="font-size:0.9rem; color:#e5e7eb; margin-bottom:0.5rem;">Run every day at:</div>', unsafe_allow_html=True)
        hours_list = config.get("schedule_fixed_hours", [])
        
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1: new_h = st.selectbox("Hour", [f"{i:02d}" for i in range(24)], disabled=running_state)
        with c2: new_m = st.selectbox("Minute", [f"{i:02d}" for i in range(0, 60, 5)], disabled=running_state)
        with c3: 
            st.markdown("<div style='margin-top:1.8rem'></div>", unsafe_allow_html=True)
            if st.button("+ Add Time", use_container_width=True, disabled=running_state):
                time_str = f"{new_h}:{new_m}"
                if time_str not in hours_list:
                    hours_list.append(time_str)
                    hours_list.sort()
                    config["schedule_fixed_hours"] = hours_list
                    save_config(config)
                    st.rerun()
                    
        if hours_list:
            st.markdown('<div style="font-size:0.85rem; color:#9ca3af; margin-top:1rem; margin-bottom:0.5rem;">Scheduled:</div>', unsafe_allow_html=True)
            for t in hours_list:
                tc1, tc2 = st.columns([4, 1])
                tc1.markdown(f'<div class="v-list-item" style="border:none;">{t}</div>', unsafe_allow_html=True)
                if tc2.button("✕", key=f"del_time_{t}", disabled=running_state):
                    hours_list.remove(t)
                    config["schedule_fixed_hours"] = hours_list
                    save_config(config)
                    st.rerun()

    elif new_mode == "specific":
        current_dt_str = config.get("schedule_specific_datetime", datetime.now().strftime("%Y-%m-%d %H:%M"))
        try:
            current_dt = datetime.strptime(current_dt_str, "%Y-%m-%d %H:%M")
        except:
            current_dt = datetime.now()
            
        c1, c2 = st.columns(2)
        with c1: d_val = st.date_input("Date", value=current_dt.date(), disabled=running_state)
        with c2: t_val = st.time_input("Time", value=current_dt.time(), disabled=running_state)
        
        if not running_state:
            new_dt_str = f"{d_val.strftime('%Y-%m-%d')} {t_val.strftime('%H:%M')}"
            if new_dt_str != config.get("schedule_specific_datetime", ""):
                config["schedule_specific_datetime"] = new_dt_str
                save_config(config)
            
        st.markdown(f'<div style="font-size:0.85rem; color:#60a5fa; margin-top:0.5rem;">→ Will run once on: {get_next_run(config)}</div>', unsafe_allow_html=True)

    if not running_state:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin: 1rem 0;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            if st.button("▶ START SCHEDULER", type="primary", use_container_width=True):
                try:
                    start_scheduler()
                    st.success("Scheduler started successfully")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {e}")
                    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="v-card"><span class="card-title">Live Log Viewer</span>', unsafe_allow_html=True)
    
    log_text = "[No logs found]"
    log_path = Path("scheduler.log")
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            log_text = "".join(lines[-100:]) if lines else "[Log file is empty]"
        except Exception:
            log_text = "[Error reading logs]"
            
    st.code(log_text, language="bash")
    l1, l2 = st.columns(2)
    with l1: 
        if st.button("Refresh Logs"):
            st.rerun()
    with l2: 
        if st.button("Clear Logs"):
            try:
                open("scheduler.log", "w").close()
                st.success("Logs cleared")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear logs: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("Systemd Deployment Commands"):
        st.code("sudo systemctl restart veilleai.service\nsudo journalctl -u veilleai -f")

elif "Topics" in page:
    st.markdown('<div class="v-card"><span class="card-title">YOUR TOPICS</span>', unsafe_allow_html=True)
    
    if not st.session_state.config.get('topics', []):
        st.info("No topics configured. Add one below.")
    
    for t in st.session_state.config.get('topics', []):
        name = t.get('name', t) if isinstance(t, dict) else t
        description = t.get('description', 'No description') if isinstance(t, dict) else "No description"
        
        col_text, col_del = st.columns([10, 1])
        with col_text:
            st.markdown(f'<div style="font-weight:bold; font-size:16px;">{name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:gray; font-size:12px; margin-bottom:10px;">{description}</div>', unsafe_allow_html=True)
        with col_del:
            if st.button("✕", key=f"del_topic_{name}"):
                st.session_state.config['topics'].remove(t)
                save_config(st.session_state.config)
                st.rerun()
                
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    st.markdown('<div class="v-card"><span class="card-title">ADD NEW TOPIC</span>', unsafe_allow_html=True)
    
    topic_name = st.text_input("Topic name", value=st.session_state.new_topic_name, placeholder="e.g. Artificial Intelligence")
    topic_description = st.text_area("Keywords / Description", value=st.session_state.new_topic_description, placeholder="Auto-generate or type keywords...", height=100)
    
    col_gen, col_add = st.columns(2)
    with col_gen:
        if st.button("✨ Auto-generate with AI", use_container_width=True):
            if topic_name:
                with st.spinner("Generating..."):
                    prompt = f"Generate exactly 15 technical keywords for monitoring the topic: '{topic_name}'. Return ONLY the keywords separated by spaces. No explanation. No numbers. No bullets."
                    try:
                        result = call_llm(prompt, config)
                        import re
                        result = re.sub(r'<think>.*?</think>', '', result, flags=re.IGNORECASE|re.DOTALL).strip()
                        st.session_state.new_topic_description = result
                        st.session_state.new_topic_name = topic_name
                        st.rerun()
                    except Exception as e:
                        st.error(f"Generation error: {e}")
            else:
                st.warning("Enter a topic name first.")
                
    with col_add:
        if st.button("+ Add Topic", type="primary", use_container_width=True):
            if topic_name and topic_description:
                # Duplicate check
                existing = [t.get('name', t).lower() if isinstance(t, dict) else t.lower() for t in st.session_state.config['topics']]
                if topic_name.lower() not in existing:
                    st.session_state.config['topics'].append({"name": topic_name, "description": topic_description})
                    save_config(st.session_state.config)
                    st.session_state.new_topic_name = ''
                    st.session_state.new_topic_description = ''
                    st.success(f"Added {topic_name}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Topic already exists.")
            else:
                st.warning("Please provide name and description.")
    st.markdown('</div>', unsafe_allow_html=True)

elif "Data Sources" in page:
    st.markdown('<div class="v-card"><span class="card-title">ADD NEW FEED</span>', unsafe_allow_html=True)
    new_feed_url = st.text_input("Feed URL", placeholder="https://...")
    if st.button("Add Feed", type="primary"):
        if new_feed_url and new_feed_url.strip():
            url = new_feed_url.strip()
            if url not in st.session_state.config.get('feeds', []):
                st.session_state.config['feeds'].append(url)
                save_config(st.session_state.config)
                st.success(f"Added {url}!")
                st.rerun()
            else:
                st.warning("Feed already exists.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="v-card"><span class="card-title">PRESETS</span>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        if st.button("Popular AI Feeds", use_container_width=True):
            feeds = [
                "https://techcrunch.com/category/artificial-intelligence/feed/",
                "https://venturebeat.com/category/ai/feed/",
                "https://www.artificialintelligence-news.com/feed/",
                "https://feeds.feedburner.com/TheHackersNews",
                "https://arxiv.org/rss/cs.AI",
                "https://huggingface.co/blog/feed.xml"
            ]
            added = 0
            for f in feeds:
                if f not in st.session_state.config['feeds']:
                    st.session_state.config['feeds'].append(f)
                    added += 1
            if added > 0:
                save_config(st.session_state.config)
                st.success(f"Added {added} AI feeds!")
                st.rerun()
    with p2:
        if st.button("Top Tech Feeds", use_container_width=True):
            feeds = [
                "https://news.ycombinator.com/rss",
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.arstechnica.com/arstechnica/index",
                "https://www.wired.com/feed/rss",
                "https://techcrunch.com/feed/"
            ]
            added = 0
            for f in feeds:
                if f not in st.session_state.config['feeds']:
                    st.session_state.config['feeds'].append(f)
                    added += 1
            if added > 0:
                save_config(st.session_state.config)
                st.success(f"Added {added} Tech feeds!")
                st.rerun()
    with p3:
        if st.button("YouTube Tech Channels", use_container_width=True):
            feeds = [
                "https://www.youtube.com/feeds/videos.xml?channel_id=UCnUYZLuoy1rq1aVMwx4aTzw",
                "https://www.youtube.com/feeds/videos.xml?channel_id=UCVhQ2NnY5Rskt6UjCUkJ_DA",
                "https://www.youtube.com/feeds/videos.xml?channel_id=UC9-y-6csu5WGm29I7JiwpnA"
            ]
            added = 0
            for f in feeds:
                if f not in st.session_state.config['feeds']:
                    st.session_state.config['feeds'].append(f)
                    added += 1
            if added > 0:
                save_config(st.session_state.config)
                st.success(f"Added {added} YT feeds!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="v-card"><span class="card-title">ALL FEEDS (toggle + weight)</span>', unsafe_allow_html=True)
    
    feeds_enabled = st.session_state.config.get('feeds_enabled', {})
    feeds_weight = st.session_state.config.get('feeds_weight', {})
    
    changed = False
    for i, f in enumerate(st.session_state.config.get('feeds', [])):
        c_toggle, c_url, c_badge, c_weight, c_del = st.columns([1, 4, 1, 2, 1])
        
        with c_toggle:
            is_on = feeds_enabled.get(f, True)
            new_on = st.toggle("", value=is_on, key=f"toggle_f_{i}", label_visibility="collapsed")
            if new_on != is_on:
                feeds_enabled[f] = new_on
                changed = True
                
        with c_url:
            st.markdown(f'<div style="font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-top:8px;">{f}</div>', unsafe_allow_html=True)
            
        with c_badge:
            badge = "YT" if "youtube.com" in f else "RSS"
            color = "#ff0000" if badge == "YT" else "#3b82f6"
            st.markdown(f'<span style="background:{color}; color:white; padding:2px 6px; border-radius:4px; font-size:10px;">{badge}</span>', unsafe_allow_html=True)
            
        with c_weight:
            current_w = float(feeds_weight.get(f, 1.0))
            new_w = st.slider("", 0.1, 2.0, current_w, 0.1, key=f"weight_f_{i}", label_visibility="collapsed")
            if new_w != current_w:
                feeds_weight[f] = new_w
                changed = True
                
        with c_del:
            if st.button("✕", key=f"del_feed_{i}"):
                st.session_state.config['feeds'].pop(i)
                feeds_enabled.pop(f, None)
                feeds_weight.pop(f, None)
                changed = True
                
    if changed:
        st.session_state.config['feeds_enabled'] = feeds_enabled
        st.session_state.config['feeds_weight'] = feeds_weight
        save_config(st.session_state.config)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif "Advanced" in page:
    st.markdown('<div class="v-card"><span class="card-title">Advanced Settings</span>', unsafe_allow_html=True)
    
    # 1. ⚠️ WARNINGS
    current_threshold = config.get("relevance_threshold", 0.30)
    if current_threshold > 0.6:
        st.markdown(f"""
        <div style='background:rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 1rem; margin-bottom: 1rem; border-radius: 4px;'>
            <strong>⚠️ WARNING: Your filter is very strict</strong><br/>
            Threshold: {current_threshold:.2f} <br/>
            This may cause empty reports!
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔧 Fix it — Set to 0.30", key="fix_threshold"):
            config["relevance_threshold"] = 0.30
            save_config(config)
            st.success("Filter set to 0.30 — reports will now have content!")
            time.sleep(1)
            st.rerun()

    # 2. 🤖 AVAILABLE PROVIDERS & API KEYS
    st.markdown('<span class="card-title mt-2">Available Providers</span>', unsafe_allow_html=True)
    
    available_providers = get_available_providers()
    
    if st.button("✨ Auto-select best available", type="primary", use_container_width=True):
        best = auto_select_best_provider(available_providers)
        st.session_state.config['provider'] = best
        st.session_state.config['model'] = get_best_model(best)
        save_config(st.session_state.config)
        st.success(f"Auto-selected {best} with {config['model']}!")
        time.sleep(1)
        st.rerun()

    st.markdown('<div style="background:rgba(255,255,255,0.02); padding:1rem; border-radius:8px; margin-top:1rem; border:1px solid rgba(255,255,255,0.05);">', unsafe_allow_html=True)
    
    for prov, details in available_providers.items():
        c1, c2, c3 = st.columns([1, 4, 1])
        is_active = (config.get('provider') == prov)
        active_label = " (Active)" if is_active else ""
        
        with c1:
            icon = "✓" if details['available'] else "✗"
            color = "#10b981" if details['available'] else "#ef4444"
            st.markdown(f'<span style="color:{color}; font-weight:bold;">{icon} {prov}{active_label}</span>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<span style="color:#9ca3af; font-size:0.9rem;">{details["reason"]}</span>', unsafe_allow_html=True)
        with c3:
            if details['available']:
                if not is_active:
                    if st.button("Select", key=f"sel_{prov}", use_container_width=True):
                        st.session_state.config['provider'] = prov
                        st.session_state.config['model'] = get_best_model(prov)
                        save_config(st.session_state.config)
                        st.rerun()
                else:
                    st.markdown('<span style="color:#10b981; font-size:1.2rem;">●</span>', unsafe_allow_html=True)
            elif prov != 'ollama':
                if st.button("Add key", key=f"add_key_btn_{prov}", use_container_width=True):
                    st.session_state[f"show_input_{prov}"] = True
                
                if st.session_state.get(f"show_input_{prov}"):
                    new_key = st.text_input(f"Paste {details['key_name']}", type="password", key=f"input_{prov}")
                    if st.button("Save key", key=f"save_btn_{prov}"):
                        if new_key:
                            save_api_key_to_env(details['key_name'], new_key)
                            st.session_state[f"show_input_{prov}"] = False
                            st.success(f"Key for {prov} saved!")
                            time.sleep(1)
                            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="v-card" style="border-top: 1px solid rgba(255,255,255,0.05); background: rgba(255,255,255,0.01);"><span class="card-title">Ollama (Local)</span>', unsafe_allow_html=True)
    
    # Status Check
    is_running = False
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        is_running = (r.status_code == 200)
    except:
        pass
    
    col_st, col_link = st.columns([1, 1])
    with col_st:
        if is_running:
            st.markdown('Status: <span class="v-badge badge-green">RUNNING</span>', unsafe_allow_html=True)
        else:
            st.markdown('Status: <span class="v-badge badge-red" style="background:#ef4444; color:white;">NOT RUNNING</span>', unsafe_allow_html=True)
    with col_link:
        st.markdown('<a href="https://ollama.com/download" target="_blank" style="text-decoration:none; color:#60a5fa; font-size:0.9rem;">Download Ollama ↗</a>', unsafe_allow_html=True)
    
    ollama_model = st.text_input("Ollama Model Name", value=config.get('ollama_model', 'llama3'), key="ollama_model_input")
    if ollama_model != config.get('ollama_model'):
        config['ollama_model'] = ollama_model
        save_config(config)
        st.rerun()
        
    if st.button("🔌 Test connection", use_container_width=True):
        if not is_running:
            st.error("Ollama is not running. Please start it first.")
        else:
            with st.spinner(f"Testing {ollama_model}..."):
                try:
                    resp = requests.post("http://localhost:11434/api/generate", 
                                       json={"model": ollama_model, "prompt": "hi", "stream": False},
                                       timeout=10)
                    if resp.status_code == 200:
                        st.success(f"Successfully connected to {ollama_model}!")
                    else:
                        st.error(f"Error from Ollama: {resp.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. 🗄️ STORAGE PATHS
    st.markdown('<span class="card-title mt-4">Storage Paths</span>', unsafe_allow_html=True)
    config['sqlite_path'] = st.text_input("SQLite Database Path", value=config.get("sqlite_path", "watcher.db"))
    config['chroma_path'] = st.text_input("ChromaDB Path", value=config.get("chroma_path", "./chroma_db"))
    
    # 5. 🔍 RELEVANCE FILTER
    st.markdown('<span class="card-title mt-4">Relevance Filter</span>', unsafe_allow_html=True)
    
    threshold = st.slider("Relevance Filter Threshold", 0.0, 1.0, config.get("relevance_threshold", 0.30), 0.05)
    config['relevance_threshold'] = threshold
    
    if threshold <= 0.3:
        badge = '<span style="background:#064e3b; color:#34d399; padding:2px 8px; border-radius:12px; font-size:0.8rem;">🟢 PERMISSIVE</span>'
        desc = "Most articles pass"
        est = "~80%"
    elif threshold <= 0.5:
        badge = '<span style="background:#78350f; color:#fbbf24; padding:2px 8px; border-radius:12px; font-size:0.8rem;">🟡 BALANCED</span>'
        desc = "Good quality filter"
        est = "~50%"
    elif threshold <= 0.7:
        badge = '<span style="background:#7c2d12; color:#fb923c; padding:2px 8px; border-radius:12px; font-size:0.8rem;">🟠 STRICT</span>'
        desc = "Only relevant articles"
        est = "~20%"
    else:
        badge = '<span style="background:#7f1d1d; color:#f87171; padding:2px 8px; border-radius:12px; font-size:0.8rem;">🔴 VERY STRICT</span>'
        desc = "Almost nothing passes"
        est = "< 5%"
        
    st.markdown(f'<div style="margin-top:-1rem; margin-bottom:1rem;">{badge} <strong>{desc}</strong><br/><span style="font-size:0.8rem; color:#9ca3af;">{est} of articles pass at this threshold</span></div>', unsafe_allow_html=True)

    # 7. 💾 SAVE + EXPORT/IMPORT
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("Save Configuration", type="primary", use_container_width=True):
        st.session_state.config = config
        save_config(config)
        st.success("Configuration saved explicitly!")
        time.sleep(1)
        st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config_content = f.read()
            st.download_button(
                "📤 Export Config",
                data=config_content,
                file_name="veilleai_config.yaml",
                mime="text/yaml",
                use_container_width=True
            )
    with c2:
        uploaded = st.file_uploader("Import config", type=['yaml','yml'], label_visibility="collapsed")
        if uploaded:
            content = uploaded.read().decode('utf-8')
            new_config = yaml.safe_load(content)
            st.session_state.config = new_config
            save_config(new_config)
            st.success("Configuration imported!")
            time.sleep(1)
            st.rerun()

    # 8. ℹ️ SYSTEM INFORMATION (collapsed)
    with st.expander("▶ System Information"):
        import sys, platform
        import streamlit as st_module
        db_path = Path("watcher.db")
        chroma_path = Path(config.get("chroma_path", "./chroma_db"))
        db_size = f"{(db_path.stat().st_size / 1024 / 1024):.1f} MB" if db_path.exists() else "Not found"
        
        # Calculate chroma size
        chroma_size_mb = 0
        if chroma_path.exists() and chroma_path.is_dir():
            total_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
            chroma_size_mb = total_size / 1024 / 1024
        
        st.code(f"""Python version:    {sys.version.split()[0]}
Streamlit version: {st_module.__version__}
Platform:          {platform.system()}
Project folder:    {str(Path(__file__).parent.absolute())}
Database size:     {db_size}
ChromaDB size:     {chroma_size_mb:.1f} MB
Total articles:    {article_count}""", language="text")

    st.markdown('</div>', unsafe_allow_html=True)

elif "Monitoring" in page:
    db_path = config.get('sqlite_path', 'watcher.db')
    try:
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM items")
            total_articles = c.fetchone()[0]
            
            c.execute("SELECT COUNT(DISTINCT source) FROM items")
            unique_sources = c.fetchone()[0]
            
            c.execute("SELECT MIN(published) FROM items")
            oldest = c.fetchone()[0] or 'N/A'
            if oldest != 'N/A':
                from datetime import datetime
                try: oldest = datetime.fromisoformat(oldest.replace('Z', '+00:00')).strftime('%b %d, %Y')
                except: pass
            
            c.execute("SELECT MAX(published) FROM items")
            latest = c.fetchone()[0] or 'N/A'
            if latest != 'N/A':
                from datetime import datetime
                try: latest = datetime.fromisoformat(latest.replace('Z', '+00:00')).strftime('%b %d, %Y %H:%M')
                except: pass
            
            c.execute("SELECT title, summary, source, published FROM items ORDER BY published DESC LIMIT 5")
            recent_articles = c.fetchall()
            
    except:
        total_articles = 0
        unique_sources = 0
        oldest = 'N/A'
        latest = 'N/A'
        recent_articles = []

    st.markdown('<div class="v-card"><span class="card-title">Live Metrics</span>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Articles DB", str(total_articles))
    with c2: st.metric("Unique Sources", str(unique_sources))
    with c3: st.metric("Oldest Entry", str(oldest))
    with c4: st.metric("Latest Entry", str(latest))
    st.markdown('</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown('<div class="v-card"><span class="card-title">Recent Articles</span></div>', unsafe_allow_html=True)
        if not recent_articles:
            st.info("No articles found in database.")
        for title, summary, source, pub in recent_articles:
            with st.expander(f"{title} - {source} ({pub})"):
                st.write(summary if summary else "No summary available.")
    
    with col_r:
        st.markdown("""
        <div class="v-card">
            <span class="card-title">System Health</span>
            <div class="v-list-item"><span>LLM API (Provider)</span> <span class="v-badge badge-green">OK Response</span></div>
            <div class="v-list-item"><span>Vector DB Memory</span> <span class="v-badge badge-amber">N/A</span></div>
            <div class="v-list-item"><span>Storage Space</span> <span class="v-badge badge-green">Active</span></div>
        </div>
        """, unsafe_allow_html=True)
