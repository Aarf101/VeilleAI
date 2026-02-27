"""LangChain-based Multi-Agent Orchestrator"""
from typing import List, Dict
from datetime import datetime
import os

class LangChainOrchestrator:
    """LangChain-powered orchestrator."""
    
    def __init__(self, collector=None, filter_agent=None, synthesizer=None, 
                 storage=None, vector_store=None, provider=None):
        self.collector = collector
        self.filter_agent = filter_agent
        self.synthesizer = synthesizer
        self.storage = storage
        self.vector_store = vector_store
        self.provider = provider
        
        try:
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                api_key=os.getenv('GROQ_API_KEY'),
                model_name="deepseek-r1-distill-llama-70b"
            )
        except:
            self.llm = None
    
    def orchestrate(self, topics: List[str], filter_threshold: float = 0.65) -> Dict:
        """Execute workflow."""
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n{'='*70}")
        print(f"🎭 LangChain Orchestrator - {cycle_id}")
        print(f"{'='*70}\n")
        
        # Collect
        print("1️⃣  COLLECTING...")
        collected = self.collector.collect_new() if self.collector else []
        print(f"   ✓ {len(collected)} items\n")
        
        if not collected:
            # Fallback: use recent items from DB instead of returning empty
            if self.storage:
                print("   ⚠️ No new items collected. Falling back to recent items from DB...")
                recent = self.storage.get_recent_items_full(limit=100)
                if recent:
                    collected = recent
                    print(f"   ✓ Using {len(collected)} recent items from DB\n")
                else:
                    return {'cycle_id': cycle_id, 'collected': [], 'filtered': [],
                           'novel': [], 'synthesis': "No items."}
            else:
                return {'cycle_id': cycle_id, 'collected': [], 'filtered': [],
                       'novel': [], 'synthesis': "No items."}
        
        # Filter
        print("2️⃣  FILTERING...")
        filtered = self.filter_agent.filter(collected, topics, filter_threshold) if self.filter_agent else collected
        print(f"   ✓ {len(filtered)} items\n")
        
        # Novelty
        print("3️⃣  NOVELTY...")
        novel_items = []
        if self.vector_store and self.provider:
            from watcher.agents.novelty_detector import is_novel_chromadb, categorize_item
            for item in filtered:
                is_novel, similarity = is_novel_chromadb(item, self.vector_store, self.provider, 0.75)
                if is_novel:
                    item['category'] = categorize_item(item)
                    novel_items.append(item)
        else:
            novel_items = filtered
        print(f"   ✓ {len(novel_items)} novel\n")
        
        # Synthesize
        print("4️⃣  SYNTHESIZING...")
        if novel_items and self.synthesizer:
            synthesis = self.synthesizer.synthesize(
                topic=", ".join(topics[:2]),
                period=cycle_id,
                context="Automated monitoring",
                items=novel_items
            )
        else:
            synthesis = "No novel items."
        print(f"   ✓ Done\n")
        
        return {'cycle_id': cycle_id, 'collected': collected, 'filtered': filtered,
                'novel': novel_items, 'synthesis': synthesis}
