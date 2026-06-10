 1: """Search API tool with multiple backend support."""
 2: 
 3: import logging
 4: from typing import Optional
 5: 
 6: import requests
 7: 
 8: from src.tools.base_tool import Tool, ToolResult
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: 
13: class SearchTool(Tool):
14:     """Search the web using various search backends."""
15: 
16:     def __init__(self, backend: str = "tavily", api_key: str = ""):
17:         self.backend = backend
18:         self.api_key = api_key
19: 
20:     @property
21:     def name(self) -> str:
22:         return "search"
23: 
24:     @property
25:     def description(self) -> str:
26:         return "Search the web for information. Returns relevant search results with titles, snippets, and URLs."
27: 
28:     def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
29:         """Search the web."""
30:         try:
31:             if self.backend == "tavily":
32:                 return self._tavily_search(query, max_results)
33:             elif self.backend == "searxng":
34:                 return self._searxng_search(query, max_results)
35:             elif self.backend == "google":
36:                 return self._google_search(query, max_results)
37:             else:
38:                 return ToolResult(
39:                     success=False,
40:                     output="",
41:                     error=f"Unknown search backend: {self.backend}",
42:                 )
43:         except Exception as e:
44:             return ToolResult(
45:                 success=False,
46:                 output="",
47:                 error=str(e),
48:             )
49: 
50:     def _tavily_search(self, query: str, max_results: int) -> ToolResult:
51:         """Search using Tavily API."""
52:         if not self.api_key:
53:             return ToolResult(success=False, output="", error="Tavily API key not configured")
54: 
55:         response = requests.post(
56:             "https://api.tavily.com/search",
57:             json={
58:                 "query": query,
59:                 "max_results": max_results,
60:                 "search_depth": "basic",
61:             },
62:             headers={"Authorization": f"Bearer {self.api_key}"},
63:             timeout=15,
64:         )
65:         response.raise_for_status()
66:         data = response.json()
67: 
68:         results = []
69:         for r in data.get("results", [])[:max_results]:
70:             results.append(
71:                 f"Title: {r.get('title', 'N/A')}\n"
72:                 f"URL: {r.get('url', 'N/A')}\n"
73:                 f"Snippet: {r.get('content', 'N/A')}\n"
74:             )
75: 
76:         return ToolResult(
77:             success=True,
78:             output="\n---\n".join(results) if results else "No results found.",
79:         )
80: 
81:     def _searxng_search(self, query: str, max_results: int) -> ToolResult:
82:         """Search using SearXNG instance."""
83:         # Default to public instance; configure via base_url for self-hosted
84:         base_url = "https://searx.be"
85:         response = requests.get(
86:             f"{base_url}/search",
87:             params={"q": query, "format": "json"},
88:             timeout=15,
89:         )
90:         response.raise_for_status()
91:         data = response.json()
92: 
93:         results = []
94:         for r in data.get("results", [])[:max_results]:
95:             results.append(
96:                 f"Title: {r.get('title', 'N/A')}\n"
97:                 f"URL: {r.get('url', 'N/A')}\n"
98:                 f"Snippet: {r.get('content', 'N/A')}\n"
99:             )
100:
101: return ToolResult(
102: success=True,
103: output="\n---\n".join(results) if results else "No results found.",
104: )
105:
106: def _google_search(self, query: str, max_results: int) -> ToolResult:
107: """Search using Google Custom Search API."""
108: if not self.api_key:
109: return ToolResult(success=False, output="", error="Google API key not configured")
110:
111: # Requires both API key and CX ID
112: import os
113: cx = os.environ.get("GOOGLE_CX_ID", "")
114: if not cx:
115: return ToolResult(success=False, output="", error="GOOGLE_CX_ID not configured")
116:
117: response = requests.get(
118: "https://www.googleapis.com/customsearch/v1",
119: params={
120: "key": self.api_key,
121: "cx": cx,
122: "q": query,
123: "num": max_results,
124: },
125: timeout=15,
126: )
127: response.raise_for_status()
128: data = response.json()
129:
130: results = []
131: for r in data.get("items", [])[:max_results]:
132: results.append(
133: f"Title: {r.get('title', 'N/A')}\n"
134: f"URL: {r.get('link', 'N/A')}\n"
135: f"Snippet: {r.get('snippet', 'N/A')}\n"
136: )
137:
138: return ToolResult(
139: success=True,
140: output="\n---\n".join(results) if results else "No results found.",
141: )
