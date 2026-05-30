"""
WorkFlow — LLM Factory
Provides a pluggable LLM abstraction so the AI service can swap
providers without changing business logic.
Currently supports: Ollama (local)
"""
import structlog
from langchain_ollama import ChatOllama

from app.config import settings

logger = structlog.get_logger()


class LLMFactory:
    """
    Returns a configured LangChain chat model.
    Strategy pattern — add more providers (Claude, GPT) by adding branches.
    """

    _chat_model: ChatOllama | None = None

    @classmethod
    def get_chat_llm(cls, temperature: float = 0.1) -> ChatOllama:
        """
        Returns a singleton ChatOllama instance.
        temperature=0.1 for deterministic, factual AI verification.
        """
        if cls._chat_model is None:
            logger.info(
                "llm.initializing",
                provider="ollama",
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
            cls._chat_model = ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=temperature,
                num_predict=600,
                format="",  # JSON format set per-call when needed
            )
        return cls._chat_model

    @classmethod
    def get_json_llm(cls) -> ChatOllama:
        """Returns Ollama configured to output JSON — used for verifyLog."""
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            num_predict=300,
            format="json",
        )

    @classmethod
    async def health_check(cls) -> dict:
        """Check if Ollama is reachable and model is available."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                models = resp.json().get("models", [])
                available = [m["name"] for m in models]
                model_ready = any(
                    settings.ollama_model in m for m in available
                )
                return {
                    "status": "ok" if model_ready else "model_not_found",
                    "available_models": available,
                    "configured_model": settings.ollama_model,
                }
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
