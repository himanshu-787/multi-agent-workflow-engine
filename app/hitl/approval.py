from pydantic import BaseModel, Field
from app.graph.state import WorkflowState


class HumanApprovalVerdict(BaseModel):
    """Schema for human review approval or rejection."""
    approved: bool = Field(description="True if the human operator approves the workflow output.")
    feedback: str | None = Field(
        default=None, description="Optional feedback or revision requests from the reviewer."
    )


def human_review_node(state: WorkflowState) -> dict:
    """Node executed when human review gate is reached or resumed."""
    # If the operator hasn't yet provided a human feedback or decision, mark as pending
    if state.get("final_status") == "pending_human_review":
        return {}

    # If already reviewed:
    is_approved = state.get("approved", False)
    status = "approved" if is_approved else "rejected_by_human"
    return {
        "final_status": status,
        "approved": is_approved,
    }
