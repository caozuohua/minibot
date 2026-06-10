 1: """Shell command execution tool with safety restrictions."""
 2: 
 3: import logging
 4: import os
 5: import re
 6: import subprocess
 7: from typing import Optional
 8: 
 9: from src.tools.base_tool import Tool, ToolResult
10: 
11: logger = logging.getLogger(__name__)
12: 
13: # Dangerous commands that are never allowed
14: BLACKLIST_PATTERNS = [
15:     r"^\s*rm\s+-rf\s+/",
16:     r"^\s*format\s+",
17:     r"^\s*mkfs",
18:     r"^\s*dd\s+if=/dev/zero",
19:     r"^\s*:\(\)\{\s*:\|:\s&\s*\}",  # fork bomb
20:     r"^\s*curl.*\|.*sh",  # pipe to shell
21:     r"^\s*wget.*\|.*sh",
22:     r"^\s*chmod\s+-R\s+777\s+/[^/]*$",
23:     r"^\s*shutdown",
24:     r"^\s*reboot",
25:     r"^\s*halt",
26: ]
27: 
28: 
29: class ShellTool(Tool):
30:     """Execute shell commands with safety restrictions."""
31: 
32:     def __init__(self, timeout: int = 30, max_output: int = 10240, work_dir: str = "."):
33:         self.timeout = timeout
34:         self.max_output = max_output
35:         self.work_dir = os.path.abspath(work_dir)
36: 
37:     @property
38:     def name(self) -> str:
39:         return "shell"
40: 
41:     @property
42:     def description(self) -> str:
43:         return "Execute a shell command on the system. Use for system operations, file management, and running programs."
44: 
45:     def _is_blacklisted(self, command: str) -> bool:
46:         """Check if command matches any blacklist pattern."""
47:         for pattern in BLACKLIST_PATTERNS:
48:             if re.search(pattern, command, re.IGNORECASE):
49:                 return True
50:         return False
51: 
52:     def execute(self, command: str, **kwargs) -> ToolResult:
53:         """Execute a shell command."""
54:         # Safety check
55:         if self._is_blacklisted(command):
56:             return ToolResult(
57:                 success=False,
58:                 output="",
59:                 error=f"Command blocked by safety filter: {command[:50]}",
60:             )
61: 
62:         try:
63:             result = subprocess.run(
64:                 command,
65:                 shell=True,
66:                 capture_output=True,
67:                 text=True,
68:                 timeout=self.timeout,
69:                 cwd=self.work_dir,
70:             )
71: 
72:             output = result.stdout + result.stderr
73:             # Truncate if too long
74:             if len(output) > self.max_output:
75:                 output = output[:self.max_output] + "\n... [output truncated]"
76: 
77:             success = result.returncode == 0
78:             error_msg = result.stderr.strip() if not success else ""
79: 
80:             return ToolResult(
81:                 success=success,
82:                 output=output.strip(),
83:                 error=error_msg,
84:             )
85: 
86:         except subprocess.TimeoutExpired:
87:             return ToolResult(
88:                 success=False,
89:                 output="",
90:                 error=f"Command timed out after {self.timeout}s",
91:             )
92:         except Exception as e:
93:             return ToolResult(
94:                 success=False,
95:                 output="",
96:                 error=str(e),
97:             )
