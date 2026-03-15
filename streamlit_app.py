"""
Streamlit Configuration UI for Automated Veille System

Provides user-friendly interface to:
- Manage topics to monitor
- Configure RSS feeds and APIs
- Set filtering thresholds
- Adjust scheduler frequency
- Select synthesis model
"""

import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, List, Any
import sqlite3
import subprocess
import os
import sys
import signal
from datetime import datetime
import glob

# Page config
st.set_page_config(
    page_title="Veille Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] * {
    color: #c9d1d9 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.875rem;
    letter-spacing: 0.01em;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    background: #1f2937 !important;
    border-radius: 6px;
    color: #58a6ff !important;
    font-weight: 600;
}
[data-testid="stSidebar"] p {
    color: #8b949e !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px !important;
}

/* ── Main header ── */
.vi-header {
    padding: 28px 0 20px 0;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 28px;
}
.vi-wordmark {
    font-size: 1.6rem;
    font-weight: 700;
    color: #2563eb;
    letter-spacing: -0.02em;
    margin: 0;
}
.vi-sub {
    font-size: 0.82rem;
    color: #6b7280;
    margin: 2px 0 0 2px;
    font-weight: 400;
}
.vi-status-bar {
    display: flex;
    gap: 20px;
    align-items: center;
    justify-content: flex-end;
    padding-top: 6px;
}
.vi-pill {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.02em;
}
.vi-pill-blue  { background: #eff6ff; color: #2563eb; }
.vi-pill-green { background: #f0fdf4; color: #16a34a; }
.vi-pill-gray  { background: #f3f4f6; color: #6b7280; }

/* ── Stat cards ── */
.stat-row { display: flex; gap: 16px; margin: 0 0 24px 0; }
.stat-card {
    flex: 1;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.stat-card .label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 8px;
}
.stat-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    line-height: 1;
}
.stat-card .sub { font-size: 0.78rem; color: #6b7280; margin-top: 4px; }

/* ── Section containers ── */
.section-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px 26px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.section-title {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #374151;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f3f4f6;
}

/* ── Status badge ── */
.badge { display:inline-block; font-size:0.75rem; font-weight:600;
         padding:3px 10px; border-radius:14px; letter-spacing:0.02em; }
.badge-green  { background:#dcfce7; color:#166534; }
.badge-red    { background:#fee2e2; color:#991b1b; }
.badge-orange { background:#ffedd5; color:#9a3412; }
.badge-blue   { background:#dbeafe; color:#1e40af; }

/* ── Feed / topic list rows ── */
.list-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 8px;
    background: #f9fafb;
    margin-bottom: 6px;
    border: 1px solid #f3f4f6;
    font-size: 0.88rem;
    color: #374151;
    word-break: break-all;
}

/* ── Inline alert banners ── */
.alert {
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.875rem;
    margin: 12px 0;
    font-weight: 400;
}
.alert-info    { background:#eff6ff; border-left:3px solid #3b82f6; color:#1e40af; }
.alert-warn    { background:#fffbeb; border-left:3px solid #f59e0b; color:#92400e; }
.alert-success { background:#f0fdf4; border-left:3px solid #22c55e; color:#166534; }
.alert-error   { background:#fef2f2; border-left:3px solid #ef4444; color:#991b1b; }

/* ── Report expander polish ── */
details summary { font-weight: 600; color: #2563eb; }
div[data-testid="stExpander"] summary p { color: #2563eb !important; font-weight: 600 !important; }
div[data-testid="stExpander"] summary svg { color: #2563eb !important; }

/* ── Button sizing tweak ── */
[data-testid="stButton"] > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: #2563eb !important;
    border-color: #2563eb !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #1d4ed8 !important;
}

/* ── Metric label smaller ── */
[data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

/* ── Remove default top padding ── */
.block-container { padding-top: 1.5rem !important; }

/* ── Log code block ── */
.stCodeBlock { border-radius: 8px; }

/* ── Divider refinement ── */
hr { border-color: #f3f4f6 !important; }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_resource
def load_config_file(path: str = "config.yaml") -> Dict:
    """Load YAML configuration file."""
    if Path(path).exists():
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {
        'database': 'watcher.db',
        'feeds': [],
        'apis': [],
        'topics': [],
        'max_items_per_feed': 10,
        'max_synthesis_items': 25,
        'run_every_minutes': 1440,
        'use_api_llm': True,
        'api_provider': 'groq',
        'use_llm': False,
        'filter_threshold': 0.45,
        'chroma_persist_dir': 'chroma_data',
    }


def save_config_file(config: Dict, path: str = "config.yaml"):
    """Save configuration to YAML file."""
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    st.success("Configuration saved.")


def get_db_stats() -> Dict[str, Any]:
    """Get database statistics."""
    db_path = st.session_state.config.get('database', 'watcher.db')
    if not Path(db_path).exists():
        return {'items': 0, 'sources': 0, 'earliest': None, 'latest': None}
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM items")
        items = c.fetchone()[0]
        
        c.execute("SELECT COUNT(DISTINCT source) FROM items")
        sources = c.fetchone()[0]
        
        c.execute("SELECT MIN(published), MAX(published) FROM items")
        earliest, latest = c.fetchone()
        
        conn.close()
        return {'items': items, 'sources': sources, 'earliest': earliest, 'latest': latest}
    except:
        return {'items': 0, 'sources': 0, 'earliest': None, 'latest': None}


# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = load_config_file()

stats = get_db_stats()

# ── Header ────────────────────────────────────────────────────────────────────
provider = st.session_state.config.get('api_provider', 'groq').upper()
model    = st.session_state.config.get('api_model', '—')
feeds_n  = len(st.session_state.config.get('feeds', []))

st.markdown(f"""
<div class="vi-header">
  <div style="display:flex; align-items:flex-start; justify-content:space-between;">
    <div>
      <p class="vi-wordmark">Veille Intelligence</p>
      <p class="vi-sub">Automated AI monitoring &amp; synthesis</p>
    </div>
    <div class="vi-status-bar">
      <span class="vi-pill vi-pill-blue">{provider} &middot; {model}</span>
      <span class="vi-pill vi-pill-green">{stats['items']:,} articles</span>
      <span class="vi-pill vi-pill-gray">{feeds_n} feeds</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("<p style='margin-top:8px'>Navigation</p>", unsafe_allow_html=True)
page = st.sidebar.radio(
    "",
    ["Dashboard", "Run Pipeline", "Scheduler", "Topics", "Data Sources", "Advanced", "Monitoring"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="font-size:0.75rem; color:#8b949e; line-height:1.8;">
  <div style="margin-bottom:4px; font-weight:600; color:#6e7681; text-transform:uppercase; letter-spacing:.07em; font-size:.68rem;">System</div>
  <div>DB &nbsp;&nbsp;&nbsp; {'watcher.db' if not Path('watcher.db').exists() else '<span style="color:#3fb950">connected</span>'}</div>
  <div>Sources &nbsp; {stats['sources']}</div>
  <div>Topics &nbsp;&nbsp; {len(st.session_state.config.get('topics', []))}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================
if page == "Dashboard":
    # Stat cards row
    topics_n = len(st.session_state.config.get('topics', []))
    st.markdown(f"""
<div class="stat-row">
  <div class="stat-card">
    <div class="label">Total Articles</div>
    <div class="value">{stats['items']:,}</div>
    <div class="sub">in database</div>
  </div>
  <div class="stat-card">
    <div class="label">Active Sources</div>
    <div class="value">{stats['sources']}</div>
    <div class="sub">unique origins</div>
  </div>
  <div class="stat-card">
    <div class="label">Topics</div>
    <div class="value">{topics_n}</div>
    <div class="sub">monitored</div>
  </div>
  <div class="stat-card">
    <div class="label">RSS Feeds</div>
    <div class="value">{feeds_n}</div>
    <div class="sub">configured</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Two column config overview
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Monitored Topics</div>', unsafe_allow_html=True)
        topics = st.session_state.config.get('topics', [])
        if topics:
            pills = " ".join(f'<span class="badge badge-blue" style="margin:2px">{t}</span>' for t in topics)
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#9ca3af; font-size:.875rem">No topics configured yet.</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">Quick Actions</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Run Full Pipeline", use_container_width=True, type="primary"):
            st.info("Switch to 'Run Pipeline' in the sidebar to execute the system.")
        if st.button("Check Scheduler Status", use_container_width=True):
            running = False
            scheduler_pid_file = Path("scheduler.pid")
            if scheduler_pid_file.exists():
                try:
                    pid = int(scheduler_pid_file.read_text().strip())
                    os.kill(pid, 0)
                    running = True
                except Exception:
                    running = False
            if running:
                st.markdown('<div class="alert alert-success">Scheduler is active and running in the background.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert alert-warn">Scheduler is not running. Go to the Scheduler page to start it.</div>', unsafe_allow_html=True)

    # Historical reports
    st.markdown('<div class="section-card"><div class="section-title">Intelligence Reports</div>', unsafe_allow_html=True)
    reports_dir = Path("reports")
    if reports_dir.exists():
        report_files = sorted(glob.glob(str(reports_dir / "intelligence_report_*.md")), reverse=True)
        if report_files:
            st.markdown(f'<div class="alert alert-info">{len(report_files)} archived reports found.</div>', unsafe_allow_html=True)
            for report_file in report_files[:10]:
                report_path = Path(report_file)
                timestamp = report_path.stem.replace("intelligence_report_", "")
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%b %d, %Y — %H:%M")
                except:
                    display_time = timestamp

                with st.expander(display_time):
                    with open(report_file, 'r') as f:
                        st.markdown(f.read())
                    base_name = report_path.stem
                    pdf_file  = reports_dir / f"{base_name}.pdf"
                    docx_file = reports_dir / f"{base_name}.docx"
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        with open(report_file, 'r') as f:
                            st.download_button("Download Markdown", data=f.read(),
                                file_name=f"{base_name}.md", mime="text/markdown",
                                key=f"md_{timestamp}", use_container_width=True)
                    with col2:
                        if pdf_file.exists():
                            with open(pdf_file, 'rb') as f:
                                st.download_button("Download PDF", data=f.read(),
                                    file_name=f"{base_name}.pdf", mime="application/pdf",
                                    key=f"pdf_{timestamp}", use_container_width=True)
                    with col3:
                        if docx_file.exists():
                            with open(docx_file, 'rb') as f:
                                st.download_button("Download Word", data=f.read(),
                                    file_name=f"{base_name}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"docx_{timestamp}", use_container_width=True)
        else:
            st.markdown('<span style="color:#9ca3af; font-size:.875rem">No reports yet. Run the pipeline to generate the first one.</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#9ca3af; font-size:.875rem">Reports folder not found. Run the pipeline to get started.</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# PAGE 2: RUN PIPELINE
# ============================================================================
elif page == "Run Pipeline":
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Run Pipeline</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Execute the full multi-agent collection, filtering, and synthesis workflow.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Collection Mode</div>', unsafe_allow_html=True)
        refresh_mode = st.radio(
            "",
            options=["Clear old (>7 days)", "Fresh start (clear all)", "Keep existing"],
            index=0,
            help="'Clear old' removes stale articles so new ones are collected",
            label_visibility="collapsed"
        )
        if refresh_mode == "Clear old (>7 days)":
            st.markdown('<div class="alert alert-info">Articles older than 7 days will be removed before collecting new ones.</div>', unsafe_allow_html=True)
        elif refresh_mode == "Fresh start (clear all)":
            st.markdown('<div class="alert alert-warn">All existing articles will be deleted. A full re-collection will happen.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert alert-warn">Existing articles are kept. You may get 0 new items if feeds were recently collected.</div>', unsafe_allow_html=True)
        show_logs = st.checkbox("Show pipeline output logs", value=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">System Check</div>', unsafe_allow_html=True)
        api_key_set   = Path(".env").exists() and "GROQ_API_KEY" in open(".env").read() or \
                        Path(".env").exists() and "GEMINI_API_KEY" in open(".env").read()
        db_exists     = Path("watcher.db").exists()
        config_valid  = len(st.session_state.config.get('feeds', [])) > 0
        api_status    = '<span class="badge badge-green">Set</span>' if api_key_set else '<span class="badge badge-red">Missing</span>'
        db_status     = '<span class="badge badge-green">Ready</span>' if db_exists else '<span class="badge badge-gray">Not found</span>'
        feed_status   = '<span class="badge badge-green">Configured</span>' if config_valid else '<span class="badge badge-orange">None</span>'
        st.markdown(f"""
<div style="font-size:0.85rem;line-height:2.2;color:#374151;">
  <div style="display:flex;justify-content:space-between"><span>API Key</span>{api_status}</div>
  <div style="display:flex;justify-content:space-between"><span>Database</span>{db_status}</div>
  <div style="display:flex;justify-content:space-between"><span>RSS Feeds</span>{feed_status}</div>
</div>
""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Run Pipeline", type="primary", use_container_width=True):
        import os
        with st.spinner("Running pipeline — this may take 1-2 minutes..."):
            cmd = ["python3", "run_full_pipeline.py"]
            if refresh_mode == "Clear old (>7 days)":
                cmd.append("--clear-old")
            elif refresh_mode == "Fresh start (clear all)":
                cmd.append("--fresh")
            try:
                env = os.environ.copy()
                if Path(".env").exists():
                    with open(".env") as f:
                        for line in f:
                            if line.strip() and not line.startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env[key] = value
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)

                if result.returncode == 0:
                    st.markdown('<div class="alert alert-success">Pipeline completed successfully.</div>', unsafe_allow_html=True)
                    if show_logs:
                        with st.expander("Pipeline output"):
                            st.code(result.stdout, language="text")

                    lines = result.stdout.split('\n')
                    c1, c2 = st.columns(2)
                    for line in lines:
                        if 'Collected:' in line:
                            c1.metric("Items Collected", line.split(':')[1].strip().split()[0])
                        if 'Filtered:' in line:
                            c2.metric("Items After Filter", line.split(':')[1].strip().split()[0])

                    import glob as _glob
                    report_files = sorted(_glob.glob("reports/intelligence_report_*.md"), reverse=True)
                    if report_files:
                        latest_report = report_files[0]
                        st.markdown(f'<div class="section-title" style="margin-top:24px">Generated Report</div>', unsafe_allow_html=True)
                        with open(latest_report, 'r') as f:
                            report = f.read()
                        st.markdown(report)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button("Download Markdown", data=report,
                                file_name=Path(latest_report).name, mime="text/markdown",
                                use_container_width=True)
                        pdf_path  = latest_report.replace('.md', '.pdf')
                        docx_path = latest_report.replace('.md', '.docx')
                        with col2:
                            if Path(pdf_path).exists():
                                with open(pdf_path, 'rb') as f:
                                    st.download_button("Download PDF", data=f.read(),
                                        file_name=Path(pdf_path).name, mime="application/pdf",
                                        use_container_width=True)
                        with col3:
                            if Path(docx_path).exists():
                                with open(docx_path, 'rb') as f:
                                    st.download_button("Download Word", data=f.read(),
                                        file_name=Path(docx_path).name,
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        use_container_width=True)
                else:
                    st.markdown(f'<div class="alert alert-error">Pipeline failed (exit code {result.returncode}).</div>', unsafe_allow_html=True)
                    st.code(result.stderr, language="text")
            except subprocess.TimeoutExpired:
                st.markdown('<div class="alert alert-error">Pipeline timed out after 15 minutes.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="alert alert-error">Error: {e}</div>', unsafe_allow_html=True)


# ============================================================================
# PAGE 3: SCHEDULER MANAGEMENT
# ============================================================================
elif page == "Scheduler":
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Scheduler</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Start, stop, and monitor the automatic pipeline scheduler.</p>', unsafe_allow_html=True)

    scheduler_pid_file = Path("scheduler.pid")
    log_file = Path("scheduler.log")

    def _load_env_vars() -> Dict[str, str]:
        env = os.environ.copy()
        if Path(".env").exists():
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
        return env

    def _read_scheduler_pid():
        if not scheduler_pid_file.exists():
            return None
        try:
            return int(scheduler_pid_file.read_text().strip())
        except Exception:
            return None

    def _pid_exists(pid: int) -> bool:
        if not pid or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        except Exception:
            return False
        return True

    def check_scheduler_running():
        pid = _read_scheduler_pid()
        if pid and _pid_exists(pid):
            return True
        if scheduler_pid_file.exists():
            try:
                scheduler_pid_file.unlink()
            except Exception:
                pass
        return False

    def get_scheduler_pid():
        pid = _read_scheduler_pid()
        return [str(pid)] if pid and _pid_exists(pid) else []

    def start_scheduler_process() -> int:
        env = _load_env_vars()
        command = [sys.executable, "-c", "from watcher.scheduler import start_scheduler; start_scheduler()"]
        with open(log_file, "ab") as log_handle:
            popen_kwargs = {
                "cwd": str(Path.cwd()),
                "env": env,
                "stdout": log_handle,
                "stderr": subprocess.STDOUT,
            }
            if os.name == "nt":
                popen_kwargs["creationflags"] = (
                    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
            else:
                popen_kwargs["start_new_session"] = True

            process = subprocess.Popen(command, **popen_kwargs)

        scheduler_pid_file.write_text(str(process.pid))
        return process.pid

    def stop_scheduler_process() -> None:
        pid = _read_scheduler_pid()
        if not pid:
            return

        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, timeout=10)
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        try:
            scheduler_pid_file.unlink()
        except Exception:
            pass

    is_running      = check_scheduler_running()
    scheduler_pids  = get_scheduler_pid()
    interval        = st.session_state.config.get('run_every_minutes', 1440)
    hours           = interval / 60
    status_badge    = '<span class="badge badge-green">Running</span>' if is_running else '<span class="badge badge-red">Stopped</span>'

    st.markdown(f"""
<div class="section-card">
  <div class="section-title">Status</div>
  <div style="display:flex; gap:40px; align-items:center;">
    <div><div class="label" style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-bottom:4px">State</div>{status_badge}</div>
    <div><div class="label" style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-bottom:4px">Interval</div>
         <span style="font-weight:600;color:#111827">{hours:.1f}h</span> <span style="color:#6b7280;font-size:.8rem">({interval} min)</span></div>
    <div><div class="label" style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-bottom:4px">Process IDs</div>
         <span style="font-weight:600;color:#111827">{len(scheduler_pids) if scheduler_pids else '—'}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start", disabled=is_running, use_container_width=True, type="primary"):
            try:
                start_scheduler_process()
                st.markdown('<div class="alert alert-success">Scheduler started — running in background.</div>', unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.markdown(f'<div class="alert alert-error">Failed to start: {e}</div>', unsafe_allow_html=True)
    with col2:
        if st.button("Stop", disabled=not is_running, use_container_width=True):
            try:
                stop_scheduler_process()
                st.markdown('<div class="alert alert-success">Scheduler stopped.</div>', unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.markdown(f'<div class="alert alert-error">Failed to stop: {e}</div>', unsafe_allow_html=True)
    with col3:
        if st.button("Restart", disabled=not is_running, use_container_width=True):
            try:
                stop_scheduler_process()
                import time; time.sleep(2)
                start_scheduler_process()
                st.markdown('<div class="alert alert-success">Scheduler restarted.</div>', unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.markdown(f'<div class="alert alert-error">Failed to restart: {e}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-card"><div class="section-title">Live Logs</div>', unsafe_allow_html=True)
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = f.read()
            recent_logs = '\n'.join(logs.split('\n')[-50:])
            st.code(recent_logs, language="text", line_numbers=False)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Refresh", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("Clear Logs", use_container_width=True):
                    open(log_file, 'w').close()
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading logs: {e}")
    else:
        st.markdown('<span style="color:#9ca3af;font-size:.875rem">No logs yet. Start the scheduler to see output here.</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Production deployment (systemd)"):
        st.code("""./install_scheduler_service.sh
sudo systemctl status agenticnotes-scheduler
sudo systemctl stop agenticnotes-scheduler
sudo systemctl start agenticnotes-scheduler""", language="bash")


# ============================================================================
# PAGE 4: TOPICS MANAGEMENT
# ============================================================================
elif page == "Topics":
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Topics</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Define what subjects the system monitors and filters by.</p>', unsafe_allow_html=True)

    topics = st.session_state.config.get('topics', [])

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Active Topics</div>', unsafe_allow_html=True)
        if topics:
            for i, topic in enumerate(topics):
                tc1, tc2 = st.columns([0.88, 0.12])
                with tc1:
                    st.markdown(f'<div class="list-row">{topic}</div>', unsafe_allow_html=True)
                with tc2:
                    if st.button("Remove", key=f"del_topic_{i}", use_container_width=True):
                        topics.pop(i)
                        st.session_state.config['topics'] = topics
                        st.rerun()
        else:
            st.markdown('<span style="color:#9ca3af;font-size:.875rem">No topics configured yet.</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-title">Add Topic</div>', unsafe_allow_html=True)
        new_topic = st.text_input("", placeholder="e.g. machine learning, blockchain, quantum computing",
                                  label_visibility="collapsed")
        if st.button("Add Topic", use_container_width=True):
            if new_topic and new_topic not in topics:
                topics.append(new_topic)
                st.session_state.config['topics'] = topics
                st.rerun()
            elif new_topic in topics:
                st.markdown('<div class="alert alert-warn">This topic already exists.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">Preset Collections</div>', unsafe_allow_html=True)
        if st.button("AI / Machine Learning", use_container_width=True):
            st.session_state.config['topics'] = ["artificial intelligence","machine learning",
                "deep learning","neural networks","generative AI"]
            st.rerun()
        if st.button("Tech General", use_container_width=True):
            st.session_state.config['topics'] = ["software development","programming",
                "technology innovation","web development","cloud computing"]
            st.rerun()
        if st.button("Security Focus", use_container_width=True):
            st.session_state.config['topics'] = ["cybersecurity","data protection",
                "privacy","encryption","threat detection"]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 3: DATA SOURCES
# ============================================================================
elif page == "Data Sources":
    st.header("Data Source Configuration")
    st.markdown("_Manage RSS feeds and API sources_")
    
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Data Sources</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Manage RSS feeds and collection parameters.</p>', unsafe_allow_html=True)

    feeds = st.session_state.config.get('feeds', [])

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Configured Feeds</div>', unsafe_allow_html=True)
        if feeds:
            for i, feed in enumerate(feeds):
                fc1, fc2 = st.columns([0.88, 0.12])
                with fc1:
                    st.markdown(f'<div class="list-row">{feed}</div>', unsafe_allow_html=True)
                with fc2:
                    if st.button("Remove", key=f"del_feed_{i}", use_container_width=True):
                        feeds.pop(i)
                        st.session_state.config['feeds'] = feeds
                        st.rerun()
        else:
            st.markdown('<span style="color:#9ca3af;font-size:.875rem">No feeds configured yet.</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-title">Add Feed</div>', unsafe_allow_html=True)
        new_feed = st.text_input("", placeholder="https://example.com/rss", label_visibility="collapsed")
        if st.button("Add Feed", use_container_width=True):
            if new_feed and new_feed.startswith('http') and new_feed not in feeds:
                feeds.append(new_feed)
                st.session_state.config['feeds'] = feeds
                st.rerun()
            elif new_feed in feeds:
                st.markdown('<div class="alert alert-warn">This feed is already in the list.</div>', unsafe_allow_html=True)
            elif new_feed:
                st.markdown('<div class="alert alert-warn">URL must start with http.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">Preset Collections</div>', unsafe_allow_html=True)
        if st.button("AI News Feeds", use_container_width=True):
            st.session_state.config['feeds'] = [
                "https://news.ycombinator.com/rss",
                "https://www.artificialintelligence-news.com/feed/",
                "https://venturebeat.com/category/ai/feed/",
                "https://techcrunch.com/category/artificial-intelligence/feed/"
            ]
            st.rerun()
        if st.button("Tech News Feeds", use_container_width=True):
            st.session_state.config['feeds'] = [
                "https://news.ycombinator.com/rss",
                "https://techcrunch.com/feed/",
                "https://www.theverge.com/rss/index.xml",
                "https://arstechnica.com/feed/"
            ]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-title">Collection Limits</div>', unsafe_allow_html=True)
        max_items = st.slider("Items per feed", min_value=1, max_value=50,
            value=st.session_state.config.get('max_items_per_feed', 10),
            help="Articles fetched per RSS feed per run")
        st.session_state.config['max_items_per_feed'] = max_items
        max_synth = st.slider("Max articles to LLM", min_value=5, max_value=100,
            value=st.session_state.config.get('max_synthesis_items', 25),
            help="Top N sent to synthesis. Lower = faster, Higher = richer report")
        st.session_state.config['max_synthesis_items'] = max_synth
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 4: ADVANCED SETTINGS
# ============================================================================
elif page == "Advanced":
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Advanced</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Fine-tune the LLM, filtering, scheduling, and storage settings.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Synthesis Model</div>', unsafe_allow_html=True)
        use_api = st.checkbox("Use API-based LLM", value=st.session_state.config.get('use_api_llm', True))
        st.session_state.config['use_api_llm'] = use_api

        if use_api:
            api_provider = st.selectbox("Provider",
                ["groq", "gemini", "ollama", "together"],
                index=["groq", "gemini", "ollama", "together"].index(
                    st.session_state.config.get('api_provider', 'groq')))
            st.session_state.config['api_provider'] = api_provider

            model_options = {
                'groq':   {'models': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
                           'names':  ['GPT-OSS 120B (best, 120B params)', 'Llama 3.3 70B (reliable)'],
                           'default': 'openai/gpt-oss-120b'},
                'gemini': {'models': ['gemini-3-flash-preview','gemini-2.5-pro','gemini-2.5-flash','gemini-2.0-flash','gemini-2.0-flash-lite'],
                           'names':  ['Gemini 3 Flash (newest)','Gemini 2.5 Pro (best quality)','Gemini 2.5 Flash (1M ctx)','Gemini 2.0 Flash (balanced)','Gemini 2.0 Flash-Lite (fastest)'],
                           'default': 'gemini-3-flash-preview'},
            }
            pm = model_options.get(api_provider, model_options['groq'])
            current_model = st.session_state.config.get('api_model', pm['default'])
            try:
                cur_idx = pm['models'].index(current_model)
            except ValueError:
                cur_idx = 0
            selected_name = st.selectbox("Model", pm['names'], index=cur_idx)
            selected_model = pm['models'][pm['names'].index(selected_name)]
            st.session_state.config['api_model'] = selected_model

            tips = {
                'groq':    ('Groq',      'Ultra-fast · 250K tokens/min · free', 'GROQ_API_KEY',    'https://console.groq.com/keys'),
                'gemini':  ('Gemini',    '1M context · 1500 req/day · free',     'GEMINI_API_KEY',  'https://aistudio.google.com/app/apikey'),
                'ollama':  ('Ollama',    'Local · fully private · no key needed', None,              'https://ollama.com'),
                'together':('Together', 'Cloud alternative',                       'TOGETHER_API_KEY','https://api.together.xyz/signup'),
            }
            name, desc, env_var, url = tips.get(api_provider, ('', '', None, ''))
            st.markdown(f'<div class="alert alert-info"><strong>{name}</strong> — {desc}<br><small>Docs: <a href="{url}" target="_blank">{url}</a></small></div>', unsafe_allow_html=True)
            if env_var:
                st.code(f'{env_var}=your-key-here  # add to .env', language="bash")
        else:
            st.markdown('<div class="alert alert-warn">Template mode active — basic output, no LLM.</div>', unsafe_allow_html=True)
            st.session_state.config['use_llm'] = False
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-title">Storage</div>', unsafe_allow_html=True)
        db_path = st.text_input("SQLite database path", value=st.session_state.config.get('database', 'watcher.db'))
        st.session_state.config['database'] = db_path
        chroma_dir = st.text_input("ChromaDB directory", value=st.session_state.config.get('chroma_persist_dir', 'chroma_data'))
        st.session_state.config['chroma_persist_dir'] = chroma_dir
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">Relevance Filter</div>', unsafe_allow_html=True)
        filter_threshold = st.slider("Threshold", min_value=0.0, max_value=1.0,
            value=st.session_state.config.get('filter_threshold', 0.45), step=0.05,
            help="Lower = more articles pass through, Higher = only close matches")
        st.session_state.config['filter_threshold'] = filter_threshold
        level = "Lenient — may include loosely relevant items" if filter_threshold < 0.35 \
               else "Strict — may reject borderline relevant items" if filter_threshold > 0.65 \
               else "Balanced"
        st.markdown(f'<div style="font-size:.8rem;color:#6b7280;margin-top:4px">{level}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-title">Scheduler Frequency</div>', unsafe_allow_html=True)
        run_every = st.slider("Run every (minutes)", min_value=1, max_value=10080,
            value=st.session_state.config.get('run_every_minutes', 1440), step=1)
        st.session_state.config['run_every_minutes'] = run_every
        st.markdown(f'<div style="font-size:.8rem;color:#6b7280;margin-top:4px">Every {run_every} min &nbsp;·&nbsp; {run_every//60}h {run_every%60:02d}m</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 5: MONITORING
# ============================================================================
elif page == "Monitoring":
    st.markdown('<h2 style="font-size:1.4rem;font-weight:700;color:#2563eb;margin-bottom:4px">Monitoring</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:.875rem;margin-bottom:24px">Inspect collected data and system health.</p>', unsafe_allow_html=True)

    earliest_str = stats['earliest'][:10] if stats['earliest'] else "—"
    latest_str   = stats['latest'][:10]   if stats['latest']   else "—"
    st.markdown(f"""
<div class="stat-row">
  <div class="stat-card"><div class="label">Total Articles</div><div class="value">{stats['items']:,}</div></div>
  <div class="stat-card"><div class="label">Unique Sources</div><div class="value">{stats['sources']}</div></div>
  <div class="stat-card"><div class="label">Oldest Entry</div><div class="value" style="font-size:1rem;padding-top:6px">{earliest_str}</div></div>
  <div class="stat-card"><div class="label">Latest Entry</div><div class="value" style="font-size:1rem;padding-top:6px">{latest_str}</div></div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Recent Articles</div>', unsafe_allow_html=True)
    db_path = st.session_state.config.get('database', 'watcher.db')
    if Path(db_path).exists():
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT title, source, published, summary FROM items ORDER BY published DESC LIMIT 20")
            items = c.fetchall()
            conn.close()
            if items:
                for i, (title, source, published, summary) in enumerate(items, 1):
                    with st.expander(f"{title[:90] if title else 'Untitled'} — {source}"):
                        col_a, col_b = st.columns(2)
                        col_a.markdown(f'<span style="font-size:.8rem;color:#6b7280">Published</span><br><b>{published}</b>', unsafe_allow_html=True)
                        col_b.markdown(f'<span style="font-size:.8rem;color:#6b7280">Source</span><br><b>{source}</b>', unsafe_allow_html=True)
                        if summary:
                            st.markdown(f'<p style="font-size:.875rem;color:#374151;margin-top:10px">{summary[:400]}...</p>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#9ca3af;font-size:.875rem">No items yet. Run the pipeline to collect articles.</span>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error reading database: {e}")
    else:
        st.markdown('<div class="alert alert-warn">Database not found. Run the collector first.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">System Health</div>', unsafe_allow_html=True)
    config_ok = Path("config.yaml").exists()
    env_ok    = Path(".env").exists()
    db_ok     = Path(db_path).exists()
    def _badge(ok): return '<span class="badge badge-green">OK</span>' if ok else '<span class="badge badge-red">Missing</span>'
    st.markdown(f"""
<div style="font-size:.875rem;line-height:2.4;color:#374151;">
  <div style="display:flex;justify-content:space-between;max-width:320px"><span>config.yaml</span>{_badge(config_ok)}</div>
  <div style="display:flex;justify-content:space-between;max-width:320px"><span>.env (API keys)</span>{_badge(env_ok)}</div>
  <div style="display:flex;justify-content:space-between;max-width:320px"><span>SQLite database</span>{_badge(db_ok)}</div>
</div>
""", unsafe_allow_html=True)
    try:
        import feedparser, chromadb
        st.markdown(f"""
<div style="font-size:.875rem;line-height:2.4;color:#374151;margin-top:8px;">
  <div style="display:flex;justify-content:space-between;max-width:320px"><span>feedparser</span>{_badge(True)}</div>
  <div style="display:flex;justify-content:space-between;max-width:320px"><span>chromadb</span>{_badge(True)}</div>
</div>
""", unsafe_allow_html=True)
    except ImportError as e:
        st.markdown(f'<div class="alert alert-error">Missing dependency: {e}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    

