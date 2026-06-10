 1: """Model router with multi-provider fallback."""
 2: 
 3: import logging
 4: from typing import List, Optional
 5: 
 6: from src.config import Config, ProviderConfig
 7: from src.models.base_provider import ModelProvider
 8: from src.models.openai_provider import OpenAIProvider
 9: from src.models.gemini_provider import GeminiProvider
10: from src.models.nvidia_provider import NvidiaProvider
11: 
12: logger = logging.getLogger(__name__)
13: 
14: 
15: class NoAvailableModelError(Exception):
16:     """Raised when all model providers fail."""
17:     pass
18: 
19: 
20: class ModelRouter:
21:     """Routes chat and embedding requests across multiple providers with fallback."""
22: 
23:     def __init__(self, config: Config):
24:         self.config = config
25:         self._providers: List[ModelProvider] = []
26:         self._chat_providers: List[ModelProvider] = []
27:         self._embed_providers: List[ModelProvider] = []
28:         self._active_provider: Optional[str] = None
29:         self._build_providers()
30: 
31:     def _build_providers(self) -> None:
32:         """Build provider instances from config."""
33:         for pc in self.config.models.providers:
34:             if not pc.api_key:
35:                 logger.warning(f"Provider '{pc.name}' has no API key, skipping")
36:                 continue
37: 
38:             provider = self._create_provider(pc)
39:             if provider:
40:                 # Store model names on the provider for lookup
41:                 provider._model_names = pc.models
42:                 self._providers.append(provider)
43:                 logger.info(f"Loaded provider: {provider.name()}")
44: 
45:         # Separate chat-capable and embed-capable providers
46:         for p in self._providers:
47:             if "chat" in p._model_names:
48:                 self._chat_providers.append(p)
49:             if "embed" in p._model_names:
50:                 self._embed_providers.append(p)
51: 
52:         if not self._providers:
53:             logger.warning("No model providers loaded")
54: 
55:     def _create_provider(self, pc: ProviderConfig) -> Optional[ModelProvider]:
56:         """Create a provider instance from config."""
57:         try:
58:             if pc.name == "openai":
59:                 return OpenAIProvider(api_key=pc.api_key, base_url=pc.base_url)
60:             elif pc.name == "gemini":
61:                 return GeminiProvider(api_key=pc.api_key)
62:             elif pc.name == "nvidia":
63:                 return NvidiaProvider(api_key=pc.api_key)
64:             else:
65:                 logger.warning(f"Unknown provider type: {pc.name}")
66:                 return None
67:         except Exception as e:
68:             logger.error(f"Failed to create provider '{pc.name}': {e}")
69:             return None
70: 
71:     def chat(self, messages: list, model: str = None) -> str:
72:         """Send chat request with fallback across providers."""
73:         errors = []
74:         for provider in self._chat_providers:
75:             try:
76:                 provider_model = model or provider.name_to_model("chat")
77:                 result = provider.chat(messages, provider_model)
78:                 self._active_provider = provider.name()
79:                 logger.info(f"Chat completed via {provider.name()}")
80:                 return result
81:             except Exception as e:
82:                 errors.append(f"{provider.name()}: {e}")
83:                 logger.warning(f"Provider {provider.name()} failed: {e}")
84: 
85:         raise NoAvailableModelError(
86:             f"All chat providers failed: {'; '.join(errors)}"
87:         )
88: 
89:     def embed(self, text: str, model: str = None) -> List[float]:
90:         """Generate embedding with fallback across providers."""
91:         errors = []
92:         for provider in self._embed_providers:
93:             try:
94:                 provider_model = model or provider.name_to_model("embed")
95:                 result = provider.embed(text, provider_model)
96:                 self._active_provider = provider.name()
97:                 logger.info(f"Embedding generated via {provider.name()}")
98:                 return result
99:             except Exception as e:
100: errors.append(f"{provider.name()}: {e}")
101: logger.warning(f"Provider {provider.name()} embed failed: {e}")
102:
103: raise NoAvailableModelError(
104: f"All embedding providers failed: {'; '.join(errors)}"
105: )
106:
107: @property
108: def active_provider(self) -> Optional[str]:
109: """Return the name of the last successful provider."""
110: return self._active_provider
111:
112: @property
113: def available_providers(self) -> List[str]:
114: """Return list of available provider names."""
115: return [p.name() for p in self._providers]
