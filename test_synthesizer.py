import re
from datetime import datetime

def clean_text(text):
    if not text: return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    text = ' '.join(text.split())
    return text[:200]
