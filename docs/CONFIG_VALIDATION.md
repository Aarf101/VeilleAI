# Configuration Validation Guide

## Overview

VeilleAI now includes a **comprehensive configuration validation layer** that ensures your `config.yaml` is correct before the application starts. This prevents silent failures and provides helpful error messages.

## What Gets Validated

### Required Fields
- **`feeds`** - Must be a list of valid HTTP/HTTPS/FTP URLs

### Optional Fields (with validation)
- **`feeds_enabled`** - Dictionary mapping feed URLs to boolean (enable/disable)
- **`feeds_weight`** - Dictionary mapping feed URLs to numeric weights (must be >= 0)
- **`topics`** - List of strings or dicts with `name` and `description`
- **`chroma_path`** - String path to ChromaDB directory
- **`enable_autonomous_search`** - Boolean
- **`enable_rss_feeds`** - Boolean
- **`enable_trending_weighting`** - Boolean
- **`enable_youtube_transcripts`** - Boolean

## How to Use

### Loading Config
```python
from watcher.config import load_config
from watcher.exceptions import ConfigValidationError

try:
    config = load_config()
    print("Config loaded successfully!")
except ConfigValidationError as e:
    print(f"Configuration error: {e}")
    # Handle error gracefully
```

### Validating Config Programmatically
```python
from watcher.config_validator import validate_config
from watcher.exceptions import ConfigInvalidValueError

try:
    validated = validate_config(raw_config_dict)
except ConfigInvalidValueError as e:
    print(f"Invalid config value: {e}")
```

## Error Examples

### Invalid Feed URL
```yaml
# ❌ WRONG
feeds:
  - not-a-valid-url  # Missing http://
  - ftp://example.com/feed  # Not a feed URL
```
**Error:** `Invalid feed URL: 'not-a-valid-url'. Must be a valid http/https/ftp URL.`

### Wrong Data Type
```yaml
# ❌ WRONG
feeds: "https://example.com/feed.xml"  # Should be a list, not string
```
**Error:** `'feeds' must be a list, got str`

### Invalid Feed Weight
```yaml
# ❌ WRONG
feeds_weight:
  https://example.com/feed.xml: -1.5  # Weight must be >= 0
```
**Error:** `feeds_weight['https://example.com/feed.xml'] must be >= 0, got -1.5`

### Reference to Non-Existent Feed
```yaml
# ⚠️ WARNING (not an error, but logged)
feeds:
  - https://example.com/feed.xml

feeds_weight:
  https://other-site.com/feed.xml: 1.0  # This feed is not in the feeds list
```
**Warning:** `Feed 'https://other-site.com/feed.xml' in feeds_weight not found in feeds list`

## Valid Configuration Example

```yaml
# ✓ VALID
feeds:
  - https://www.artificialintelligence-news.com/feed/
  - https://huggingface.co/blog/feed.xml
  - https://techcrunch.com/feed/

feeds_enabled:
  https://www.artificialintelligence-news.com/feed/: true
  https://huggingface.co/blog/feed.xml: false
  https://techcrunch.com/feed/: true

feeds_weight:
  https://www.artificialintelligence-news.com/feed/: 1.0
  https://huggingface.co/blog/feed.xml: 2.0
  https://techcrunch.com/feed/: 1.5

topics:
  - AI
  - "Machine Learning"
  - name: "Deep Learning"
    description: "Neural networks and related techniques"

chroma_path: ./chroma_db

enable_autonomous_search: true
enable_rss_feeds: true
enable_trending_weighting: true
enable_youtube_transcripts: false
```

## Exception Hierarchy

The validation layer uses a structured exception hierarchy:

```
VeilleAIException (base)
├── ConfigError
│   ├── ConfigValidationError - Validation failed
│   ├── ConfigMissingKeyError - Required key missing
│   └── ConfigInvalidValueError - Invalid value for key
├── CollectorError
├── FilterError
├── StorageError
├── SynthesizerError
├── SchedulerError
├── LLMProviderError
├── NetworkError
└── DataValidationError
```

## Migration from Old Config

If you're upgrading from a version without validation:

1. Run the app - validation will report any issues
2. Fix errors reported by the validation layer
3. Ensure all feed URLs are valid (use browser to test)
4. Check `feeds_enabled` and `feeds_weight` reference actual feeds
5. Validate boolean flags are `true` or `false`, not strings

## Testing Your Config

Use the demo script to test your configuration:

```bash
python test_config_validation_demo.py
```

Or test a specific custom config file:

```python
from watcher.config import load_config

config = load_config("path/to/your/config.yaml")
print("Config is valid!")
```

## Best Practices

1. ✓ Use valid HTTPS URLs for feeds
2. ✓ Keep feed weights between 0.5 and 3.0 for best results
3. ✓ Always use boolean values (true/false) for flags
4. ✓ Remove feeds from `feeds_enabled` that aren't in the `feeds` list
5. ✓ Test config changes before deploying

## Troubleshooting

**Q: "Invalid feed URL" error but the URL works in my browser**
- A: Add the protocol (`https://`) if missing
- A: Check for extra spaces: `" https://example.com "` won't work
- A: Validate it's a feed URL, not a webpage URL

**Q: "feeds must be a list" but I only have one feed**
- A: Even single feeds must be in a list: `feeds: ["https://example.com/feed.xml"]`

**Q: Config worked before, now getting validation errors**
- A: The validation layer is stricter. Follow the error messages to fix issues.
- A: Check YAML syntax with `yamllint config.yaml`

## See Also

- [Config File Reference](../docs/CONFIG_REFERENCE.md)
- [Exception Types](../watcher/exceptions.py)
- [Validation Source](../watcher/config_validator.py)
