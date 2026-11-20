from typing import Any, Dict
from pydantic import ValidationError

from app.tools.base import BaseToolWrapper, ToolResult
from app.tools.calculator import CalculatorTool
from app.tools.code_executor import CodeExecutorTool
from app.tools.file_tools import FileReaderTool, FileWriterTool
from app.tools.search import WebSearchTool


class ToolRegistry:
    """Central registry for managing, validating, and executing tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseToolWrapper] = {}
        # Register default tools
        self.register(CodeExecutorTool())
        self.register(WebSearchTool())
        self.register(FileReaderTool())
        self.register(FileWriterTool())
        self.register(CalculatorTool())

    def register(self, tool: BaseToolWrapper) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseToolWrapper | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' is not registered in ToolRegistry.",
            )

        try:
            # Validate parameters strictly against Pydantic schema
            validated_args = tool.args_schema(**kwargs)
            return tool.run(**validated_args.model_dump())
        except ValidationError as ve:
            return ToolResult(
                success=False,
                output="",
                error=f"Validation error for tool '{tool_name}': {ve.errors()}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution error in tool '{tool_name}': {str(e)}",
            )

    def get_langchain_tools(self) -> list:
        return [tool.to_langchain_tool() for tool in self._tools.values()]


# Default singleton instance
default_registry = ToolRegistry()
