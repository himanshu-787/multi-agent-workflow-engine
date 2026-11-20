from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Standardized tool output structure."""
    success: bool = Field(description="Whether the tool execution succeeded.")
    output: str = Field(description="Output text or return value of the tool.")
    error: str | None = Field(default=None, description="Error message if execution failed.")


class BaseToolWrapper(ABC):
    """Abstract base class for all tools in the orchestrator registry."""
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with validated arguments."""
        pass

    def to_langchain_tool(self):
        """Convert this tool wrapper into a LangChain BaseTool."""
        from langchain_core.tools import StructuredTool

        def sync_fn(**kwargs):
            res = self.run(**kwargs)
            if not res.success:
                return f"Error: {res.error}\nOutput: {res.output}"
            return res.output

        return StructuredTool.from_function(
            func=sync_fn,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )
