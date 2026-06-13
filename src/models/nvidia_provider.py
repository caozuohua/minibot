"""NVIDIA NIM model provider (OpenAI-compatible interface)."""

import logging

from openai import OpenAI

from src.models.base_provider import ModelProvider

logger = logging.getLogger(__name__)

# NVIDIA NIM base URL
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaProvider(ModelProvider):
    """NVIDIA NIM API provider (embedding models via OpenAI-compatible interface)."""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__()
        self.api_key = api_key
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url or NVIDIA_BASE_URL,
        )

    def name(self) -> str:
        return "nvidia"

    def chat(self, messages: list, model: str | None = None) -> str:
        """NVIDIA NIM currently focuses on embedding models.

        Raises NotImplementedError if chat is not supported.
        """
        raise NotImplementedError(
            "NVIDIA NIM provider does not support chat completions"
        )

    def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding vector via NVIDIA NIM."""
        logger.debug(f"[NVIDIA] embed request, model={model}")
        response = self._client.embeddings.create(
            model=model,
            input=text,
        )
        embedding = response.data[0].embedding
        logger.debug(f"[NVIDIA] embed dimension: {len(embedding)}")
        return embedding
