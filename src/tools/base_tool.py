1: """Base class for tools."""
 2: 
 3: from abc import ABC, abstractmethod
 4: from dataclasses import dataclass
 5: from typing import Any
 6: 
 7: 
 8: @dataclass
 9: class ToolResult:
10:     """Result of a tool execution."""
11:     success: bool
12:     output: str
13:     error: str = ""
14: 
15: 
16: class Tool(ABC):
17:     """Base class for all tools."""
18: 
19:     @property
20:     @abstractmethod
21:     def name(self) -> str:
22:         """Tool name."""
23:         ...
24: 
25:     @property
26:     @abstractmethod
27:     def description(self) -> str:
28:         """Human-readable description of what this tool does."""
29:         ...
30: 
31:     @abstractmethod
32:     def execute(self, **kwargs) -> ToolResult:
33:         """Execute the tool with given parameters."""
34:         ...
35: 
36:     def to_dict(self) -> dict:
37:         """Serialize tool info for LLM prompt."""
38:         return {
39:             "name": self.name,
40:             "description": self.description,
41:         }
