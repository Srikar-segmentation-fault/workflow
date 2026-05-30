"""
WorkFlow — LLM Factory
Provider: Ollama (local) — model: qwen2.5
Uses the Ollama REST API directly via httpx (no SDK dependency).
"""
import json

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

# Ollama chat endpoint
_OLLAMA_CHAT_URL = "{base}/api/chat"
_OLLAMA_TAGS_URL = "{base}/api/tags"


class LLMFactory:
    """
    Thin async wrapper around the Ollama /api/chat endpoint.
    All AI calls go through call_ollama() for a consistent interface.
    """

    @classmethod
    async def call_ollama(
        cls,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> str:
        """
        POST to Ollama /api/chat and return the assistant message content.
        json_mode=True appends a JSON-only instruction and sets format="json".
        """
        if json_mode:
            user = (
                user
                + "\n\nIMPORTANT: Respond ONLY with valid JSON. "
                "No markdown fences, no extra text."
            )

        payload: dict = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        url = _OLLAMA_CHAT_URL.format(base=settings.ollama_base_url)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        data = response.json()
        text = data["message"]["content"].strip()

        logger.info(
            "llm.call_complete",
            provider="ollama",
            model=settings.ollama_model,
            chars=len(text),
        )
        return text

    @classmethod
    async def health_check(cls) -> dict:
        """Check Ollama is running and qwen2.5 is available."""
        try:
            url = _OLLAMA_TAGS_URL.format(base=settings.ollama_base_url)
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            models = [m["name"] for m in resp.json().get("models", [])]
            model_ready = any(settings.ollama_model in m for m in models)

            return {
                "status": "ok" if model_ready else "model_not_found",
                "provider": "ollama",
                "model": settings.ollama_model,
                "available_models": models,
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "provider": "ollama",
                "model": settings.ollama_model,
                "error": str(e),
            }
