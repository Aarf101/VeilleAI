import os
import sqlite3
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from watcher.storage.store import _VECTOR_STORE, _EMB_PROVIDER

def _get_langchain_llm(config: Dict[str, Any]):
    """Helper to instantiate the appropriate LangChain ChatModel based on config."""
    def get_config_value(cfg, *keys, default=''):
        for key in keys:
            if key in cfg and cfg[key]:
                return cfg[key]
        return default

    provider = get_config_value(config, 'provider', 'api_provider', default='groq')
    model = get_config_value(config, 'model', 'api_model', default='')
    
    if provider == 'gemini':
        # Use the newest langchain google wrapper if installed, or fallback
        from langchain_core.messages import HumanMessage
        class GeminiFallback:
            def __init__(self, m):
                import importlib
                self.genai = importlib.import_module('google.genai')
                self.api_key = os.environ.get('GEMINI_API_KEY')
                self.client = self.genai.Client(api_key=self.api_key)
                self.model = m or 'gemini-2.0-flash'
            def invoke(self, messages):
                if isinstance(messages, list):
                    prompt = "\n".join([m.content for m in messages])
                else: prompt = str(messages.to_string())
                resp = self.client.models.generate_content(model=self.model, contents=prompt)
                from langchain_core.messages import AIMessage
                return AIMessage(content=resp.text)
        return GeminiFallback(model)
        
    elif provider == 'groq':
        from langchain_groq import ChatGroq
        api_key = os.environ.get('GROQ_API_KEY', '')
        return ChatGroq(
            api_key=api_key,
            model_name=model or "mixtral-8x7b-32768",
            temperature=0.3
        )
    else:
        # Default/Fallback to Ollama
        from langchain_core.messages import AIMessage
        class OllamaFallback:
            def __init__(self, m):
                self.model = m or 'llama3'
                from groq import Groq # we'll reuse groq interface but point it to ollama if needed
            def invoke(self, messages):
                return AIMessage(content=f"LangChain adapter for {provider} not natively supported in VeilleAI yet.")
        return OllamaFallback(model)

def query_rag(query: str, config: Dict[str, Any], db_path: str, top_k: int = 40, history: List[Dict[str, str]] = None) -> str:
    """Uses LangChain and the Vector store to answer a query over stored articles with conversational memory."""
    if not _VECTOR_STORE or not _EMB_PROVIDER:
        return "RAG is not fully configured (missing Vector Store or Embeddings provider)."
    
    try:
        # 1. Retrieve IDs from Chroma vector store
        query_emb = _EMB_PROVIDER.embed([query])[0].tolist()
        results = _VECTOR_STORE.query(query_emb, n_results=top_k)
        
        if not results:
            return "I couldn't find any relevant articles in the database to answer your question."
            
        matched_ids = [res[0] for res in results]
        
        # 2. Fetch full article text from SQLite
        articles = []
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" * len(matched_ids))
            cur = conn.execute(
                f"SELECT title, summary, content, source, published FROM items WHERE id IN ({placeholders})",
                matched_ids
            )
            for row in cur.fetchall():
                articles.append(dict(row))
                
        # 3. Format Documents into a single context string
        context_str = ""
        for i, art in enumerate(articles, 1):
            title = art.get("title") or "Unknown Title"
            source = art.get("source") or "Unknown Source"
            date = art.get("published") or "Unknown Date"
            text_body = art.get("content") or art.get("summary") or ""
            context_str += f"Document {i}:\nTitle: {title} (Source: {source}, Date: {date})\nBody: {text_body[:1000]}\n\n"
            
        # 4. Format History
        history_msgs = []
        if history:
            for msg in history[-6:]: # Keep last 3 turns
                role = "assistant" if msg["role"] == "assistant" else "human"
                history_msgs.append((role, msg["content"]))

        # 5. LangChain Prompt Template
        messages = [
            ("system", "You are an intelligent technical assistant for VeilleAI. You use the provided context and conversation history to answer user questions.\n"
                       "INSTRUCTIONS:\n"
                       "1. DO NOT use 'Document X' or 'Document [number]' in your response. This is internal metadata only.\n"
                       "2. For EVERY piece of information you provide, you MUST explicitly mention its Source and its Publication Date (e.g., 'According to WIRED (2026-05-12)...').\n"
                       "3. If the user asks about a connection between entities, scan all context. If they aren't in the same article, summarize information for each from the context.\n"
                       "Context:\n{context}")
        ]
        messages.extend(history_msgs)
        messages.append(("human", "Question: {question}"))
        
        prompt_template = ChatPromptTemplate.from_messages(messages)

        # 6. Build LangChain LLM Pipeline
        llm = _get_langchain_llm(config)
        output_parser = StrOutputParser()
        
        # LCEL logic: Prompt -> LLM -> Parser
        chain = prompt_template | llm | output_parser
        
        # 7. Execute Chain
        response = chain.invoke({
            "context": context_str,
            "question": query
        })
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"LangChain Error during RAG query: {str(e)}"
