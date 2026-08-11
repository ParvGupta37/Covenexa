"""
Cohere implementation of LLMProvider — Sprint 2.
Wraps Cohere Command A for text generation and Embed v4 for embeddings.
"""
from typing import Any, Dict, List, Optional
import structlog
from ai.llm.base import LLMProvider
from integrations.cohere.client import CohereClient

logger = structlog.get_logger(__name__)


class CohereProvider(LLMProvider):
    """
    LLMProvider implementation backed by the CohereClient.
    Agents call LLMService → CohereProvider → CohereClient.
    Also exposes embed() for the DocumentAgent to generate chunk embeddings.
    """

    def __init__(self, api_key: str, model_name: str = "command-a-03-2025") -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._client = CohereClient(api_key=api_key)
        self._client.initialize()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Generate a text response using Cohere Command A."""
        logger.info("cohere.generate", model=self._model_name, prompt_len=len(prompt))
        result = await self._client.chat(
            message=prompt,
            model=self._model_name,
            system_prompt=system_prompt,
        )
        return result.get("text", "")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Alias for generate() to support BaseAgent / Agent invocations."""
        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Generate a conversational response given a message list."""
        logger.info("cohere.generate_chat", model=self._model_name, message_count=len(messages))
        # Combine messages into a single prompt for Cohere chat API
        system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
        user_msgs = [m["content"] for m in messages if m.get("role") != "system"]
        system_prompt = system_msgs[0] if system_msgs else None
        combined_prompt = "\n".join(user_msgs)
        result = await self._client.chat(
            message=combined_prompt,
            model=self._model_name,
            system_prompt=system_prompt,
        )
        return result.get("text", "")

    async def embed(
        self,
        texts: List[str],
        input_type: str = "search_document",
    ) -> List[List[float]]:
        """Generate Cohere Embed v4 embeddings (1024-dim)."""
        return await self._client.embed(texts=texts, input_type=input_type)
