# VeilleAI (formerly known as AgenticNotes)

VeilleAI is a fully autonomous, AI-powered intelligence gathering and tech-watch (*veille technologique*) pipeline. It acts as your personal research team—scouring the internet, filtering the noise, and synthesizing high-quality, executive-ready Markdown reports based on your specific topics of interest.

## Key Features

* **Tri-Modal Collection Strategy:**
  * **Standard RSS:** Pulls from dozens of traditional news feeds.
  * **Autonomous News Search:** Uses headless DuckDuckGo searches to find breaking news articles beyond your feed list.
  * **Autonomous YouTube Scraping:** Automatically finds relevant YouTube videos, extracts their Closed Captions/Transcripts, and reads them as text.
* **Intelligent Sorting (Hot & Fresh):** Custom mathematical weighting that detects "Hot" news (multiple sources covering the same event) and heavily prioritizes "Fresh" articles (within 24-48 hours) while penalizing stale data.
* **Multi-LLM Synthesis:** Support for **Groq** (Llama 3.3 70b), **Google Gemini** (2.0 Flash), and local open-source models via **Ollama**. 
* **Sleek Dashboard:** A beautiful, dark-mode **Streamlit dashboard** to manage topics, configure AI providers, test pipelines, and view generated reports seamlessly.

## Quick Start

### 1. Installation
Clone the repository and install the dependencies:

**Mac/Linux:**
```bash
git clone https://github.com/Aarf101/AgenticNotes.git
cd AgenticNotes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```powershell
git clone https://github.com/Aarf101/AgenticNotes.git
cd AgenticNotes
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file in the root directory and add your preferred API keys. You only need the key for the provider you intend to use:
```env
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=AIza_your_key_here
```

### 3. Launch the Dashboard
Start the **Streamlit UI** to configure your topics and run the pipeline:
```bash
streamlit run streamlit_app.py
```

## Architecture & Pipeline

1. **Collector Agent:** Gathers raw data based on your UI-selected strategy (RSS, DuckDuckGo News, or YouTube Transcripts).
2. **Filter/Scoring Agent:** Dedupes identical articles and scores them using the "Trending & Recency" decay algorithm.
3. **Synthesizer Agent (LLM):** Takes the top 5 articles per topic, reads the full contexts, and writes an executive summary, period news, and strategic implications into a final `.md` file.

## Tech Stack
* **Backend:** Python
* **Web Framework:** Streamlit
* **AI/LLMs:** Groq, Gemini, Ollama
* **Data Gathering:** Feedparser, DuckDuckGo-Search (`ddgs`), YouTube Transcript API
* **Storage:** SQLite (raw data cache) & ChromaDB (Vector store)

Voir `config.yaml` pour ajuster sources et paramètres.
