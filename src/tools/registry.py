 1: """Tool registry — manages all available tools."""
 2: 
 3: import logging
 4: from typing import Dict, List, Optional
 5: 
 6: from src.config import Config
 7: from src.tools.base_tool import Tool, ToolResult
 8: from src.tools.shell import ShellTool
 9: from src.tools.search import SearchTool
10: from src.tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
11: from src.tools.browser import BrowserTool
12: 
13: logger = logging.getLogger(__name__)
14: 
15: 
16: class ToolRegistry:
17:     """Registry of available tools for the agent."""
18: 
19:     def __init__(self, config: Config):
20:         self.config = config.tools
21:         self._tools: Dict[str, Tool] = {}
22:         self._register_defaults()
23: 
24:     def _register_defaults(self):
25:         """Register all built-in tools."""
26:         work_dir = self.config.work_dir
27: 
28:         self.register(ShellTool(
29:             timeout=self.config.shell_timeout,
30:             max_output=self.config.output_max_bytes,
31:             work_dir=work_dir,
32:         ))
33:         self.register(SearchTool(
34:             backend=self.config.search_backend,
35:             api_key=self.config.search_api_key,
36:         ))
37:         self.register(ReadFileTool(work_dir=work_dir))
38:         self.register(WriteFileTool(work_dir=work_dir))
39:         self.register(EditFileTool(work_dir=work_dir))
40:         self.register(BrowserTool())
41: 
42:         logger.info(f"Registered {len(self._tools)} tools")
43: 
44:     def register(self, tool: Tool):
45:         """Register a tool."""
46:         self._tools[tool.name] = tool
47:         logger.debug(f"Registered tool: {tool.name}")
48: 
49:     def call(self, name: str, **kwargs) -> ToolResult:
50:         """Call a tool by name."""
51:         tool = self._tools.get(name)
52:         if not tool:
53:             return ToolResult(
54:                 success=False,
55:                 output="",
56:                 error=f"Unknown tool: {name}. Available: {', '.join(self._tools.keys())}",
57:             )
58: 
59:         logger.info(f"Calling tool: {name}")
60:         result = tool.execute(**kwargs)
61:         logger.info(f"Tool {name} result: success={result.success}")
62:         return result
63: 
64:     def list_tools(self) -> List[dict]:
65:         """List all available tools with descriptions."""
66:         return [tool.to_dict() for tool in self._tools.values()]
67: 
68:     def get_tool_names(self) -> List[str]:
69:         """Return list of registered tool names."""
70:         return list(self._tools.keys())
71: 
72:     def format_for_prompt(self) -> str:
73:         """Format tools as a prompt-friendly string for the LLM."""
74:         lines = ["Available tools:"]
75:         for tool in self._tools.values():
76:             lines.append(f"  - {tool.name}: {tool.description}")
77:         return "\n".join(lines)
