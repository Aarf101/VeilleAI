import yaml
from watcher.agents.filter import SmartFilter
from watcher.agents.collector import CollectorAgent

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['feeds_weight']['https://www.artificialintelligence-news.com/feed/'] = 0.1
config['feeds_enabled'] = {f: False for f in config['feeds']}
config['feeds_enabled']['https://www.artificialintelligence-news.com/feed/'] = True

collector = CollectorAgent(storage=None)
items = collector.collect_new()

flt = SmartFilter(['Artificial Intelligence'], threshold=0.5, config=config)
for item in items:
    res, score, method = flt.match_article_to_topic(item, 'Artificial Intelligence')
    print(f"Title: {item['title'][:30]}... | Score: {score} | Method: {method} | Target: {item.get('feed_url')}")
