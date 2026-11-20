import os
from pathlib import Path
from pydantic import BaseModel, Field

from app.tools.base import BaseToolWrapper, ToolResult


class FileReaderInput(BaseModel):
    file_path: str = Field(description="Relative path of the file to read within the workspace.")


class FileWriterInput(BaseModel):
    file_path: str = Field(description="Relative path of the file to write within the workspace.")
    content: str = Field(description="Content to write to the file.")


def _resolve_safe_path(rel_path: str) -> Path:
    base = Path.cwd().resolve()
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Access denied: path '{rel_path}' escapes workspace directory.")
    return target


class FileReaderTool(BaseToolWrapper):
    name = "file_reader"
    description = "Reads text content from a file within the workspace."
    args_schema = FileReaderInput

    def run(self, file_path: str) -> ToolResult:
        try:
            safe_path = _resolve_safe_path(file_path)
            if not safe_path.exists():
                return ToolResult(
                    success=False, output="", error=f"File not found: {file_path}"
                )
            if not safe_path.is_file():
                return ToolResult(
                    success=False, output="", error=f"Path is not a regular file: {file_path}"
                )

            content = safe_path.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content, error=None)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class FileWriterTool(BaseToolWrapper):
    name = "file_writer"
    description = "Writes text content to a file within the workspace."
    args_schema = FileWriterInput

    def run(self, file_path: str, content: str) -> ToolResult:
        try:
            safe_path = _resolve_safe_path(file_path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to {file_path}.",
                error=None,
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
