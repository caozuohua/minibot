 1: """Google Gemini model provider."""
 2: 
 3: import logging
 4: from typing import List, Optional
 5: 
 6: import google.generativeai as genai
 7: 
 8: from src.models.base_provider import ModelProvider
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: 
13: class GeminiProvider(ModelProvider):
14:     """Google Gemini API provider."""
15: 
16:     def __init__(self, api_key: str):
17:         super().__init__()
18:         self.api_key = api_key
19:         genai.configure(api_key=api_key)
20: 
21:     def name(self) -> str:
22:         return "gemini"
23: 
24:     def chat(self, messages: list, model: str = None) -> str:
25:         """Send chat completion request."""
26:         logger.debug(f"[Gemini] chat request, model={model}")
27: 
28:         gemini_model = genai.GenerativeModel(model)
29:         
30:         # Separate system message from conversation
31:         system_instruction = None
32:         conversation = []
33:         for msg in messages:
34:             if msg.get("role") == "system":
35:                 system_instruction = msg.get("content", "")
36:             else:
37:                 conversation.append(msg)
38: 
39:         # Build Gemini contents
40:         contents = []
41:         for msg in conversation:
42:             role = "user" if msg.get("role") == "user" else "model"
43:             contents.append({
44:                 "role": role,
45:                 "parts": [msg.get("content", "")],
46:             })
47: 
48:         config = {
49:             "temperature": 0.7,
50:         }
51:         if system_instruction:
52:             config["system_instruction"] = system_instruction
53: 
54:         response = gemini_model.generate_content(
55:             contents=contents,
56:             generation_config=genai.types.GenerationConfig(**{k: v for k, v in config.items() if k != "system_instruction"}),
57:         )
58: 
59:         content = response.text
60:         logger.debug(f"[Gemini] chat response length: {len(content)} chars")
61:         return content or ""
62: 
63:     def embed(self, text: str, model: str = None) -> List[float]:
64:         """Generate embedding vector."""
65:         logger.debug(f"[Gemini] embed request, model={model}")
66:         embedding = genai.embed_content(model=model, content=text)
67:         values = embedding["values"]
68:         logger.debug(f"[Gemini] embed dimension: {len(values)}")
69:         return values
