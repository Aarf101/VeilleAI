import os
from pathlib import Path

# Charge .env
for line in Path('.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

# Test Groq
try:
    from groq import Groq
    client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
    resp   = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": "Dis juste 'LLM fonctionne !'"
        }],
        max_tokens=20
    )
    print("GROQ OK:", resp.choices[0].message.content)
except Exception as e:
    print("GROQ ERREUR:", e)

# Test Gemini
try:
    import google.generativeai as genai
    genai.configure(
        api_key=os.environ.get('GEMINI_API_KEY')
    )
    m    = genai.GenerativeModel('gemini-2.0-flash')
    resp = m.generate_content("Dis juste 'LLM fonctionne !'")
    print("GEMINI OK:", resp.text)
except Exception as e:
    print("GEMINI ERREUR:", e)