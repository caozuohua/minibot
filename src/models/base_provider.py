 1: """Abstract base class for model providers."""
 2: 
 3: from abc import ABC, abstractmethod
 4: from typing import List, Optional
 5: 
 6: 
 7: class ModelProvider(ABC):
 8:     """Base class for all model providers."""
 9: 
10:     @abstractmethod
11:     def name(self) -> str:
12:         """Return provider name (e.g., 'openai', 'gemini')."""
13:         ...
14: 
15:     @abstractmethod
16:     def chat(self, messages: list, model: str = None) -> str:
17:         """Send chat completion request.
18:         
19:         Args:
20:             messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
21:             model: Optional model override.
22:         
23:         Returns:
24:             Assistant response text.
25:         """
26:         ...
27: 
28:     def __init__(self):
29:         self._model_names = {}
30: 
31:     def name_to_model(self, task: str) -> Optional[str]:
32:         """Return default model name for a task ('chat' or 'embed')."""
33:         return self._model_names.get(task)
34: 
35:     @abstractmethod
36:     def embed(self, text: str, model: str = None) -> List[float]:
37:         """Generate embedding vector.
38:         
39:         Args:
40:             text: Input text.
41:             model: Optional model override.
42:         
43:         Returns:
44:             Embedding vector as list of floats.
45:         """
46:         ...
