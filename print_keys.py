from watcher.agents.collector import CollectorAgent
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['feeds_enabled'] = {f: False for f in config['feeds']}
config['feeds_enabled']['https://www.artificialintelligence-news.com/feed/'] = True

collector = CollectorAgent(storage=None)
items = collector.collect_new()
for item in items:
    print(item.keys())
    break
