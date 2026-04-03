import sys
try:
    import sgmllib
    print("sgmllib is already available")
except ImportError:
    print("sgmllib is missing, attempting shim...")
    try:
        import sgmllib3k as sgmllib
        sys.modules['sgmllib'] = sgmllib
        print("sgmllib shimmed successfully using sgmllib3k")
    except ImportError:
        print("sgmllib3k is also missing!")

try:
    import feedparser
    print(f"feedparser version: {feedparser.__version__}")
    # Try parsing a tiny XML
    xml = "<?xml version='1.0'?><rss version='2.0'><channel><title>Test</title><item><title>Item</title></item></channel></rss>"
    d = feedparser.parse(xml)
    print(f"Parsed title: {d.feed.title}")
except Exception as e:
    print(f"FAILED: {e}")
