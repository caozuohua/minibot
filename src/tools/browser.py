"""Web page scraping tool."""

import logging
import re
import subprocess

from src.tools.base_tool import Tool, ToolResult

logger = logging.getLogger(__name__)


class BrowserTool(Tool):
    """Scrape web pages using curl."""

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Fetch and extract text content from a web page. Returns cleaned plain text."

    def execute(self, url: str, **kwargs) -> ToolResult:
        """Fetch web page and extract text."""
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sL",
                    "--max-time",
                    "15",
                    "-A",
                    "MiniBot/1.0",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"curl failed: {result.stderr[:200]}",
                )

            html = result.stdout
            text = self._html_to_text(html)

            # Truncate if too long
            max_len = 10000
            if len(text) > max_len:
                text = text[:max_len] + "\n... [content truncated]"

            return ToolResult(success=True, output=text)

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Page fetch timed out")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove script and style contents
        html = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*", "\n", text)

        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
