#!/usr/bin/env python3
"""CLI tool for historical analysis and period comparisons.

Usage:
    python demo/history_report.py              # Show comparison (current vs previous week)
    python demo/history_report.py --weeks 4    # Show 4-week report
    python demo/history_report.py --compare    # Show detailed comparison
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure project root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watcher.analysis.history import HistoricalAnalyzer
from watcher.config import load_config


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def show_comparison():
    """Show current vs previous period comparison."""
    cfg = load_config() or {'database': 'watcher.db'}
    db_path = cfg.get('database', 'watcher.db')
    
    analyzer = HistoricalAnalyzer(db_path)
    comparison = analyzer.compare_periods(current_days=7, previous_days=7)
    
    print_section("COMPARAISON SEMAINE ACTUELLE vs PRÉCÉDENTE")
    
    print(f"\nPériode actuelle:")
    print(f"  Articles: {comparison['current']['item_count']}")
    print(f"  Sources: {comparison['current']['sources']}")
    
    print(f"\nPériode précédente:")
    print(f"  Articles: {comparison['previous']['item_count']}")
    print(f"  Sources: {comparison['previous']['sources']}")
    
    print(f"\nTendance: {comparison['trend']}")
    print(f"Croissance: {comparison['growth_percent']:+.1f}%")


def show_weekly_report(weeks=4):
    """Show week-by-week report."""
    cfg = load_config() or {'database': 'watcher.db'}
    db_path = cfg.get('database', 'watcher.db')
    
    analyzer = HistoricalAnalyzer(db_path)
    
    print_section(f"RAPPORT HISTORIQUE ({weeks} DERNIÈRES SEMAINES)")
    
    report = analyzer.generate_historical_report(weeks=weeks)
    print(f"\n{report}")


def show_period_summary(days=7):
    """Show summary for a specific period."""
    cfg = load_config() or {'database': 'watcher.db'}
    db_path = cfg.get('database', 'watcher.db')
    
    analyzer = HistoricalAnalyzer(db_path)
    
    now = datetime.now(timezone.utc)
    end_date = now
    start_date = now - timedelta(days=days)
    
    summary = analyzer.get_date_range_summary(start_date, end_date)
    
    print_section(f"RÉSUMÉ DE PÉRIODE ({days} JOURS)")
    
    print(f"\nPériode: {summary['period']}")
    print(f"Articles: {summary['item_count']}")
    print(f"Sources: {summary['source_count']}")
    print(f"\nRésumé: {summary['summary']}")
    
    if summary.get('first_item'):
        print(f"\nPremier article: {summary['first_item']}")
        print(f"Dernier article: {summary['last_item']}")
    
    if summary.get('sources'):
        print(f"\nSources:")
        for source in summary['sources'][:5]:
            print(f"  • {source}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Historical analysis tool')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks for report (default: 4)')
    parser.add_argument('--compare', action='store_true', help='Show detailed comparison')
    parser.add_argument('--period', type=int, default=7, help='Days for period summary (default: 7)')
    
    args = parser.parse_args()
    
    if args.compare:
        show_comparison()
    else:
        show_weekly_report(weeks=args.weeks)
        print("\n")
        show_period_summary(days=args.period)
    
    print("\n")
