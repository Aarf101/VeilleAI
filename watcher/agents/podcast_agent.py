import os
import asyncio
import edge_tts
from watcher.agents.synthesizer import call_llm

def remove_markdown(text):
    import re
    # Remove bold, italics
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    # Remove headers
    text = re.sub(r'#+\s*(.*?)\n', r'\1\n', text)
    # Remove URLs
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove multiple spaces/newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

async def _generate_audio_async(text, output_file, voice="en-US-ChristopherNeural"):
    """Valid popular voices: en-US-ChristopherNeural, en-US-AriaNeural, en-GB-RyanNeural, en-GB-SoniaNeural"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_podcast_audio(report_text, config, output_filepath):
    """
    1. Takes the markdown intelligence report.
    2. Rewrites it via LLM into a conversational, smooth podcast script.
    3. Synthesizes it to an mp3 file using Microsoft Edge TTS.
    """
    try:
        # Prompt the LLM to rewrite the report as a podcast script
        prompt = f"""You are the host of a concise daily tech briefing called "VeilleAI Intelligence Pod".
Your task is to take the following Markdown intelligence report and rewrite it into a conversational, engaging, and easy-to-listen-to podcast script.

RULES:
- Make it sound natural when spoken out loud.
- Do NOT include any markdown, asterisks, hashtags, or URLs in the script.
- Keep it under 500 words to maintain a ~3 minute runtime.
- Start with a quick, catchy welcome.
- Group the news logically. 
- End with a brief sign-off.
- ONLY output the spoken words. No director notes, no [Music plays], no stage directions.

INTELLIGENCE REPORT:
{report_text}
"""
        # Call the existing LangChain-powered LLM pipe
        try:
            script = call_llm(prompt, config)
        except Exception as e:
            import sys
            sys.stderr.write(f"LLM podcast script generation failed: {e}. Falling back to simple markdown stripping.\n")
            script = None
            
        # Fallback if LLM fails: just strip markdown
        if not script or script.isspace() or "Error" in script:
            script = remove_markdown(report_text)
            
        # Optional: ensure no lingering markdown
        clean_script = remove_markdown(script)
        
        # Generate audio using Edge TTS
        asyncio.run(_generate_audio_async(clean_script, output_filepath))
        return clean_script
    except Exception as e:
        import sys
        import traceback
        sys.stderr.write(f"Error generating podcast: {str(e)}\n")
        traceback.print_exc(file=sys.stderr)
        return None
