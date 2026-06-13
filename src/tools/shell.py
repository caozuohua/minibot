"""Shell command execution tool with safety restrictions."""

import logging
import os
import re
import subprocess

from src.tools.base_tool import Tool, ToolResult

logger = logging.getLogger(__name__)

# Dangerous commands that are never allowed
BLACKLIST_PATTERNS = [
    r"^\s*rm\s+-rf\s+/",
    r"^\s*format\s+",
    r"^\s*mkfs",
    r"^\s*dd\s+if=/dev/zero",
    r"^\s*:\(\)\{\s*:\|:\s*&\s*\}",  # fork bomb
    r"^\s*curl.*\|.*sh",  # pipe to shell
    r"^\s*wget.*\|.*sh",
    r"^\s*chmod\s+-R\s+777\s+/[^/]*$",
    r"^\s*shutdown",
    r"^\s*reboot",
    r"^\s*halt",
]


class ShellTool(Tool):
    """Execute shell commands with safety restrictions."""

    def __init__(self, timeout: int = 30, max_output: int = 10240, work_dir: str = "."):
        self.timeout = timeout
        self.max_output = max_output
        self.work_dir = os.path.abspath(work_dir)

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command on the system. "
            "Use for system operations, file management, and running programs."
        )

    def _is_blacklisted(self, command: str) -> bool:
        """Check if command matches any blacklist pattern."""
        for pattern in BLACKLIST_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute a shell command."""
        # Safety check
        if self._is_blacklisted(command):
            return ToolResult(
                success=False,
                output="",
                error=f"Command blocked by safety filter: {command[:50]}",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.work_dir,
            )

            output = result.stdout + result.stderr
            # Truncate if too long
            if len(output) > self.max_output:
                output = output[: self.max_output] + "\n... [output truncated]"

            success = result.returncode == 0
            error_msg = result.stderr.strip() if not success else ""

            return ToolResult(
                success=success,
                output=output.strip(),
                error=error_msg,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {self.timeout}s",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )
