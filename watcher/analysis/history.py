"""Historical analysis module for period-based summarization and comparison.

Provides:
- Period-based item retrieval
- Previous period context
- Period-to-period comparison
- Historical trend analysis
"""
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import sqlite3
from email.utils import parsedate_to_datetime


class HistoricalAnalyzer:
    """Analyze items across time periods."""
    
    def __init__(self, db_path: str = "watcher.db"):
        self.db_path = db_path
    
    def _parse_rfc_date(self, date_str: str) -> Optional[datetime]:
        """Parse RFC date string to datetime."""
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return None
    
    def get_period_items(self, days: int = 7, end_date: Optional[datetime] = None) -> List[Dict]:
        """Get items from a specific period (last N days)."""
        if end_date is None:
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
        
        start_date = end_date - timedelta(days=days)
        
        # Make sure both dates are timezone-aware
        if end_date.tzinfo is None:
            from datetime import timezone
            end_date = end_date.replace(tzinfo=timezone.utc)
        if start_date.tzinfo is None:
            from datetime import timezone
            start_date = start_date.replace(tzinfo=timezone.utc)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all items and filter by date in Python
        c.execute("SELECT * FROM items WHERE published IS NOT NULL ORDER BY id DESC")
        
        items = []
        for row in c.fetchall():
            item = dict(row)
            pub_date = self._parse_rfc_date(item.get('published'))
            if pub_date and start_date <= pub_date <= end_date:
                items.append(item)
        
        conn.close()
        return items
    
    def get_previous_period_summary(self, current_period_days: int = 7) -> Dict:
        """Generate summary of previous period for context."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        prev_end = now - timedelta(days=current_period_days)
        prev_start = prev_end - timedelta(days=current_period_days)
        
        items = self._get_items_in_range(prev_start, prev_end)
        
        if not items:
            return {
                'period': f"{prev_start.strftime('%Y-%m-%d')} to {prev_end.strftime('%Y-%m-%d')}",
                'item_count': 0,
                'sources': 0,
                'summary': 'Aucune donnée disponible pour la période précédente.'
            }
        
        # Analyze previous period
        sources = set(item.get('source', 'Unknown') for item in items)
        
        return {
            'period': f"{prev_start.strftime('%Y-%m-%d')} to {prev_end.strftime('%Y-%m-%d')}",
            'item_count': len(items),
            'sources': len(sources),
            'summary': self._build_period_summary(items),
            'top_titles': [item.get('title', '')[:80] for item in items[:3]]
        }
    
    def compare_periods(self, current_days: int = 7, previous_days: int = 7) -> Dict:
        """Compare current period with previous period."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Current period
        current_items = self.get_period_items(days=current_days, end_date=now)
        
        # Previous period
        prev_end = now - timedelta(days=current_days)
        prev_start = prev_end - timedelta(days=previous_days)
        prev_items = self._get_items_in_range(prev_start, prev_end)
        
        return {
            'current': {
                'period_days': current_days,
                'item_count': len(current_items),
                'sources': len(set(item.get('source') for item in current_items)),
            },
            'previous': {
                'period_days': previous_days,
                'item_count': len(prev_items),
                'sources': len(set(item.get('source') for item in prev_items)),
            },
            'trend': self._calculate_trend(len(current_items), len(prev_items)),
            'growth_percent': round(((len(current_items) - len(prev_items)) / max(len(prev_items), 1)) * 100, 1)
        }
    
    def get_date_range_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get detailed summary for a specific date range."""
        items = self._get_items_in_range(start_date, end_date)
        
        if not items:
            return {
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'item_count': 0,
                'source_count': 0,
                'summary': 'Aucun article trouvé pour cette période.'
            }
        
        sources = set(item.get('source', 'Unknown') for item in items)
        
        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'item_count': len(items),
            'sources': list(sources),
            'source_count': len(sources),
            'summary': self._build_period_summary(items),
            'first_item': items[0].get('published', '') if items else None,
            'last_item': items[-1].get('published', '') if items else None,
        }
    
    def _get_items_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Helper to get items in a date range (parses RFC dates)."""
        from datetime import timezone
        
        # Make sure both dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all items and filter by date in Python (since dates are RFC strings)
        c.execute("SELECT * FROM items WHERE published IS NOT NULL ORDER BY id DESC")
        
        items = []
        for row in c.fetchall():
            item = dict(row)
            pub_date = self._parse_rfc_date(item.get('published'))
            if pub_date and start_date <= pub_date <= end_date:
                items.append(item)
        
        conn.close()
        return items
    
    def _build_period_summary(self, items: List[Dict]) -> str:
        """Generate rich text summary of period for better context."""
        if not items:
            return "Aucun article."
        
        sources = set(item.get('source', 'Unknown') for item in items)
        
        # Find most common keywords with better analysis
        keywords = {}
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('summary', '')).lower()
            # Expanded keyword list for better theme detection
            for keyword in ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 
                          'llm', 'large language model', 'generative ai', 'gpt', 'chatgpt',
                          'technology', 'innovation', 'cloud', 'data', 'model', 'agent',
                          'deployment', 'production', 'optimization', 'performance']:
                if keyword in text:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Build enriched summary
        summary_parts = []
        summary_parts.append(f"{len(items)} articles collectés")
        summary_parts.append(f"{len(sources)} sources différentes")
        
        # Add top themes
        if keywords:
            top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]
            themes = ", ".join([kw.title() for kw, _ in top_keywords])
            summary_parts.append(f"Thèmes principaux: {themes}")
        
        # Add top sources
        source_counts = {}
        for item in items:
            src = item.get('source', 'Unknown')
            source_counts[src] = source_counts.get(src, 0) + 1
        
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        sources_str = ", ".join([src for src, _ in top_sources])
        summary_parts.append(f"Sources principales: {sources_str}")
        
        # Sample key titles
        if len(items) >= 2:
            sample_titles = [item.get('title', '')[:60] + "..." for item in items[:2]]
            summary_parts.append(f"Exemples: \"{sample_titles[0]}\", \"{sample_titles[1]}\"")
        
        return ". ".join(summary_parts) + "."
    
    def _calculate_trend(self, current: int, previous: int) -> str:
        """Calculate trend direction."""
        if current > previous:
            return "↑ En hausse"
        elif current < previous:
            return "↓ En baisse"
        else:
            return "→ Stable"
    
    def _get_items_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all items within date range (parses RFC dates)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all items and filter by date in Python
        c.execute("SELECT * FROM items WHERE published IS NOT NULL ORDER BY id DESC")
        
        items = []
        for row in c.fetchall():
            item = dict(row)
            pub_date = self._parse_rfc_date(item.get('published'))
            if pub_date and start_date <= pub_date <= end_date:
                items.append(item)
        
        conn.close()
        return items
    
    def generate_historical_report(self, weeks: int = 4) -> str:
        """Generate report spanning multiple weeks."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        report_lines = []
        
        report_lines.append(f"# RAPPORT HISTORIQUE ({weeks} dernières semaines)")
        report_lines.append("")
        
        # Week by week
        for week in range(weeks, 0, -1):
            week_end = now - timedelta(days=(week-1)*7)
            week_start = week_end - timedelta(days=7)
            
            week_data = self.get_date_range_summary(week_start, week_end)
            report_lines.append(f"## Semaine {week}")
            report_lines.append(f"Période: {week_data['period']}")
            report_lines.append(f"Articles: {week_data['item_count']}")
            report_lines.append(f"Sources: {week_data['source_count']}")
            report_lines.append(f"Résumé: {week_data['summary']}")
            report_lines.append("")
        
        # Overall comparison
        comparison = self.compare_periods(current_days=7, previous_days=7)
        report_lines.append("## ANALYSE COMPARATIVE")
        report_lines.append(f"Semaine actuelle vs précédente: {comparison['trend']}")
        report_lines.append(f"Croissance: {comparison['growth_percent']:+.1f}%")
        report_lines.append(f"Items: {comparison['current']['item_count']} vs {comparison['previous']['item_count']}")
        
        return "\n".join(report_lines)
