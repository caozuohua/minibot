"""Model router with multi-provider fallback."""

import logging

from src.config import Config, ProviderConfig
from src.models.base_provider import ModelProvider
from src.models.gemini_provider import GeminiProvider
from src.models.nvidia_provider import NvidiaProvider
from src.models.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class NoAvailableModelError(Exception):
    """Raised when all model providers fail."""

    pass


class ModelRouter:
    """Routes chat and embedding requests across multiple providers with fallback."""

    def __init__(self, config: Config):
        self.config = config
        self._providers: list[ModelProvider] = []
        self._chat_providers: list[ModelProvider] = []
        self._embed_providers: list[ModelProvider] = []
        self._active_provider: str | None = None
        self._build_providers()

    def _build_providers(self) -> None:
        """Build provider instances from config."""
        for pc in self.config.models.providers:
            if not pc.api_key:
                logger.warning(f"Provider '{pc.name}' has no API key, skipping")
                continue

            provider = self._create_provider(pc)
            if provider:
                # Store model names on the provider for lookup
                provider._model_names = pc.models
                self._providers.append(provider)
                logger.info(f"Loaded provider: {provider.name()}")

        # Separate chat-capable and embed-capable providers
        for p in self._providers:
            if "chat" in p._model_names:
                self._chat_providers.append(p)
            if "embed" in p._model_names:
                self._embed_providers.append(p)

        if not self._providers:
            logger.warning("No model providers loaded")

    def _create_provider(self, pc: ProviderConfig) -> ModelProvider | None:
        """Create a provider instance from config."""
        try:
            if pc.name == "openai":
                return OpenAIProvider(api_key=pc.api_key, base_url=pc.base_url)
            elif pc.name == "gemini":
                return GeminiProvider(api_key=pc.api_key)
            elif pc.name == "nvidia":
                return NvidiaProvider(api_key=pc.api_key)
            else:
                logger.warning(f"Unknown provider type: {pc.name}")
                return None
        except Exception as e:
            logger.error(f"Failed to create provider '{pc.name}': {e}")
            return None

    def chat(self, messages: list, model: str | None = None) -> str:
        """Send chat request with fallback across providers."""
        errors = []
        for provider in self._chat_providers:
            try:
                provider_model = model or provider.name_to_model("chat")
                result = provider.chat(messages, provider_model)
                self._active_provider = provider.name()
                logger.info(f"Chat completed via {provider.name()}")
                return result
            except Exception as e:
                errors.append(f"{provider.name()}: {e}")
                logger.warning(f"Provider {provider.name()} failed: {e}")

        raise NoAvailableModelError(f"All chat providers failed: {'; '.join(errors)}")

    def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding with fallback across providers."""
        errors = []
        for provider in self._embed_providers:
            try:
                provider_model = model or provider.name_to_model("embed")
                result = provider.embed(text, provider_model)
                self._active_provider = provider.name()
                logger.info(f"Embedding generated via {provider.name()}")
                return result
            except Exception as e:
                errors.append(f"{provider.name()}: {e}")
                logger.warning(f"Provider {provider.name()} embed failed: {e}")

        raise NoAvailableModelError(
            f"All embedding providers failed: {'; '.join(errors)}"
        )

    @property
    def active_provider(self) -> str | None:
        """Return the name of the last successful provider."""
        return self._active_provider

    @property
    def available_providers(self) -> list[str]:
        """Return list of available provider names."""
        return [p.name() for p in self._providers]
