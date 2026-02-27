#!/usr/bin/env python3
"""
Full pipeline demo - execute complete watch system with LangChain orchestration
Collector → Filter → Analysis → Synthesizer

Usage:
    python3 run_full_pipeline.py              # Normal run
    python3 run_full_pipeline.py --clear-old  # Clear items older than 7 days before running
    python3 run_full_pipeline.py --fresh      # Clear ALL items before running (fresh start)
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Load environment variables from .env
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent))

from watcher.config import load_config
from watcher.storage.store import Storage
from watcher.storage.vector_store import VectorStore
from watcher.nlp.embeddings import EmbeddingProvider
from watcher.agents.collector import CollectorAgent
from watcher.agents.filter_agent import FilterAgent
from watcher.agents.analysis import AnalysisAgent
from watcher.agents.synthesizer import Synthesizer
from watcher.agents.langchain_orchestrator import LangChainOrchestrator
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def clear_old_items(db_path: str, days: int = 7):
    """Clear items older than specified days from database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d')
        
        # Count items before deletion
        cursor.execute("SELECT COUNT(*) FROM items WHERE published < ?", (cutoff_str,))
        count_before = cursor.fetchone()[0]
        
        if count_before > 0:
            # Delete old items
            cursor.execute("DELETE FROM items WHERE published < ?", (cutoff_str,))
            conn.commit()
            print(f"🗑️  Cleared {count_before} items older than {days} days ({cutoff_str})")
        else:
            print(f"✓ No items older than {days} days to clear")
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not clear old items: {e}")


