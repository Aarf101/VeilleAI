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
from datetime import datetime
import glob

# Page config
st.set_page_config(
    page_title="Veille Config",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .config-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        color: #856404;
    }
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
    st.success("✅ Configuration saved!")


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

# Header
col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.title("⚙️ Veille Configuration")
    st.markdown("_Automated AI Monitoring System_")
with col2:
    st.markdown("### Status")
    stats = get_db_stats()
    st.metric("Items Collected", stats['items'])
    st.metric("Sources", stats['sources'])

st.divider()

# Sidebar navigation
page = st.sidebar.radio(
    "Configuration Sections",
    ["📊 Dashboard", "▶️ Run Pipeline", "⏰ Scheduler", "🎯 Topics", "📡 Data Sources", "🔧 Advanced", "📈 Monitoring"]
)

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================
if page == "📊 Dashboard":
    st.header("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", stats['items'])
    with col2:
        st.metric("Data Sources", stats['sources'])
    with col3:
        st.metric("Topics Monitored", len(st.session_state.config.get('topics', [])))
    with col4:
        st.metric("Feeds Configured", len(st.session_state.config.get('feeds', [])))
    
    st.divider()
    
    st.subheader("Current Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Topics:**")
        for topic in st.session_state.config.get('topics', []):
            st.write(f"- {topic}")
    
    with col2:
        st.write("**Feed URLs:**")
        for feed in st.session_state.config.get('feeds', []):
            st.write(f"- {feed}")
    
    st.divider()
    
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Run Full Pipeline", use_container_width=True, type="primary"):
            st.switch_page = "▶️ Run Pipeline"
            st.info("👉 Switch to 'Run Pipeline' page to execute the system")
    
    with col2:
        if st.button("⏰ Start Background Scheduler", use_container_width=True):
            st.info(f"""
**To run scheduler in background:**

```bash
# Option 1: Using APScheduler (recommended)
source load_env.sh
python3 -c "from watcher.scheduler import start_scheduler; start_scheduler()" &

# Option 2: Simple scheduler  
python3 scheduler_agent.py &
```

The scheduler will run the pipeline every {st.session_state.config.get('run_every_minutes', 1440)} minutes.
Check with: `ps aux | grep scheduler`
            """)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 View Latest Report", use_container_width=True):
            if Path("watch_report_demo.md").exists():
                with open("watch_report_demo.md", 'r') as f:
                    st.markdown(f.read())
            else:
                st.warning("No report found. Run the pipeline first.")
    
    with col2:
        if st.button("🔍 Check Scheduler Status", use_container_width=True):
            import subprocess
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            scheduler_running = "scheduler" in result.stdout or "APScheduler" in result.stdout
            
            if scheduler_running:
                st.success("✅ Scheduler is running")
            else:
                st.warning("⚠️ Scheduler is NOT running - start it manually")
    
    # Historical reports section
    st.divider()
    st.subheader("📚 Historical Reports")
    
    reports_dir = Path("reports")
    if reports_dir.exists():
        # Find all timestamped reports
        report_files = sorted(glob.glob(str(reports_dir / "intelligence_report_*.md")), reverse=True)
        
        if report_files:
            st.info(f"Found {len(report_files)} archived reports")
            
            # Display reports in expandable sections
            for report_file in report_files[:10]:  # Show last 10 reports
                report_path = Path(report_file)
                timestamp = report_path.stem.replace("intelligence_report_", "")
                
                # Parse timestamp for display
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%B %d, %Y at %I:%M:%S %p")
                except:
                    display_time = timestamp
                
                with st.expander(f"📄 Report from {display_time}"):
                    with open(report_file, 'r') as f:
                        st.markdown(f.read())
                    
                    # Download buttons for this report
                    col1, col2, col3 = st.columns(3)
                    
                    base_name = report_path.stem
                    pdf_file = reports_dir / f"{base_name}.pdf"
                    docx_file = reports_dir / f"{base_name}.docx"
                    
                    with col1:
                        with open(report_file, 'r') as f:
                            st.download_button(
                                "📄 Markdown",
                                data=f.read(),
                                file_name=f"{base_name}.md",
                                mime="text/markdown",
                                key=f"md_{timestamp}"
                            )
                    
                    with col2:
                        if pdf_file.exists():
                            with open(pdf_file, 'rb') as f:
                                st.download_button(
                                    "📕 PDF",
                                    data=f.read(),
                                    file_name=f"{base_name}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_{timestamp}"
                                )
                    
                    with col3:
                        if docx_file.exists():
                            with open(docx_file, 'rb') as f:
                                st.download_button(
                                    "📘 Word",
                                    data=f.read(),
                                    file_name=f"{base_name}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"docx_{timestamp}"
                                )
        else:
            st.info("No archived reports yet. Reports will appear here after pipeline runs.")
    else:
        st.info("No reports folder found. Run the pipeline to generate reports.")


