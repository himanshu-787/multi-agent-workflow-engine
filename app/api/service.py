import uuid
from typing import Any, Dict, Optional

from app.graph.builder import build_graph
from app.memory.store import default_memory_store
from app.persistence.checkpointer import get_sqlite_checkpointer
from app.tools.registry import default_registry


class WorkflowService:
    def __init__(self, checkpointer=None, memory_store=None, tool_registry=None, llm=None):
        self.checkpointer = checkpointer or get_sqlite_checkpointer()
        self.memory_store = memory_store or default_memory_store
        self.tool_registry = tool_registry or default_registry
        self.llm = llm

    def _get_graph(
        self,
        max_iterations: int = 3,
        enable_tools: bool = True,
        enable_memory: bool = True,
    ):
        return build_graph(
            llm=self.llm,
            max_iterations=max_iterations,
            checkpointer=self.checkpointer,
            enable_tools=enable_tools,
            tool_registry=self.tool_registry,
            enable_memory=enable_memory,
            memory_store=self.memory_store,
        )

    def start_workflow(
        self,
        task: str,
        thread_id: Optional[str] = None,
        require_human_approval: bool = False,
        max_iterations: int = 3,
        enable_tools: bool = True,
        enable_memory: bool = True,
    ) -> Dict[str, Any]:
        tid = thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": tid}}
        graph = self._get_graph(
            max_iterations=max_iterations,
            enable_tools=enable_tools,
            enable_memory=enable_memory,
        )

        initial_state = {
            "task": task,
            "require_human_approval": require_human_approval,
        }
        graph.invoke(initial_state, config=config)

        snapshot = graph.get_state(config)
        next_step = snapshot.next[0] if snapshot.next else None

        if next_step == "human_review":
            status = "pending_human_review"
            message = "Workflow paused at human approval gate."
        else:
            status = snapshot.values.get("final_status", "completed")
            message = f"Workflow completed with status: {status}"

        return {
            "thread_id": tid,
            "status": status,
            "next_step": next_step,
            "message": message,
        }

    def get_workflow_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        config = {"configurable": {"thread_id": thread_id}}
        graph = self._get_graph()
        snapshot = graph.get_state(config)

        if not snapshot or not snapshot.values:
            return None

        values = snapshot.values
        next_step = snapshot.next[0] if snapshot.next else None
        status = values.get("final_status") or (
            "pending_human_review" if next_step == "human_review" else "running"
        )

        return {
            "thread_id": thread_id,
            "status": status,
            "next_step": next_step,
            "task": values.get("task", ""),
            "code": values.get("code"),
            "critique": values.get("critique"),
            "execution_result": values.get("execution_result"),
            "iterations": values.get("iterations", 0),
        }

    def approve_workflow(
        self,
        thread_id: str,
        approved: bool,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        graph = self._get_graph()
        snapshot = graph.get_state(config)

        if not snapshot or not snapshot.values:
            raise ValueError(f"Workflow with thread_id '{thread_id}' not found.")

        # Update state at human_review node
        update_data = {
            "approved": approved,
            "human_feedback": feedback,
            "final_status": "approved" if approved else "rejected_by_human",
        }
        graph.update_state(config, update_data, as_node="human_review")

        # Resume graph execution
        graph.invoke(None, config=config)

        final_snapshot = graph.get_state(config)
        final_values = final_snapshot.values
        return {
            "thread_id": thread_id,
            "status": final_values.get("final_status", "completed"),
            "message": "Approval processed and workflow resumed.",
            "final_code": final_values.get("code"),
        }

    def get_workflow_history(self, thread_id: str) -> list[dict]:
        config = {"configurable": {"thread_id": thread_id}}
        graph = self._get_graph()
        history = []
        for state in graph.get_state_history(config):
            history.append({
                "step": state.metadata.get("step") if state.metadata else None,
                "node": state.metadata.get("node") if state.metadata else None,
                "next": state.next,
                "values": {k: str(v)[:200] for k, v in state.values.items()},
            })
        return history


default_workflow_service = WorkflowService()
