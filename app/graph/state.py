from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict, total=False):
    task: str
    messages: Annotated[list, add_messages]
    research_notes: str
    code: str
    critique: str
    approved: bool
    iterations: int
    final_status: str  # "approved" | "max_iterations_reached" | "pending_human_review" | "rejected_by_human"
    execution_result: str
    human_feedback: str | None
    memory_context: str | None
