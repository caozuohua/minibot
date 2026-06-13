"""File operation tools (read, write, edit)."""

import logging
import os

from src.tools.base_tool import Tool, ToolResult

logger = logging.getLogger(__name__)


class ReadFileTool(Tool):
    """Read file contents."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = os.path.abspath(work_dir)

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a file. "
            "Supports large files with offset and limit parameters."
        )

    def execute(
        self, path: str, offset: int = 1, limit: int = 500, **kwargs
    ) -> ToolResult:
        """Read file contents."""
        full_path = self._resolve_path(path)
        if not full_path:
            return ToolResult(
                success=False, output="", error=f"Path outside work directory: {path}"
            )

        try:
            with open(full_path, encoding="utf-8") as f:
                lines = f.readlines()

            total = len(lines)
            start = max(0, offset - 1)
            end = min(total, start + limit)
            chunk = lines[start:end]

            content = "".join(chunk)
            info = f"File: {path} ({total} lines total, showing {start + 1}-{end})\n\n"

            return ToolResult(success=True, output=info + content)

        except FileNotFoundError:
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _resolve_path(self, path: str) -> str | None:
        """Resolve path and ensure it's within work directory."""
        full = path if os.path.isabs(path) else os.path.join(self.work_dir, path)

        full = os.path.realpath(full)
        if not full.startswith(self.work_dir):
            return None
        return full


class WriteFileTool(Tool):
    """Write content to a file."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = os.path.abspath(work_dir)

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Write content to a file. "
            "Creates the file if it doesn't exist. "
            "Creates parent directories as needed."
        )

    def execute(self, path: str, content: str, **kwargs) -> ToolResult:
        """Write content to file."""
        full_path = self._resolve_path(path)
        if not full_path:
            return ToolResult(
                success=False, output="", error=f"Path outside work directory: {path}"
            )

        try:
            # Create parent directories
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {path}",
            )

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _resolve_path(self, path: str) -> str | None:
        """Resolve path and ensure it's within work directory."""
        full = path if os.path.isabs(path) else os.path.join(self.work_dir, path)

        full = os.path.realpath(full)
        if not full.startswith(self.work_dir):
            return None
        return full


class EditFileTool(Tool):
    """Edit file by replacing text."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = os.path.abspath(work_dir)

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Edit a file by replacing exact text. "
            "The old_text must exist exactly once in the file."
        )

    def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> ToolResult:
        """Replace old_text with new_text in file."""
        full_path = self._resolve_path(path)
        if not full_path:
            return ToolResult(
                success=False, output="", error=f"Path outside work directory: {path}"
            )

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            count = content.count(old_text)
            if count == 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"old_text not found in {path}",
                )
            if count > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"old_text found {count} times in {path} (must be unique)",
                )

            new_content = content.replace(old_text, new_text, 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                success=True,
                output=(
                    f"Edited {path}: replaced {len(old_text)} chars "
                    f"with {len(new_text)} chars"
                ),
            )

        except FileNotFoundError:
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _resolve_path(self, path: str) -> str | None:
        """Resolve path and ensure it's within work directory."""
        full = path if os.path.isabs(path) else os.path.join(self.work_dir, path)

        full = os.path.realpath(full)
        if not full.startswith(self.work_dir):
            return None
        return full
