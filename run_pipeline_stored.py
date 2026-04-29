#!/usr/bin/env python3
"""
Full pipeline demo using stored items
Filter → Analysis → Synthesizer (using items from database)
"""
import sys
import os
from pathlib import Path
from datetime import datetime

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
from watcher.agents.filter_agent import FilterAgent
from watcher.agents.analysis import AnalysisAgent
from watcher.agents.synthesizer import Synthesizer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_full_pipeline_with_stored():
    """Execute pipeline using already-collected items from storage."""
    
    print("\n" + "="*70)
    print("COMPLETE WATCH PIPELINE (Using Stored Items)")
    print("Filter -> Analysis -> Synthesizer")
    print("="*70)
    
    # Load configuration
    config = load_config() or {}
    topics = config.get('topics', [])
    db_path = config.get('sqlite_path', config.get('database', 'watcher.db'))
    
    print(f"\n[CONFIG] Configuration:")
    print(f"   Topics: {topics}")
    print(f"   Database: {db_path}")
    
    # Initialize storage
    storage = Storage(db_path)
    
    # ========================================
    # GET STORED ITEMS
    # ========================================
    print(f"\n{'='*70}")
    print("RETRIEVE STORED ITEMS")
    print(f"{'='*70}")
    
    # Get recent items from storage
    stored_items = storage.get_recent_items_full(limit=50)
    print(f"[OK] Retrieved {len(stored_items)} items from database")
    
    # Items are already dicts from get_recent_items_full
    collected_items = stored_items
    
    if not collected_items:
        print("No items in database, exiting...")
        storage.close()
        return
    
    # ========================================
    # STAGE 1: FILTERING (Relevance)
    # ========================================
    print(f"\n{'='*70}")
    print("STAGE 1: FILTERING (Semantic Relevance)")
    print(f"{'='*70}")
    
    filter_agent = FilterAgent()
    threshold = config.get('relevance_threshold', 0.40)  # Lower default to show full pipeline
    filtered_items = filter_agent.filter(
        collected_items, 
        topics=topics,
        threshold=threshold
    )
    print(f"[OK] Filtered to {len(filtered_items)}/{len(collected_items)} relevant items")
    
    if not filtered_items:
        print("No items passed filtering, exiting...")
        storage.close()
        return
    
    # Show filtered items summary
    print(f"\n[TOP] Highest relevance items:")
    for item in sorted(filtered_items, key=lambda x: x.get('relevance_score', 0), reverse=True)[:3]:
        title = item.get('title', 'N/A')[:60]
        score = item.get('relevance_score', 0)
        topics_matched = item.get('relevant_topics', [])
        print(f"   • {title}")
        print(f"     Score: {score:.2f}, Topics: {topics_matched}")
    
    # ========================================
    # STAGE 2: ANALYSIS (Novelty + Category)
    # ========================================
    print(f"\n{'='*70}")
    print("STAGE 2: ANALYSIS (Novelty Detection & Categorization)")
    print(f"{'='*70}")
    
    analysis_agent = AnalysisAgent(storage=storage)
    analyzed_items = analysis_agent.analyze(filtered_items, lookback_days=7)
    print(f"[OK] Analyzed {len(analyzed_items)} items")
    
    # Categorize by priority
    high_priority = [i for i in analyzed_items if i.get('priority') == 'high']
    medium_priority = [i for i in analyzed_items if i.get('priority') == 'medium']
    low_priority = [i for i in analyzed_items if i.get('priority') == 'low']
    
    print(f"\n[STATS] Items by priority:")
    print(f"   [H] High:   {len(high_priority)}")
    print(f"   [M] Medium: {len(medium_priority)}")
    print(f"   [L] Low:    {len(low_priority)}")
    
    print(f"\n[STATS] Items by category:")
    categories = {}
    for item in analyzed_items:
        cat = item.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {cat}: {count}")
    
    # Show top high-priority items
    if high_priority:
        print(f"\n[HIGH] High-priority items:")
        for item in high_priority[:3]:
            title = item.get('title', 'N/A')[:60]
            cat = item.get('category', 'Other')
            nov_score = item.get('novelty_score', 0)
            print(f"   • {title}")
            print(f"     Category: {cat}, Novelty: {nov_score:.2f}")
    
    # ========================================
    # STAGE 3: SYNTHESIS (Report Generation)
    # ========================================
    print(f"\n{'='*70}")
    print("STAGE 3: SYNTHESIS (Report Generation)")
    print(f"{'='*70}")
    
    # Load from config
    use_api_llm = config.get('use_api_llm', True)
    api_provider = config.get('api_provider', 'groq')
    api_model = config.get('api_model', 'openai/gpt-oss-120b')
    synthesizer = Synthesizer(use_api_llm=use_api_llm, api_provider=api_provider, api_model=api_model)
    synthesis_topic = config.get('synthesis_topic', 'AI & Technology Watch')
    period = "2026-02-10"  # Current date
    context = f"Monitoring: {', '.join(topics)}"
    
    report = synthesizer.synthesize(
        topic=synthesis_topic,
        period=period,
        context=context,
        items=analyzed_items,
        db_path=db_path
    )
    print(f"[OK] Generated report ({len(report)} bytes)")
    
    # Save report with intelligence_report format
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    report_path = reports_dir / f"intelligence_report_{timestamp}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[OK] Report saved to {report_path}")
    
    # Try to generate a podcast-style audio summary and save alongside the report
    try:
        from watcher.agents.podcast_agent import generate_podcast_audio
        audio_path = str(report_path).replace('.md', '.mp3')
        print(f"Generating podcast audio for report to {audio_path}...")
        script = generate_podcast_audio(report, config, audio_path)
        if script:
            print(f"[OK] Saved podcast audio: {audio_path}")
        else:
            print("Podcast audio generation failed or returned None.")
    except Exception as e:
        print(f"Podcast audio generation skipped: {e}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print("PIPELINE SUMMARY")
    print(f"{'='*70}")
    print(f"\nFlow:")
    print(f"  Retrieved:  {len(collected_items):3d} items from DB")
    print(f"  Filtered:   {len(filtered_items):3d} items (relevant)")
    print(f"  Analyzed:   {len(analyzed_items):3d} items")
    print(f"    [1] High:    {len(high_priority):3d}")
    print(f"    [2] Medium:  {len(medium_priority):3d}")
    print(f"    [3] Low:     {len(low_priority):3d}")
    
    print(f"\nReport: {len(report)} bytes generated")
    print(f"Topics: {len(topics)} monitored")
    print(f"Threshold: {threshold}")
    
    print(f"\n{'='*70}")
    print(f"[DONE] PIPELINE COMPLETE")
    print(f"{'='*70}\n")
    
    # Show first 500 chars of report
    print("REPORT PREVIEW:")
    print("-" * 70)
    print(report[:1000])
    if len(report) > 1000:
        print(f"\n... ({len(report) - 1000} more bytes)")
    print("-" * 70)
    
    storage.close()


if __name__ == "__main__":
    run_full_pipeline_with_stored()
