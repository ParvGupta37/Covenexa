"""
Cohere integration client — Sprint 2 implementation.
Provides:
  - LLM inference via Command A (command-a-03-2025)
  - Embeddings via Embed v4 (embed-v4.0, 1024 dimensions)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_EMBED_BATCH_SIZE = 96  # Cohere Embed v4 max batch size


class CohereClient:
    """
    Cohere API client for LLM inference and embedding generation.
    Gracefully degrades to mock responses when API key is absent.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: Any = None
        self._available = bool(api_key and api_key != "not_set")

    def initialize(self) -> None:
        """Initialize the Cohere async client."""
        if not self._available:
            logger.warning("CohereClient: No API key — LLM calls will return mock responses.")
            return
        try:
            import cohere
            self._client = cohere.AsyncClientV2(api_key=self._api_key)
            logger.info("CohereClient initialized (Command A + Embed v4).")
        except ImportError:
            logger.error("cohere package not installed.")
            self._available = False

    async def chat(
        self,
        message: str,
        model: str = "command-a-03-2025",
        documents: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a chat message to Cohere Command A.
        Returns {"text": str, "model": str, "usage": dict}.
        """
        if not self._available or self._client is None:
            return {"text": _mock_llm_response(message), "model": "mock", "usage": {}}

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})

            kwargs: dict[str, Any] = {"model": model, "messages": messages}
            if documents:
                kwargs["documents"] = documents

            response = await self._client.chat(**kwargs)
            text = response.message.content[0].text if response.message.content else ""
            return {
                "text": text,
                "model": model,
                "usage": {
                    "input_tokens": getattr(response.usage, "billed_units", {}).get("input_tokens", 0),
                    "output_tokens": getattr(response.usage, "billed_units", {}).get("output_tokens", 0),
                } if hasattr(response, "usage") else {},
            }
        except Exception as exc:
            logger.error("CohereClient.chat failed: %s", exc)
            return {"text": "", "model": model, "usage": {}, "error": str(exc)}

    async def embed(
        self,
        texts: list[str],
        model: str = "embed-v4.0",
        input_type: str = "search_document",
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        Automatically batches into groups of 96.
        Returns list of 1024-dim float vectors.
        """
        if not self._available or self._client is None:
            # Return deterministic zero-vector mocks so pipeline doesn't crash
            return [[0.0] * 1024 for _ in texts]

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[i: i + _EMBED_BATCH_SIZE]
            try:
                response = await self._client.embed(
                    texts=batch,
                    model=model,
                    input_type=input_type,
                    embedding_types=["float"],
                )
                all_embeddings.extend(response.embeddings.float_)
            except Exception as exc:
                logger.error("CohereClient.embed batch %d failed: %s", i, exc)
                # Return zeros for failed batch
                all_embeddings.extend([[0.0] * 1024 for _ in batch])
        return all_embeddings


def _mock_llm_response(message: str) -> str:
    """Return a clearly-labelled placeholder when Cohere is unavailable."""
    return (
        '{"_note": "Cohere API key not configured. This is a mock response.", '
        '"covenants": [], "financial_metrics": {}}'
    )
