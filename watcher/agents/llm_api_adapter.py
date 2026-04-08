"""API-based LLM adapter for free, high-quality models.

Supports:
1. GROQ API (free tier, ultra-fast) - Llama, Mixtral
2. Hugging Face Inference Providers (free tier) - DeepSeek R1, GPT-OSS, Qwen
3. Ollama (local, free) - DeepSeek, Llama, Mistral
4. Together AI (free tier) - Various open models

All of these are MUCH better than Flan-T5 and free to use.
"""
from __future__ import annotations
from typing import Optional, Dict
import os
import json


class APILLMAdapter:
    """Adapter for free API-based LLMs (Groq, Ollama, Together)."""
    
    PROVIDERS = {
        'groq': {
            'url': 'https://api.groq.com/openai/v1/chat/completions',
            'models': ['llama-3.3-70b-versatile', 'llama-3.1-405b-reasoning', 'deepseek-r1-distill-llama-70b', 'mixtral-8x7b-32768'],
            'requires_key': True,
            'free': True,
            'speed': 'ultra-fast',
        },
        'huggingface': {
            'url': 'https://router.huggingface.co/v1/chat/completions',
            'models': ['deepseek-ai/DeepSeek-R1:fastest', 'openai/gpt-oss-120b:fastest', 'Qwen/Qwen2.5-72B-Instruct:fastest'],
            'requires_key': True,
            'free': True,
            'speed': 'very fast',
            'context': 'varies by model',
        },
        'ollama': {
            'url': 'http://localhost:11434/api/generate',
            'models': ['deepseek-r1:latest', 'llama3.2:latest', 'mistral:latest'],
            'requires_key': False,
            'free': True,
            'speed': 'fast',
            'local': True,
        },
        'together': {
            'url': 'https://api.together.xyz/v1/chat/completions',
            'models': ['deepseek-ai/deepseek-llm-67b-chat', 'meta-llama/Llama-3-70b-chat-hf'],
            'requires_key': True,
            'free': True,  # Free tier available
            'speed': 'fast',
        },
        'gemini': {
            'url': 'https://generativelanguage.googleapis.com/v1beta/models',
            'models': ['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro'],
            'requires_key': True,
            'free': True,  # 1500 requests/day, 1M tokens/min
            'speed': 'very fast',
            'context': '1M tokens',
        }
    }
    
    def __init__(self, 
                 provider: str = 'groq',
                 model: str = None,
                 api_key: str = None,
                 timeout: int = 30):
        """
        Initialize API-based LLM adapter.
        
        Args:
            provider: 'groq', 'huggingface', 'ollama', or 'together'
            model: Model name (uses default if None)
            api_key: API key (not needed for Ollama). Can also use env vars:
                    - GROQ_API_KEY
                    - HF_TOKEN (for Hugging Face)
                    - TOGETHER_API_KEY
            timeout: Request timeout in seconds
        
        Examples:
            # Groq (fastest, free)
            adapter = APILLMAdapter('groq', api_key='gsk_...')
            
            # Hugging Face (DeepSeek R1, 671B params, free)
            adapter = APILLMAdapter('huggingface', model='deepseek-ai/DeepSeek-R1:fastest')
            
            # Ollama (local, no API key needed)
            adapter = APILLMAdapter('ollama')
            
            # Together AI
            adapter = APILLMAdapter('together', api_key='...')
        """
        self.provider = provider.lower()
        
        if self.provider not in self.PROVIDERS:
            raise ValueError(f"Provider must be one of: {list(self.PROVIDERS.keys())}")
        
        provider_info = self.PROVIDERS[self.provider]
        
        # Set model
        self.model = model or provider_info['models'][0]
        
        # Get API key from parameter or environment
        self.api_key = api_key
        if provider_info['requires_key'] and not self.api_key:
            # Hugging Face uses HF_TOKEN instead of HUGGINGFACE_API_KEY
            if self.provider == 'huggingface':
                env_var = 'HF_TOKEN'
            elif self.provider == 'gemini':
                env_var = 'GEMINI_API_KEY'
            else:
                env_var = f"{self.provider.upper()}_API_KEY"
            
            self.api_key = os.getenv(env_var)
            if not self.api_key:
                raise ValueError(
                    f"{self.provider} requires an API key. "
                    f"Set {env_var} environment variable or pass api_key parameter.\n"
                    f"Get free API key at: {self._get_signup_url()}"
                )
        
        self.base_url = provider_info['url']
        # Gemini needs more time for large reports
        self.timeout = 90 if self.provider == 'gemini' else timeout
        
        # Import requests
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")
    
    def _get_signup_url(self) -> str:
        """Get signup URL for the provider."""
        urls = {
            'groq': 'https://console.groq.com/keys (FREE, instant approval)',
            'huggingface': 'https://huggingface.co/settings/tokens (FREE, create token with "Inference" permission)',
            'together': 'https://api.together.xyz/signup (FREE tier available)',
            'ollama': 'https://ollama.ai (FREE, run locally)',
            'gemini': 'https://aistudio.google.com/app/apikey (FREE, 1500 req/day, 1M tokens/min)',
        }
        return urls.get(self.provider, '')
    
    def generate(self, 
                prompt: str, 
                max_new_tokens: int = 512,
                temperature: float = 0.7,
                **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input text
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            
        Returns:
            Generated text
        """
        if self.provider == 'ollama':
            return self._generate_ollama(prompt, max_new_tokens, temperature)
        else:
            return self._generate_openai_compatible(prompt, max_new_tokens, temperature)
    
    def _generate_ollama(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Ollama API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = self.requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except Exception as e:
            raise RuntimeError(
                f"Ollama generation failed: {e}\n"
                f"Make sure Ollama is running: ollama serve\n"
                f"And model is pulled: ollama pull {self.model}"
            )
    
    def _generate_openai_compatible(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using OpenAI-compatible API (Groq, Together) or Gemini."""
        if self.provider == 'gemini':
            return self._generate_gemini(prompt, max_tokens, temperature)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = self.requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except self.requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError(
                    f"Invalid API key for {self.provider}. "
                    f"Get a free key at: {self._get_signup_url()}"
                )
            raise RuntimeError(f"{self.provider} API error: {e}")
        except Exception as e:
            raise RuntimeError(f"{self.provider} generation failed: {e}")
    
    def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Google Gemini API."""
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        try:
            response = self.requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract text from Gemini response format
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        return parts[0]['text'].strip()
            
            raise RuntimeError(f"Unexpected Gemini response format: {result}")
        except self.requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                raise RuntimeError(
                    f"Invalid API key for Gemini. "
                    f"Get a free key at: {self._get_signup_url()}"
                )
            raise RuntimeError(f"Gemini API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}")


def get_recommended_adapter() -> APILLMAdapter:
    """
    Get the best available free LLM adapter.
    
    Priority:
    1. Groq (if API key available) - fastest, best quality
    2. Ollama (if running locally) - good quality, private
    3. Raises error with instructions
    
    Returns:
        Configured APILLMAdapter
    """
    # Try Groq first (best option)
    if os.getenv('GROQ_API_KEY'):
        return APILLMAdapter('groq')
    
    # Try Ollama
    try:
        adapter = APILLMAdapter('ollama')
        # Test if Ollama is running
        adapter.requests.get('http://localhost:11434/api/tags', timeout=2)
        return adapter
    except:
        pass
    
    # If nothing works, provide instructions
    raise RuntimeError(
        "\n" + "="*70 + "\n"
        "No free LLM provider configured!\n\n"
        "OPTION 1 (RECOMMENDED - Ultra Fast): Groq API\n"
        "  1. Get free API key: https://console.groq.com/keys\n"
        "  2. Set environment variable: export GROQ_API_KEY='your-key'\n"
        "  3. Uses DeepSeek-R1 70B (very high quality)\n\n"
        "OPTION 2 (Local/Private): Ollama\n"
        "  1. Install: curl -fsSL https://ollama.com/install.sh | sh\n"
        "  2. Start: ollama serve\n"
        "  3. Pull model: ollama pull deepseek-r1\n\n"
        "Both are 100% FREE and much better than Flan-T5!\n"
        + "="*70
    )
