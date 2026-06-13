"""Abstract base class for model providers."""

from abc import ABC, abstractmethod


class ModelProvider(ABC):
    """Base class for all model providers."""

    def __init__(self):
        self._model_names = {}

    @abstractmethod
    def name(self) -> str:
        """Return provider name (e.g., 'openai', 'gemini')."""
        ...

    def name_to_model(self, task: str) -> str | None:
        """Return default model name for a task ('chat' or 'embed')."""
        return self._model_names.get(task)

    @abstractmethod
    def chat(self, messages: list, model: str | None = None) -> str:
        """Send chat completion request.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            model: Optional model override.

        Returns:
            Assistant response text.
        """
        ...

    @abstractmethod
    def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding vector.

        Args:
            text: Input text.
            model: Optional model override.

        Returns:
            Embedding vector as list of floats.
        """
        ...
