"""
Unified LLM Service.
This is the only class AI Agents call to execute LLM queries.
"""
from typing import Any, Dict, List, Optional
from ai.llm.base import LLMProvider


class LLMService:
    """
    Orchestrates prompts handling and routing to the active LLMProvider.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """Helper to invoke generation on provider."""
        return await self._provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """Helper to invoke conversational queries."""
        return await self._provider.generate_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
