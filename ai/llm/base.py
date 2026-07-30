"""
Abstract LLM Provider interface.
Allows switching models/providers (Cohere, OpenAI, Anthropic) without altering agent code.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    """
    Abstract base class for all Large Language Model providers.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """
        Generate text response from raw prompt input.
        """
        ...

    @abstractmethod
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """
        Generate chat response from list of structured messages.
        Each message dict should have 'role' (system/user/assistant) and 'content'.
        """
        ...
