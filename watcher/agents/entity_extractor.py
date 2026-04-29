import json
import re
import logging
from watcher.agents.synthesizer import call_llm

logger = logging.getLogger(__name__)

PROMPT = """Extract the top 10 technical entities (Libraries, Frameworks, Companies, Protocols, People, Concepts) from the text.
Return ONLY a JSON array (no explanation) using objects with keys `name` and `type`.
Example output:
[{"name": "React", "type": "Framework"}, {"name": "LangChain", "type": "Library"}]

Text:
{text}
"""

def extract_entities(text, config):
    if not text or len(text.strip()) < 20:
        return []

    # Use simple replace to avoid interpreting braces inside the PROMPT
    # (PROMPT contains JSON examples with braces which would break str.format)
    prompt = PROMPT.replace("{text}", text[:4000])  # bound length
    try:
        response = call_llm(prompt, config)
        # Parse JSON
        # Find json array boundaries
        # Try to extract the first JSON array in the response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            j_str = match.group(0)
            try:
                return json.loads(j_str)
            except Exception:
                # fallthrough to try to sanitize
                pass

        # Fallback: try to extract JSON by trimming leading/trailing non-json
        try:
            return json.loads(response.strip())
        except Exception:
            # attempt to remove common wrappers like ```json
            cleaned = re.sub(r'```json', '', response, flags=re.IGNORECASE)
            cleaned = re.sub(r'```', '', cleaned)
            # find array again
            match2 = re.search(r'\[.*?\]', cleaned, re.DOTALL)
            if match2:
                try:
                    return json.loads(match2.group(0))
                except Exception:
                    pass
        # Last resort: return empty
        logger.error(f"Failed to parse entities JSON from LLM response: {response[:200]}")
        return []
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return []

def save_entities_to_db(item_id, entities, mention_time, db_path="watcher.db"):
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            for ent in entities:
                name = ent.get("name") or ent.get("entity")
                etype = ent.get("type", "Unknown")
                if not name:
                    continue
                name = name.strip().title()

                # Insert entity if not exists
                cur.execute("INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?)", (name, etype))
                cur.execute("SELECT id FROM entities WHERE name = ?", (name,))
                row = cur.fetchone()
                if row:
                    ent_id = row[0]
                    cur.execute("INSERT OR IGNORE INTO item_entities (item_id, entity_id, mention_time) VALUES (?, ?, ?)", 
                                (item_id, ent_id, mention_time))
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving entities to db: {e}")

