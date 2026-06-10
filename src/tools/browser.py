 1: """Web page scraping tool."""
 2: 
 3: import logging
 4: import re
 5: import subprocess
 6: 
 7: from src.tools.base_tool import Tool, ToolResult
 8: 
 9: logger = logging.getLogger(__name__)
10: 
11: 
12: class BrowserTool(Tool):
13:     """Scrape web pages using curl."""
14: 
15:     @property
16:     def name(self) -> str:
17:         return "browser"
18: 
19:     @property
20:     def description(self) -> str:
21:         return "Fetch and extract text content from a web page. Returns cleaned plain text."
22: 
23:     def execute(self, url: str, **kwargs) -> ToolResult:
24:         """Fetch web page and extract text."""
25:         try:
26:             result = subprocess.run(
27:                 ["curl", "-sL", "--max-time", "15",
28:                  "-A", "MiniBot/1.0",
29:                  url],
30:                 capture_output=True,
31:                 text=True,
32:                 timeout=20,
33:             )
34: 
35:             if result.returncode != 0:
36:                 return ToolResult(
37:                     success=False,
38:                     output="",
39:                     error=f"curl failed: {result.stderr[:200]}",
40:                 )
41: 
42:             html = result.stdout
43:             text = self._html_to_text(html)
44: 
45:             # Truncate if too long
46:             max_len = 10000
47:             if len(text) > max_len:
48:                 text = text[:max_len] + "\n... [content truncated]"
49: 
50:             return ToolResult(success=True, output=text)
51: 
52:         except subprocess.TimeoutExpired:
53:             return ToolResult(success=False, output="", error="Page fetch timed out")
54:         except Exception as e:
55:             return ToolResult(success=False, output="", error=str(e))
56: 
57:     def _html_to_text(self, html: str) -> str:
58:         """Convert HTML to plain text."""
59:         # Remove script and style contents
60:         html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
61:         html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
62: 
63:         # Remove HTML tags
64:         text = re.sub(r"<[^>]+>", " ", html)
65: 
66:         # Clean up whitespace
67:         text = re.sub(r"\s+", " ", text)
68:         text = re.sub(r"\n\s*", "\n", text)
69: 
70:         # Remove excessive blank lines
71:         text = re.sub(r"\n{3,}", "\n\n", text)
72: 
73:         return text.strip()
