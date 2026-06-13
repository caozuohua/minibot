"""Tool registry — manages all available tools."""

import logging

from src.config import Config
from src.tools.base_tool import Tool, ToolResult
from src.tools.browser import BrowserTool
from src.tools.file_ops import EditFileTool, ReadFileTool, WriteFileTool
from src.tools.search import SearchTool
from src.tools.shell import ShellTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools for the agent."""

    def __init__(self, config: Config):
        self.config = config.tools
        self._tools: dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register all built-in tools."""
        work_dir = self.config.work_dir

        self.register(
            ShellTool(
                timeout=self.config.shell_timeout,
                max_output=self.config.output_max_bytes,
                work_dir=work_dir,
            )
        )
        self.register(
            SearchTool(
                backend=self.config.search_backend,
                api_key=self.config.search_api_key,
            )
        )
        self.register(ReadFileTool(work_dir=work_dir))
        self.register(WriteFileTool(work_dir=work_dir))
        self.register(EditFileTool(work_dir=work_dir))
        self.register(BrowserTool())

        logger.info(f"Registered {len(self._tools)} tools")

    def register(self, tool: Tool):
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def call(self, name: str, **kwargs) -> ToolResult:
        """Call a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=(
                    f"Unknown tool: {name}. Available: {', '.join(self._tools.keys())}"
                ),
            )

        logger.info(f"Calling tool: {name}")
        result = tool.execute(**kwargs)
        logger.info(f"Tool {name} result: success={result.success}")
        return result

    def list_tools(self) -> list[dict]:
        """List all available tools with descriptions."""
        return [tool.to_dict() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())

    def format_for_prompt(self) -> str:
        """Format tools as a prompt-friendly string for the LLM."""
        lines = ["Available tools:"]
        for tool in self._tools.values():
            lines.append(f"  - {tool.name}: {tool.description}")
        return "\n".join(lines)
