import subprocess
import sys
from pydantic import BaseModel, Field

from app.tools.base import BaseToolWrapper, ToolResult


class CodeExecutionInput(BaseModel):
    code: str = Field(description="Executable Python code string.")
    timeout_seconds: int = Field(
        default=5, ge=1, le=30, description="Maximum execution timeout in seconds."
    )


class CodeExecutorTool(BaseToolWrapper):
    name = "code_executor"
    description = (
        "Safely executes Python code in an isolated subprocess and returns stdout, "
        "stderr, and execution status."
    )
    args_schema = CodeExecutionInput

    def run(self, code: str, timeout_seconds: int = 5) -> ToolResult:
        try:
            process = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            if process.returncode == 0:
                output = stdout if stdout else "Code executed successfully with no output."
                return ToolResult(success=True, output=output, error=None)
            else:
                combined_err = f"{stderr}\n{stdout}".strip()
                return ToolResult(
                    success=False,
                    output=stdout,
                    error=f"Process exited with code {process.returncode}:\n{combined_err}",
                )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout_seconds} seconds.",
            )
        except Exception as e:
            return ToolResult(
                success=False, output="", error=f"Execution error: {str(e)}"
            )
