import yaml
from pathlib import Path

def save_config(config):
    try:
        if 'feeds' in config:
            config['feeds'] = list(dict.fromkeys(config['feeds']))
        if 'topics' in config:
            config['topics'] = list(dict.fromkeys(config['topics']))
            
        with open("config_test.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

config['feeds'].append("https://test.rss")
print("Result of save_config:", save_config(config))
