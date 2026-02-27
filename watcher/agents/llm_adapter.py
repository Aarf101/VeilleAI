"""Local LLM adapter using Hugging Face `transformers` pipelines.

This provides a thin adapter exposing `generate(prompt, **kwargs)`.
If `transformers` is not installed, raises a clear ImportError.
"""
from __future__ import annotations
from typing import Optional


class LocalLLMAdapter:
    def __init__(self, model_name: str = "gpt2", task: str = "text-generation", device: Optional[int] = None):
        """Adapter for local HF models using `transformers` pipelines.

        - `task` can be `text-generation` (causal) or `text2text-generation` (seq2seq)
        - `device`: integer CUDA device index or None for CPU (-1)
        """
        try:
            from transformers import pipeline
        except Exception as e:
            raise ImportError(
                "transformers is required for local LLM generation. Install with: pip install transformers accelerate"
            ) from e

        self.model_name = model_name
        self.task = task or "text-generation"

        # transformers pipeline expects device index or -1 for CPU
        device_arg = -1 if device is None else int(device)
        self.pipe = None
        self.seq2seq = False
        try:
            # try creating a pipeline for the task
            self.pipe = pipeline(self.task, model=model_name, device=device_arg)
        except Exception:
            try:
                # fallback to CPU pipeline
                self.pipe = pipeline(self.task, model=model_name)
            except Exception:
                # If pipeline for task is not available (e.g., 'text2text-generation' missing),
                # fall back to direct model usage for seq2seq models (T5/FLAN-T5).
                try:
                    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                    import torch

                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                    self.device = torch.device("cpu") if device is None else torch.device(f"cuda:{device}")
                    self.model.to(self.device)
                    self.seq2seq = True
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to initialize model pipeline or seq2seq fallback for {model_name}: {e}"
                    ) from e

    def generate(self, prompt: str, max_new_tokens: int = 256, do_sample: bool = False, temperature: float = 0.2, **kwargs) -> str:
        """Generate text from prompt. Additional `pipeline` kwargs can be passed.

        Returns the generated text string.
        """
        # If we set up a seq2seq model manually, run generation via model.generate
        if getattr(self, "seq2seq", False):
            # use tokenizer and model directly
            import torch

            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            gen_kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": bool(do_sample),
                "temperature": float(temperature),
            }
            gen = self.model.generate(**inputs, **gen_kwargs)
            out = self.tokenizer.decode(gen[0], skip_special_tokens=True)
            return out

        params = dict(max_new_tokens=max_new_tokens, do_sample=do_sample, temperature=temperature)
        params.update(kwargs)
        out = self.pipe(prompt, **params)
        if out and isinstance(out, list):
            # different pipelines may return `generated_text` or `text` keys
            first = out[0]
            for key in ("generated_text", "text", "summary_text"):
                if key in first:
                    return first.get(key, "")
            # fallback: join all string values
            for v in first.values():
                if isinstance(v, str) and v.strip():
                    return v
        return ""
