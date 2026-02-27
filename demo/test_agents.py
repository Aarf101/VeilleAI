"""Test script for all agents in the watcher system."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watcher import config
from watcher.storage.store import Storage
from watcher.agents.filter import filter_items
from watcher.agents.novelty_detector import is_novel, categorize_item
from watcher.agents.synthesizer import Synthesizer
from watcher.nlp.embeddings import EmbeddingProvider


def test_filtering_agent():
    print("\n" + "="*60)
    print("TEST 1: FILTERING AGENT")
    print("="*60)
    
    cfg = config.load_config()
    storage = Storage(cfg.get("database", "watcher.db"))
    print("Loading embedding model...")
    provider = EmbeddingProvider()
    
    items = storage.get_recent_items_full(5)  # Reduced from 10
    topics = cfg.get("topics", ["artificial intelligence"])
    
    print(f"\nTopics: {topics}")
    print(f"Items to filter: {len(items)}\n")
    print("Computing similarity scores...")
    
    results = filter_items(items, topics, threshold=0.30, provider=provider)  # Lowered threshold
    
    print("\n" + "-"*60)
    for item, score, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{status} Score: {score:.3f}")
        print(f"Title: {item['title']}")
        print(f"Source: {item.get('source', 'N/A')}")
    print("-"*60)
    
    passed_count = sum(1 for _, _, p in results if p)
    print(f"\n✅ Result: {passed_count}/{len(results)} items passed threshold (0.30)")
    
    return [item for item, score, passed in results if passed]


def test_novelty_detector(filtered_items):
    print("\n" + "="*60)
    print("TEST 2: NOVELTY DETECTOR")
    print("="*60)
    
    cfg = config.load_config()
    storage = Storage(cfg.get("database", "watcher.db"))
    print("Loading embedding model...")
    provider = EmbeddingProvider()
    
    novel_items = []
    
    print(f"\nTesting {len(filtered_items)} filtered items for novelty...")
    print("(Comparing against last 200 items in database)\n")
    print("-"*60)
    
    for item in filtered_items[:3]:  # Reduced to 3
        novel, similarity = is_novel(item, storage, provider=provider, sim_threshold=0.75)
        category = categorize_item(item)
        
        status = "✓ NOVEL" if novel else "✗ DUPLICATE"
        print(f"\n{status}")
        print(f"Title: {item['title']}")
        print(f"Max Similarity: {similarity:.3f} (threshold: 0.75)")
        print(f"Category: {category}")
        
        if novel:
            item['category'] = category
            novel_items.append(item)
    
    print("-"*60)
    print(f"\n✅ Result: {len(novel_items)} novel items detected")
    print(f"Note: Items already in DB will show similarity ~1.0 (exact match)")
    return novel_items


def test_synthesizer(novel_items):
    print("\n" + "="*60)
    print("TEST 3: SYNTHESIZER AGENT")
    print("="*60)
    
    cfg = config.load_config()
    model = cfg.get("synthesizer_model", "google/flan-t5-small")
    
    print(f"\nModel: {model}")
    print(f"Items to synthesize: {len(novel_items)}\n")
    
    if not novel_items:
        print("⚠ No novel items to synthesize. Using all items instead.")
        storage = Storage(cfg.get("database", "watcher.db"))
        novel_items = storage.get_recent_items_full(2)  # Reduced to 2
    
    print(f"Using Groq API for high-quality synthesis...")
    synthesizer = Synthesizer(use_api_llm=True, api_provider='groq')
    
    print("\nGenerating synthesis...")
    print("(This may take 5-10 seconds...)\n")
    
    note = synthesizer.synthesize(
        topic="Artificial Intelligence",
        period="February 7, 2026",
        context="Automated monitoring of AI developments",
        items=novel_items[:3],  # Reduced to 3
        max_new_tokens=150  # Reduced for faster generation
    )
    
    print("="*60)
    print("GENERATED SYNTHESIS NOTE:")
    print("="*60)
    print(note)
    print("="*60)
    
    print("\n⚠️  NOTE: FLAN-T5-small is too small for quality synthesis.")
    print("For better results, upgrade to 'google/flan-t5-base' in config.yaml")
    
    return note
    print("="*60)
    
    return note


def main():
    print("\n" + "█"*60)
    print("█" + " "*18 + "AGENT TESTING SUITE" + " "*21 + "█")
    print("█"*60)
    
    # Test 1: Filtering
    filtered_items = test_filtering_agent()
    
    # Test 2: Novelty Detection
    novel_items = test_novelty_detector(filtered_items if filtered_items else [])
    
    # Test 3: Synthesis
    test_synthesizer(novel_items)
    
    print("\n" + "█"*60)
    print("█" + " "*20 + "TESTING COMPLETE" + " "*22 + "█")
    print("█"*60 + "\n")


if __name__ == "__main__":
    main()
