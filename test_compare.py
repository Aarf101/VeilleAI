import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from watcher.agents.filter import SmartFilter
from watcher.nlp.embeddings import EmbeddingProvider
from watcher.agents.novelty_detector import _cosine_sim
import numpy as np

def test_article_topic_comparison():
    print("\n" + "="*60)
    print("TESTING TOPIC RELEVANCE (SmartFilter)")
    print("="*60)
    
    topics = ["AI in Healthcare", "Crypto Regulation", "Sustainable Energy"]
    sf = SmartFilter(topics=topics, threshold=0.30)
    
    article = {
        "title": "New AI diagnostic tool approved by FDA",
        "summary": "The FDA has given the green light to a new deep learning algorithm that can detect early signs of retinal disease from eye scans.",
        "content": "Medical technology continues to advance as AI models prove their worth in clinical settings..."
    }
    
    print(f"Article: {article['title']}")
    print("-" * 30)
    
    for topic in topics:
        is_match, score, method = sf.match_article_to_topic(article, topic)
        status = "[MATCH]" if is_match else "[REJECT]"
        print(f"{status} Topic: {topic:20} | Score: {score:.4f} | Method: {method}")

def test_article_article_comparison():
    print("\n" + "="*60)
    print("TESTING ARTICLE-TO-ARTICLE NOVELTY (NN)")
    print("="*60)
    
    provider = EmbeddingProvider()
    
    # Cases to test
    # 1. Very similar (semantic duplicates)
    art1_text = "NVIDIA announces new H200 GPU for large language model training."
    art2_text = "NVIDIA releases the H200 chips designed to train AI models faster."
    
    # 2. Complete different topic
    art3_text = "SpaceX completes another successful Starship test flight in Texas."
    
    texts = [art1_text, art2_text, art3_text]
    embs = provider.embed(texts)
    
    sim12 = _cosine_sim(embs[0], embs[1])
    sim13 = _cosine_sim(embs[0], embs[2])
    
    print(f"Art 1: {art1_text}")
    print(f"Art 2: {art2_text}")
    print(f"Art 3: {art3_text}")
    print("-" * 30)
    
    threshold = 0.75  # Default threshold used in novelty_detector.py
    
    print(f"Sim(1 vs 2): {sim12:.4f} -> Novel? {sim12 < threshold} (Expected: False/Duplicate)")
    print(f"Sim(1 vs 3): {sim13:.4f} -> Novel? {sim13 < threshold} (Expected: True/Novel)")

if __name__ == "__main__":
    try:
        test_article_topic_comparison()
        test_article_article_comparison()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()