# ============================================================================
# PAGE 2: RUN PIPELINE
# ============================================================================
elif page == "▶️ Run Pipeline":
    st.header("Execute Pipeline")
    st.markdown("_Run the complete multi-agent workflow from this interface_")
    
    st.divider()
    
    # Pipeline configuration
    st.subheader("Pipeline Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        clear_db = st.checkbox("Clear database before running", value=False, 
                              help="Remove old data to re-collect everything fresh")
    with col2:
        show_logs = st.checkbox("Show detailed logs", value=True)
    
    st.divider()
    
    # Run button
    if st.button("▶️ START PIPELINE", type="primary", use_container_width=True):
        import subprocess
        import os
        
        with st.spinner("Running pipeline..."):
            # Prepare command
            if clear_db and Path("watcher.db").exists():
                os.remove("watcher.db")
                st.success("✅ Database cleared")
            
            # Run pipeline
            try:
                env = os.environ.copy()
                # Load .env file
                if Path(".env").exists():
                    with open(".env") as f:
                        for line in f:
                            if line.strip() and not line.startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env[key] = value
                
                result = subprocess.run(
                    ["python3", "run_full_pipeline.py"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300
                )
                
                if result.returncode == 0:
                    st.success("✅ Pipeline completed successfully!")
                    
                    if show_logs:
                        st.subheader("Pipeline Output")
                        st.code(result.stdout, language="text")
                    
                    # Show results
                    st.divider()
                    st.subheader("📊 Results")
                    
                    # Parse output for stats
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Collected:' in line:
                            st.metric("Items Collected", line.split(':')[1].strip().split()[0])
                        if 'Filtered:' in line:
                            st.metric("Items Filtered", line.split(':')[1].strip().split()[0])
                    
                    # Show report
                    if Path("watch_report_demo.md").exists():
                        st.divider()
                        st.subheader("📝 Generated Report")
                        with open("watch_report_demo.md", 'r') as f:
                            report = f.read()
                            st.markdown(report)
                        
                        # Download buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button(
                                "📄 Download Markdown",
                                data=report,
                                file_name="intelligence_report.md",
                                mime="text/markdown"
                            )
                        with col2:
                            if Path("watch_report_demo.pdf").exists():
                                with open("watch_report_demo.pdf", 'rb') as f:
                                    st.download_button(
                                        "📕 Download PDF",
                                        data=f.read(),
                                        file_name="intelligence_report.pdf",
                                        mime="application/pdf"
                                    )
                        with col3:
                            if Path("watch_report_demo.docx").exists():
                                with open("watch_report_demo.docx", 'rb') as f:
                                    st.download_button(
                                        "📘 Download Word",
                                        data=f.read(),
                                        file_name="intelligence_report.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                else:
                    st.error(f"❌ Pipeline failed with exit code {result.returncode}")
                    st.code(result.stderr, language="text")
                    
            except subprocess.TimeoutExpired:
                st.error("❌ Pipeline timed out after 5 minutes")
            except Exception as e:
                st.error(f"❌ Error running pipeline: {e}")
    
    st.divider()
    
    # Status
    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        api_key_set = Path(".env").exists() and "GROQ_API_KEY" in open(".env").read()
        st.metric("Groq API Key", "✅ Set" if api_key_set else "❌ Missing")
    
    with col2:
        db_exists = Path("watcher.db").exists()
        st.metric("Database", "✅ Exists" if db_exists else "⚪ Empty")
    
    with col3:
        config_valid = len(st.session_state.config.get('feeds', [])) > 0
        st.metric("RSS Feeds", "✅ Configured" if config_valid else "⚠️ None")


# ============================================================================
# PAGE 3: SCHEDULER MANAGEMENT
# ============================================================================
elif page == "⏰ Scheduler":
    st.header("Scheduler Management")
    st.markdown("_Start, stop, and monitor the automatic pipeline scheduler_")
    
    st.divider()
    
    # Check scheduler status
    def check_scheduler_running():
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "start_scheduler" in result.stdout
        except:
            return False
    
    def get_scheduler_pid():
        try:
            result = subprocess.run(
                ["pgrep", "-f", "start_scheduler"],
                capture_output=True,
                text=True,
                timeout=5
            )
            pids = result.stdout.strip().split('\n')
            return [p for p in pids if p]
        except:
            return []
    
    is_running = check_scheduler_running()
    scheduler_pids = get_scheduler_pid()
    
    # Status display
    st.subheader("📊 Scheduler Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_text = "🟢 Running" if is_running else "🔴 Stopped"
        st.metric("Status", status_text)
    
    with col2:
        interval = st.session_state.config.get('run_every_minutes', 1440)
        hours = interval / 60
        st.metric("Interval", f"{hours:.1f} hours")
    
    with col3:
        st.metric("Active PIDs", len(scheduler_pids))
    
    st.divider()
    
    # Control buttons
    st.subheader("🎮 Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Scheduler", disabled=is_running, use_container_width=True):
            try:
                # Start scheduler in background
                subprocess.Popen(
                    [
                        "/bin/bash", "-c",
                        f"cd {Path.cwd()} && . .venv/bin/activate && nohup python3 -c 'from watcher.scheduler import start_scheduler; start_scheduler()' > scheduler.log 2>&1 &"
                    ],
                    start_new_session=True
                )
                st.success("✅ Scheduler started! Running in background.")
                st.info("💡 The scheduler will run the full pipeline immediately, then every " + 
                       f"{interval} minutes ({hours:.1f} hours).")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to start scheduler: {e}")
    
    with col2:
        if st.button("⏸️ Stop Scheduler", disabled=not is_running, use_container_width=True):
            try:
                for pid in scheduler_pids:
                    subprocess.run(["kill", pid], timeout=5)
                st.success("✅ Scheduler stopped!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to stop scheduler: {e}")
    
    with col3:
        if st.button("🔄 Restart Scheduler", disabled=not is_running, use_container_width=True):
            try:
                # Stop
                for pid in scheduler_pids:
                    subprocess.run(["kill", pid], timeout=5)
                import time
                time.sleep(2)
                # Start
                subprocess.Popen(
                    [
                        "/bin/bash", "-c",
                        f"cd {Path.cwd()} && . .venv/bin/activate && nohup python3 -c 'from watcher.scheduler import start_scheduler; start_scheduler()' > scheduler.log 2>&1 &"
                    ],
                    start_new_session=True
                )
                st.success("✅ Scheduler restarted!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to restart scheduler: {e}")
    
    st.divider()
    
    # Logs viewer
    st.subheader("📜 Scheduler Logs")
    
    log_file = Path("scheduler.log")
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = f.read()
            
            # Show last 50 lines
            log_lines = logs.split('\n')
            recent_logs = '\n'.join(log_lines[-50:])
            
            st.code(recent_logs, language="text", line_numbers=False)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear Logs"):
                    open(log_file, 'w').close()
                    st.success("✅ Logs cleared!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading logs: {e}")
    else:
        st.info("No logs yet. Start the scheduler to see logs.")
    
    st.divider()
    
    # Configuration
    st.subheader("⚙️ Scheduler Settings")
    st.info(f"💡 Current interval: **{interval} minutes** ({hours:.1f} hours)")
    st.markdown("To change the interval, go to **🔧 Advanced** → Scheduler Frequency")
    
    # Systemd service option
    st.divider()
    st.subheader("🔧 Production Deployment")
    st.markdown("""
    For production use, install as a systemd service (survives reboots):
    
    ```bash
    ./install_scheduler_service.sh
    sudo systemctl status agenticnotes-scheduler
    sudo systemctl stop agenticnotes-scheduler
    sudo systemctl start agenticnotes-scheduler
    ```
    """)


# ============================================================================
# PAGE 4: TOPICS MANAGEMENT
# ============================================================================
elif page == "🎯 Topics":
    st.header("Topic Management")
    st.markdown("_Configure topics the system will monitor and filter by_")
    
    st.divider()
    
    topics = st.session_state.config.get('topics', [])
    
    st.subheader("Current Topics")
    if topics:
        for i, topic in enumerate(topics):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.write(f"**{i+1}. {topic}**")
            with col2:
                if st.button("❌", key=f"del_topic_{i}", use_container_width=True):
                    topics.pop(i)
                    st.session_state.config['topics'] = topics
                    st.rerun()
    else:
        st.info("No topics configured yet.")
    
    st.divider()
    
    st.subheader("Add New Topic")
    new_topic = st.text_input(
        "Enter topic name",
        placeholder="e.g., 'machine learning', 'blockchain', 'quantum computing'"
    )
    
    if st.button("➕ Add Topic", use_container_width=True):
        if new_topic and new_topic not in topics:
            topics.append(new_topic)
            st.session_state.config['topics'] = topics
            st.rerun()
        elif new_topic in topics:
            st.warning("This topic already exists!")
    
    st.divider()
    
    st.subheader("Preset Topic Groups")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 AI/ML Focus", use_container_width=True):
            st.session_state.config['topics'] = [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "neural networks",
                "generative AI"
            ]
            st.rerun()
    
    with col2:
        if st.button("💻 Tech General", use_container_width=True):
            st.session_state.config['topics'] = [
                "software development",
                "programming",
                "technology innovation",
                "web development",
                "cloud computing"
            ]
            st.rerun()
    
    with col3:
        if st.button("🔐 Security Focus", use_container_width=True):
            st.session_state.config['topics'] = [
                "cybersecurity",
                "data protection",
                "privacy",
                "encryption",
                "threat detection"
            ]
            st.rerun()
    
    st.divider()
    
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 3: DATA SOURCES
# ============================================================================
elif page == "📡 Data Sources":
    st.header("Data Source Configuration")
    st.markdown("_Manage RSS feeds and API sources_")
    
    st.divider()
    
    # RSS Feeds section
    st.subheader("RSS Feeds")
    feeds = st.session_state.config.get('feeds', [])
    
    if feeds:
        st.write("**Configured Feeds:**")
        for i, feed in enumerate(feeds):
            col1, col2, col3 = st.columns([0.7, 0.2, 0.1])
            with col1:
                st.caption(feed)
            with col2:
                priority = st.selectbox(
                    "Priority",
                    ["High", "Medium", "Low"],
                    key=f"priority_{i}",
                    label_visibility="collapsed"
                )
            with col3:
                if st.button("🗑️", key=f"del_feed_{i}"):
                    feeds.pop(i)
                    st.session_state.config['feeds'] = feeds
                    st.rerun()
    else:
        st.info("No RSS feeds configured yet.")
    
    st.divider()
    
    st.subheader("Add RSS Feed")
    new_feed = st.text_input(
        "Feed URL",
        placeholder="https://example.com/rss",
        label_visibility="collapsed"
    )
    
    if st.button("➕ Add Feed", use_container_width=True):
        if new_feed and new_feed.startswith('http') and new_feed not in feeds:
            feeds.append(new_feed)
            st.session_state.config['feeds'] = feeds
            st.rerun()
        elif new_feed in feeds:
            st.warning("This feed already exists!")
        elif new_feed:
            st.warning("Please enter a valid URL starting with http")
    
    st.divider()
    
    st.subheader("Preset Feed Collections")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 AI News Feeds", use_container_width=True):
            st.session_state.config['feeds'] = [
                "https://news.ycombinator.com/rss",
                "https://www.artificialintelligence-news.com/feed/",
                "https://venturebeat.com/category/ai/feed/",
                "https://techcrunch.com/category/artificial-intelligence/feed/"
            ]
            st.rerun()
    
    with col2:
        if st.button("💻 Tech News Feeds", use_container_width=True):
            st.session_state.config['feeds'] = [
                "https://news.ycombinator.com/rss",
                "https://techcrunch.com/feed/",
                "https://www.theverge.com/rss/index.xml",
                "https://arstechnica.com/feed/"
            ]
            st.rerun()
    
    st.divider()
    
    # Max items per feed
    st.subheader("Collection Settings")
    max_items = st.slider(
        "Max items per feed per collection",
        min_value=1,
        max_value=50,
        value=st.session_state.config.get('max_items_per_feed', 10),
        help="Higher values = more data but slower collection"
    )
    st.session_state.config['max_items_per_feed'] = max_items
    
    st.divider()
    
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 4: ADVANCED SETTINGS
# ============================================================================
elif page == "🔧 Advanced":
    st.header("Advanced Configuration")
    st.markdown("_Fine-tune filtering, synthesis, and scheduling_")
    
    st.divider()
    
    # Scheduler settings
    st.subheader("🕐 Scheduler")
    run_every = st.slider(
        "Run collection every (minutes)",
        min_value=15,
        max_value=10080,
        value=st.session_state.config.get('run_every_minutes', 1440),
        step=15,
        help="1440 min = 24 hours (daily). 60 min = hourly"
    )
    st.session_state.config['run_every_minutes'] = run_every
    st.caption(f"⏱️ Collection will run every {run_every} minutes ({run_every//60}h {run_every%60}m)")
    
    st.divider()
    
    # Synthesis settings
    st.subheader("🤖 Synthesis Configuration")
    
    use_api = st.checkbox(
        "Use API-based LLM (Recommended)",
        value=st.session_state.config.get('use_api_llm', True),
        help="API models provide much better quality than local models"
    )
    st.session_state.config['use_api_llm'] = use_api
    
    if use_api:
        api_provider = st.selectbox(
            "API Provider",
            ["groq", "gemini", "ollama", "together"],
            index=["groq", "gemini", "ollama", "together"].index(st.session_state.config.get('api_provider', 'groq')),
            help="Groq: GPT-OSS 120B/Llama 70B (ultra-fast, free) | Gemini: 2.0 Flash (best quality, 1M context, free) | Ollama: Local, private | Together: Alternative cloud"
        )
        st.session_state.config['api_provider'] = api_provider
        
        # Model selection - BEST FREE GEMINI MODELS (Feb 2026)
        model_options = {
            'groq': {
                'models': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
                'names': ['GPT-OSS 120B (best, 120B params)', 'Llama 3.3 70B (reliable)'],
                'default': 'openai/gpt-oss-120b'
            },
            'gemini': {
                'models': [
                    'gemini-3-flash-preview',           # Newest! Feb 2026
                    'gemini-2.5-pro',                   # Best quality
                    'gemini-2.5-flash',                 # Fast + reasoning
                    'gemini-2.0-flash',                 # Balanced
                    'gemini-2.0-flash-lite'             # Smallest/fastest
                ],
                'names': [
                    'Gemini 3 Flash (NEWEST - Feb 2026)',
                    'Gemini 2.5 Pro (best quality, reasoning)',
                    'Gemini 2.5 Flash (hybrid reasoning, 1M context)',
                    'Gemini 2.0 Flash (balanced, 1M context)',
                    'Gemini 2.0 Flash-Lite (fastest, cheapest)'
                ],
                'default': 'gemini-3-flash-preview'
            }
        }
        
        provider_models = model_options[api_provider]
        current_model = st.session_state.config.get('api_model', provider_models['default'])
        
        # Find current model index (default to 0 if not found)
        try:
            current_index = provider_models['models'].index(current_model)
        except ValueError:
            current_index = 0
        
        selected_model_name = st.selectbox(
            "Model",
            provider_models['names'],
            index=current_index,
            help="Choose the specific model to use with this provider"
        )
        
        # Map back to actual model ID
        selected_model = provider_models['models'][provider_models['names'].index(selected_model_name)]
        st.session_state.config['api_model'] = selected_model
        
        # Provider-specific info and setup instructions
        if api_provider == 'groq':
            st.info("⚡ **Groq**: Ultra-fast, 250K tokens/min free tier")
            st.markdown("**Setup:** Get free API key at https://console.groq.com/keys")
            st.markdown("**Set in .env:** `GROQ_API_KEY=your-key-here`")
        
        elif api_provider == 'gemini':
            st.info("🏆 **Gemini**: Best quality, 1M context, 1500 req/day free")
            st.markdown("**Setup:** Get free API key at https://aistudio.google.com/app/apikey")
            st.markdown("**Set in .env:** `GEMINI_API_KEY=your-key-here`")
        
        elif api_provider == 'ollama':
            st.info("🏠 **Ollama**: Run locally, fully private, no API key needed")
            st.markdown("**Setup:** `curl -fsSL https://ollama.com/install.sh | sh`")
            st.markdown("**Start:** `ollama serve && ollama pull " + selected_model.split(':')[0] + "`")
        
        else:
            st.info("☁️ **Together AI**: Alternative cloud provider")
            st.markdown("**Setup:** Get API key at https://api.together.xyz/signup")
    else:
        st.warning("⚠️ Template mode: Basic synthesis without LLM (fast but limited quality)")
        st.session_state.config['use_llm'] = False
    
    st.divider()
    
    st.subheader("📊 Filter Settings")
    filter_threshold = st.slider(
        "Relevance threshold",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.config.get('filter_threshold', 0.45),
        step=0.05,
        help="Lower = more lenient (more items), Higher = stricter (fewer items)"
    )
    st.session_state.config['filter_threshold'] = filter_threshold
    
    if filter_threshold < 0.35:
        st.caption("⚠️ Very lenient - may include less relevant items")
    elif filter_threshold > 0.65:
        st.caption("⚠️ Very strict - may filter out relevant items")
    else:
        st.caption("✅ Balanced filtering")
    
    st.divider()
    
    # Database settings
    st.subheader("💾 Database")
    db_path = st.text_input(
        "Database path",
        value=st.session_state.config.get('database', 'watcher.db')
    )
    st.session_state.config['database'] = db_path
    
    chroma_dir = st.text_input(
        "ChromaDB persistence directory",
        value=st.session_state.config.get('chroma_persist_dir', 'chroma_data'),
        help="Vector embeddings storage"
    )
    st.session_state.config['chroma_persist_dir'] = chroma_dir
    
    st.divider()
    
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        save_config_file(st.session_state.config)


# ============================================================================
# PAGE 5: MONITORING
# ============================================================================
elif page == "📈 Monitoring":
    st.header("System Monitoring")
    st.markdown("_View collected data and system health_")
    
    st.divider()
    
    # Statistics
    st.subheader("📊 Collection Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", stats['items'])
    with col2:
        st.metric("Unique Sources", stats['sources'])
    with col3:
        st.metric("Oldest Item", stats['earliest'][:10] if stats['earliest'] else "N/A")
    with col4:
        st.metric("Latest Item", stats['latest'][:10] if stats['latest'] else "N/A")
    
    st.divider()
    
    # Browse items
    st.subheader("📄 Recent Items")
    db_path = st.session_state.config.get('database', 'watcher.db')
    
    if Path(db_path).exists():
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute("""
                SELECT title, source, published, summary
                FROM items
                ORDER BY published DESC
                LIMIT 20
            """)
            items = c.fetchall()
            conn.close()
            
            if items:
                for i, (title, source, published, summary) in enumerate(items, 1):
                    with st.expander(f"{i}. {title[:80]}... ({source})"):
                        st.write(f"**Published:** {published}")
                        st.write(f"**Source:** {source}")
                        if summary:
                            st.write(f"**Summary:** {summary[:300]}...")
            else:
                st.info("No items collected yet. Run collector to fetch data.")
        except Exception as e:
            st.error(f"Error reading database: {e}")
    else:
        st.warning("Database not found. Run collector first.")
    
    st.divider()
    
    # System health
    st.subheader("🏥 System Health")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configuration Files:**")
        config_exists = Path("config.yaml").exists()
        st.write(f"- config.yaml: {'✅' if config_exists else '❌'}")
    
    with col2:
        st.write("**Dependencies:**")
        try:
            import feedparser
            import yaml
            import sqlite3
            st.write("- feedparser: ✅")
            st.write("- yaml: ✅")
            st.write("- sqlite3: ✅")
        except:
            st.write("- Missing dependencies: ❌")


# Footer
st.divider()
st.markdown("""
---LangChain Orchestrator**: Coordinates multi-agent workflow
- **Collectors**: Fetch data from RSS feeds and APIs
- **Filters**: Select items matching configured topics (semantic similarity)
- **ChromaDB**: Vector storage for novelty detection
- **Synthesizer**: Generate intelligence reports with DeepSeek R1 671B (HuggingFace) or Llama 3.3 70B (Groq)

Run in terminal:
- `source load_env.sh` - Load API keys
- `python3 run_full_pipeline.py` - Run full pipeline
- `python3 demo_langchain.py` - Test LangChain orchestrator
- `python demo/run_collectors.py` - Collect new data
- `python demo/test_agents.py` - Test all agents
- `streamlit run streamlit_app.py` - Launch this UI
""")
