 1: """File operation tools (read, write, edit)."""
 2: 
 3: import logging
 4: import os
 5: from typing import Optional
 6: 
 7: from src.tools.base_tool import Tool, ToolResult
 8: 
 9: logger = logging.getLogger(__name__)
10: 
11: 
12: class ReadFileTool(Tool):
13:     """Read file contents."""
14: 
15:     def __init__(self, work_dir: str = "."):
16:         self.work_dir = os.path.abspath(work_dir)
17: 
18:     @property
19:     def name(self) -> str:
20:         return "read_file"
21: 
22:     @property
23:     def description(self) -> str:
24:         return "Read the contents of a file. Supports large files with offset and limit parameters."
25: 
26:     def execute(self, path: str, offset: int = 1, limit: int = 500, **kwargs) -> ToolResult:
27:         """Read file contents."""
28:         full_path = self._resolve_path(path)
29:         if not full_path:
30:             return ToolResult(success=False, output="", error=f"Path outside work directory: {path}")
31: 
32:         try:
33:             with open(full_path, "r", encoding="utf-8") as f:
34:                 lines = f.readlines()
35: 
36:             total = len(lines)
37:             start = max(0, offset - 1)
38:             end = min(total, start + limit)
39:             chunk = lines[start:end]
40: 
41:             content = "".join(chunk)
42:             info = f"File: {path} ({total} lines total, showing {start+1}-{end})\n\n"
43: 
44:             return ToolResult(success=True, output=info + content)
45: 
46:         except FileNotFoundError:
47:             return ToolResult(success=False, output="", error=f"File not found: {path}")
48:         except Exception as e:
49:             return ToolResult(success=False, output="", error=str(e))
50: 
51:     def _resolve_path(self, path: str) -> Optional[str]:
52:         """Resolve path and ensure it's within work directory."""
53:         if os.path.isabs(path):
54:             full = path
55:         else:
56:             full = os.path.join(self.work_dir, path)
57: 
58:         full = os.path.realpath(full)
59:         if not full.startswith(self.work_dir):
60:             return None
61:         return full
62: 
63: 
64: class WriteFileTool(Tool):
65:     """Write content to a file."""
66: 
67:     def __init__(self, work_dir: str = "."):
68:         self.work_dir = os.path.abspath(work_dir)
69: 
70:     @property
71:     def name(self) -> str:
72:         return "write_file"
73: 
74:     @property
75:     def description(self) -> str:
76:         return "Write content to a file. Creates the file if it doesn't exist. Creates parent directories as needed."
77: 
78:     def execute(self, path: str, content: str, **kwargs) -> ToolResult:
79:         """Write content to file."""
80:         full_path = self._resolve_path(path)
81:         if not full_path:
82:             return ToolResult(success=False, output="", error=f"Path outside work directory: {path}")
83: 
84:         try:
85:             # Create parent directories
86:             parent = os.path.dirname(full_path)
87:             if parent:
88:                 os.makedirs(parent, exist_ok=True)
89: 
90:             with open(full_path, "w", encoding="utf-8") as f:
91:                 f.write(content)
92: 
93:             return ToolResult(
94:                 success=True,
95:                 output=f"Written {len(content)} bytes to {path}",
96:             )
97: 
98:         except Exception as e:
99:             return ToolResult(success=False, output="", error=str(e))
100:
101: def _resolve_path(self, path: str) -> Optional[str]:
102: if os.path.isabs(path):
103: full = path
104: else:
105: full = os.path.join(self.work_dir, path)
106: full = os.path.realpath(full)
107: if not full.startswith(self.work_dir):
108: return None
109: return full
110:
111:
112: class EditFileTool(Tool):
113: """Edit file by replacing text."""
114:
115: def init(self, work_dir: str = "."):
116: self.work_dir = os.path.abspath(work_dir)
117:
118: @property
119: def name(self) -> str:
120: return "edit_file"
121:
122: @property
123: def description(self) -> str:
124: return "Edit a file by replacing exact text. The old_text must exist exactly once in the file."
125:
126: def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> ToolResult:
127: """Replace old_text with new_text in file."""
128: full_path = self._resolve_path(path)
129: if not full_path:
130: return ToolResult(success=False, output="", error=f"Path outside work directory: {path}")
131:
132: try:
133: with open(full_path, "r", encoding="utf-8") as f:
134: content = f.read()
135:
136: count = content.count(old_text)
137: if count == 0:
138: return ToolResult(
139: success=False,
140: output="",
141: error=f"old_text not found in {path}",
142: )
143: if count > 1:
144: return ToolResult(
145: success=False,
146: output="",
147: error=f"old_text found {count} times in {path} (must be unique)",
148: )
149:
150: new_content = content.replace(old_text, new_text, 1)
151: with open(full_path, "w", encoding="utf-8") as f:
152: f.write(new_content)
153:
154: return ToolResult(
155: success=True,
156: output=f"Edited {path}: replaced {len(old_text)} chars with {len(new_text)} chars",
157: )
158:
159: except FileNotFoundError:
160: return ToolResult(success=False, output="", error=f"File not found: {path}")
161: except Exception as e:
162: return ToolResult(success=False, output="", error=str(e))
163:
164: def _resolve_path(self, path: str) -> Optional[str]:
165: if os.path.isabs(path):
166: full = path
167: else:
168: full = os.path.join(self.work_dir, path)
169: full = os.path.realpath(full)
170: if not full.startswith(self.work_dir):
171: return None
172: return full
