from app.graph.state import WorkflowState
from app.tools.registry import default_registry


def make_executor(registry=None):
    reg = registry or default_registry

    def executor(state: WorkflowState) -> dict:
        code = state.get("code", "")
        if not code:
            return {"execution_result": "No code provided to execute."}

        # Run code via CodeExecutorTool
        result = reg.execute("code_executor", code=code, timeout_seconds=5)
        if result.success:
            return {"execution_result": f"[SUCCESS] Output:\n{result.output}"}
        else:
            return {"execution_result": f"[FAILED] {result.error}"}

    return executor
