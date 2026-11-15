import os
import re
import json
import logging
import httpx
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Explanation template cache
_TEMPLATE_CACHE: Dict[str, str] = {}

class GroqLLMManager:
    """
    Manages Groq LLM client, runtime model discovery, fallback chain,
    reasoning content stripping, and deterministic fallback.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        self.active_model: Optional[str] = None
        self.models_discovered: List[str] = []
        self._init_model()

    def _init_model(self):
        if settings.GROQ_MODEL:
            self.active_model = settings.GROQ_MODEL
            logger.info(f"Using explicitly configured GROQ_MODEL: {self.active_model}")
            return

        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Operating in deterministic template fallback mode.")
            return

        try:
            # Query Groq models endpoint
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with httpx.Client(timeout=5.0) as client:
                res = client.get("https://api.groq.com/openai/v1/models", headers=headers)
                if res.status_code == 200:
                    models = [m.get("id", "") for m in res.json().get("data", [])]
                    self.models_discovered = models
                    logger.info(f"Discovered {len(models)} models on Groq.")
                    
                    # 1. Search for Qwen chat model
                    qwen_models = [m for m in models if "qwen" in m.lower() and not "whisper" in m.lower()]
                    if qwen_models:
                        self.active_model = qwen_models[0]
                        logger.info(f"Selected Qwen model: {self.active_model}")
                        return

                    # 2. Search for gpt-oss-120b
                    if "openai/gpt-oss-120b" in models:
                        self.active_model = "openai/gpt-oss-120b"
                        logger.info(f"Selected model: {self.active_model}")
                        return

                    # 3. Search for gpt-oss-20b
                    if "openai/gpt-oss-20b" in models:
                        self.active_model = "openai/gpt-oss-20b"
                        logger.info(f"Selected model: {self.active_model}")
                        return
                    
                    # 4. Fallback to any valid non-llama text model
                    non_llama = [m for m in models if "llama" not in m.lower() and "whisper" not in m.lower()]
                    if non_llama:
                        self.active_model = non_llama[0]
                        logger.info(f"Selected non-llama model: {self.active_model}")
                        return
        except Exception as e:
            logger.warning(f"Groq model discovery failed: {e}. Will fall back to template engine.")

    def strip_reasoning(self, text: str) -> str:
        """Strip <think>...</think> or other internal reasoning tags."""
        if not text:
            return ""
        # Remove XML think tags
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Remove markdown think blocks
        cleaned = re.sub(r"```thinking.*?```", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def generate_chat_response(self, messages: List[Dict[str, str]], fallback_template: str = "") -> str:
        """
        Generate completion using active Groq model with fallback chain.
        If Groq is exhausted or unavailable, returns fallback_template.
        """
        if not self.api_key or not self.active_model:
            return fallback_template

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.active_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return self.strip_reasoning(content)
                elif res.status_code == 404 or "model_not_found" in res.text:
                    logger.warning(f"Model {self.active_model} deprecated or not found. Falling back.")
                    # Try next fallback model
                    if self.active_model != "openai/gpt-oss-20b":
                        self.active_model = "openai/gpt-oss-20b"
                        payload["model"] = self.active_model
                        res2 = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                        if res2.status_code == 200:
                            content = res2.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                            return self.strip_reasoning(content)
                elif res.status_code == 429:
                    logger.warning("Groq rate limit (429) hit. Falling back to template generation.")
        except Exception as e:
            logger.warning(f"Groq API call exception: {e}. Falling back to template.")

        return fallback_template

llm_manager = GroqLLMManager()