def clear_all_items(db_path: str):
    """Clear ALL items from database for fresh start."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count items before deletion
        cursor.execute("SELECT COUNT(*) FROM items")
        count_before = cursor.fetchone()[0]
        
        if count_before > 0:
            # Delete all items
            cursor.execute("DELETE FROM items")
            conn.commit()
            print(f"🗑️  Cleared ALL {count_before} items from database (fresh start)")
        else:
            print(f"✓ Database already empty")
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not clear items: {e}")


def run_full_pipeline():
    """Execute the complete watch pipeline with LangChain orchestration."""
    
    # Check for command-line arguments
    clear_mode = None
    if '--clear-old' in sys.argv:
        clear_mode = 'old'
    elif '--fresh' in sys.argv:
        clear_mode = 'fresh'
    
    print("\n" + "="*70)
    print("🎭 LANGCHAIN-ORCHESTRATED PIPELINE")
    print("Collector → Filter → Analysis → Synthesizer")
    print("="*70)
    
    # Load configuration
    config = load_config() or {}
    topics = config.get('topics', [])
    db_path = config.get('database', 'watcher.db')
    threshold = config.get('filter_threshold', 0.65)
    
    # Clear items if requested
    if clear_mode == 'old':
        print(f"\n🧹 Clearing old items (>7 days)...")
        clear_old_items(db_path, days=7)
    elif clear_mode == 'fresh':
        print(f"\n🧹 Clearing ALL items for fresh start...")
        clear_all_items(db_path)
    
    print(f"\n📋 Configuration:")
    print(f"   Topics: {topics}")
    print(f"   Database: {db_path}")
    print(f"   Filter threshold: {threshold}")
    print(f"   Framework: LangChain")
    
    # Initialize storage and vector store
    storage = Storage(db_path)
    vector_store = VectorStore(
        collection_name="watcher",
        persist_directory=config.get('chroma_persist_dir', 'chroma_data')
    )
    provider = EmbeddingProvider()
    
    # Initialize agents
    collector = CollectorAgent(storage=storage)
    filter_agent = FilterAgent(provider=provider)
    analysis_agent = AnalysisAgent(storage=storage)
    
    use_api_llm = config.get('use_api_llm', True)
    api_provider = config.get('api_provider', 'huggingface')
    api_model = config.get('api_model', 'deepseek-ai/DeepSeek-R1:fastest')
    synthesizer = Synthesizer(use_api_llm=use_api_llm, api_provider=api_provider, api_model=api_model)
    
    # Create LangChain orchestrator
    print(f"\n🎭 Initializing LangChain Orchestrator...")
    orchestrator = LangChainOrchestrator(
        collector=collector,
        filter_agent=filter_agent,
        synthesizer=synthesizer,
        storage=storage,
        vector_store=vector_store,
        provider=provider
    )
    print("✓ Orchestrator ready")
    
    # Execute orchestrated workflow
    print(f"\n{'='*70}")
    print("EXECUTING LANGCHAIN-ORCHESTRATED WORKFLOW")
    print(f"{'='*70}\n")
    
    result = orchestrator.orchestrate(topics=topics, filter_threshold=threshold)
    
    collected_items = result['collected']
    filtered_items = result['filtered']
    novel_items = result['novel']
    
    # Run additional analysis on novel items
    if novel_items:
        print(f"\n{'='*70}")
        print("STAGE 4: DETAILED ANALYSIS (Priority & Category)")
        print(f"{'='*70}")
        
        analyzed_items = analysis_agent.analyze(novel_items, lookback_days=7)
        print(f"✓ Analyzed {len(analyzed_items)} items")
        
        # Categorize by priority
        high_priority = [i for i in analyzed_items if i.get('priority') == 'high']
        medium_priority = [i for i in analyzed_items if i.get('priority') == 'medium']
        low_priority = [i for i in analyzed_items if i.get('priority') == 'low']
        
        print(f"\n📊 Items by priority:")
        print(f"   🔴 High:   {len(high_priority)}")
        print(f"   🟡 Medium: {len(medium_priority)}")
        print(f"   🟢 Low:    {len(low_priority)}")
        
        print(f"\n📊 Items by category:")
        categories = {}
        for item in analyzed_items:
            cat = item.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {cat}: {count}")
        
        # Show top high-priority items
        if high_priority:
            print(f"\n🔴 High-priority items:")
            for item in high_priority[:3]:
                title = item.get('title', 'N/A')[:60]
                cat = item.get('category', 'Other')
                nov_score = item.get('novelty_score', 0)
                print(f"   • {title}")
                print(f"     Category: {cat}, Novelty: {nov_score:.2f}")
    else:
        analyzed_items = []
        high_priority = []
        medium_priority = []
        low_priority = []
    
    # Get synthesis report from orchestrator
    report = result['synthesis']
    
    if not report or report == "No novel items.":
        print("\n⚠️  No novel items to synthesize, generating basic report...")
        synthesis_topic = config.get('synthesis_topic', 'AI & Technology Watch')
        period = datetime.now().strftime("%Y-%m-%d")
        context = f"Monitoring: {', '.join(topics)}"
        
        report = synthesizer.synthesize(
            topic=synthesis_topic,
            period=period,
            context=context,
            items=analyzed_items if analyzed_items else filtered_items,
            db_path=db_path
        )
    
    print(f"\n✓ Generated report ({len(report)} bytes)")
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Save report with timestamp
    report_path = reports_dir / f"intelligence_report_{timestamp}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved to {report_path}")
    
    # Also save as "latest" for easy access
    latest_path = "watch_report_demo.md"
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Latest copy: {latest_path}")
    
    # Export to PDF and Word with timestamp
    print("\n📄 Exporting to PDF and Word...")
    try:
        pdf_path = reports_dir / f"intelligence_report_{timestamp}.pdf"
        synthesizer.export_to_pdf(
            note_text=report,
            output_path=str(pdf_path),
            topic=", ".join(topics[:2]),
            period="LangChain Pipeline Execution"
        )
        print(f"✓ PDF exported: {pdf_path}")
        
        # Latest PDF copy
        latest_pdf = "watch_report_demo.pdf"
        synthesizer.export_to_pdf(
            note_text=report,
            output_path=latest_pdf,
            topic=", ".join(topics[:2]),
            period="LangChain Pipeline Execution"
        )
        
        docx_path = reports_dir / f"intelligence_report_{timestamp}.docx"
        synthesizer.export_to_docx(
            note_text=report,
            output_path=str(docx_path),
            topic=", ".join(topics[:2]),
            period="LangChain Pipeline Execution"
        )
        print(f"✓ Word exported: {docx_path}")
        
        # Latest Word copy
        latest_docx = "watch_report_demo.docx"
        synthesizer.export_to_docx(
            note_text=report,
            output_path=latest_docx,
            topic=", ".join(topics[:2]),
            period="LangChain Pipeline Execution"
        )
    except Exception as e:
        print(f"⚠ Export failed (optional): {e}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print("🎭 LANGCHAIN PIPELINE SUMMARY")
    print(f"{'='*70}")
    print(f"\nOrchestrated Flow:")
    print(f"  Collected:  {len(collected_items):3d} items")
    print(f"  Filtered:   {len(filtered_items):3d} items (relevant)")
    print(f"  Novel:      {len(novel_items):3d} items (unique)")
    if analyzed_items:
        print(f"  Analyzed:   {len(analyzed_items):3d} items")
        print(f"    ├─ High:    {len(high_priority):3d}")
        print(f"    ├─ Medium:  {len(medium_priority):3d}")
        print(f"    └─ Low:     {len(low_priority):3d}")
    
    print(f"\nReport: {len(report)} bytes generated")
    print(f"Topics: {len(topics)} monitored")
    print(f"Threshold: {threshold}")
    print(f"Framework: LangChain {result['cycle_id']}")
    print(f"\nReports saved to:")
    print(f"  • reports/intelligence_report_{timestamp}.{{md,pdf,docx}}")
    print(f"  • watch_report_demo.{{md,pdf,docx}} (latest)")
    
    print(f"\n{'='*70}")
    print("✓ LANGCHAIN PIPELINE COMPLETE")
    print(f"{'='*70}\n")
    
    storage.close()


if __name__ == "__main__":
    run_full_pipeline()
