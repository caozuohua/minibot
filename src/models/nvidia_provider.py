 1: """NVIDIA NIM model provider (OpenAI-compatible interface)."""
 2: 
 3: import logging
 4: from typing import List, Optional
 5: 
 6: from openai import OpenAI
 7: 
 8: from src.models.base_provider import ModelProvider
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: # NVIDIA NIM base URL
13: NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
14: 
15: 
16: class NvidiaProvider(ModelProvider):
17:     """NVIDIA NIM API provider (embedding models via OpenAI-compatible interface)."""
18: 
19:     def __init__(self, api_key: str, base_url: Optional[str] = None):
20:         super().__init__()
21:         self.api_key = api_key
22:         self._client = OpenAI(
23:             api_key=api_key,
24:             base_url=base_url or NVIDIA_BASE_URL,
25:         )
26: 
27:     def name(self) -> str:
28:         return "nvidia"
29: 
30:     def chat(self, messages: list, model: str = None) -> str:
31:         """NVIDIA NIM currently focuses on embedding models.
32:         
33:         Raises NotImplementedError if chat is not supported.
34:         """
35:         raise NotImplementedError("NVIDIA NIM provider does not support chat completions")
36: 
37:     def embed(self, text: str, model: str = None) -> List[float]:
38:         """Generate embedding vector via NVIDIA NIM."""
39:         logger.debug(f"[NVIDIA] embed request, model={model}")
40:         response = self._client.embeddings.create(
41:             model=model,
42:             input=text,
43:         )
44:         embedding = response.data[0].embedding
45:         logger.debug(f"[NVIDIA] embed dimension: {len(embedding)}")
46:         return embedding
