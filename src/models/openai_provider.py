"""OpenAI model provider."""

import logging

from openai import OpenAI

from src.models.base_provider import ModelProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(ModelProvider):
    """OpenAI API provider (compatible with any OpenAI-compatible API)."""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__()
        self.api_key = api_key
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def name(self) -> str:
        return "openai"

    def chat(self, messages: list, model: str | None = None) -> str:
        """Send chat completion request."""
        logger.debug(f"[OpenAI] chat request, model={model}")
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        logger.debug(f"[OpenAI] chat response length: {len(content)} chars")
        return content or ""

    def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding vector."""
        logger.debug(f"[OpenAI] embed request, model={model}")
        response = self._client.embeddings.create(
            model=model,
            input=text,
        )
        embedding = response.data[0].embedding
        logger.debug(f"[OpenAI] embed dimension: {len(embedding)}")
        return embedding
