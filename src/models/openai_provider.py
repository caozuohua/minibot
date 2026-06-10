 1: """OpenAI model provider."""
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
12: 
13: class OpenAIProvider(ModelProvider):
14:     """OpenAI API provider (compatible with any OpenAI-compatible API)."""
15: 
16:     def __init__(self, api_key: str, base_url: Optional[str] = None):
17:         super().__init__()
18:         self.api_key = api_key
19:         self._client = OpenAI(api_key=api_key, base_url=base_url)
20: 
21:     def name(self) -> str:
22:         return "openai"
23: 
24:     def chat(self, messages: list, model: str = None) -> str:
25:         """Send chat completion request."""
26:         logger.debug(f"[OpenAI] chat request, model={model}")
27:         response = self._client.chat.completions.create(
28:             model=model,
29:             messages=messages,
30:             temperature=0.7,
31:         )
32:         content = response.choices[0].message.content
33:         logger.debug(f"[OpenAI] chat response length: {len(content)} chars")
34:         return content or ""
35: 
36:     def embed(self, text: str, model: str = None) -> List[float]:
37:         """Generate embedding vector."""
38:         logger.debug(f"[OpenAI] embed request, model={model}")
39:         response = self._client.embeddings.create(
40:             model=model,
41:             input=text,
42:         )
43:         embedding = response.data[0].embedding
44:         logger.debug(f"[OpenAI] embed dimension: {len(embedding)}")
45:         return embedding
