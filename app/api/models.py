from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStartRequest(BaseModel):
    task: str = Field(description="The task description for the multi-agent team.")
    require_human_approval: bool = Field(
        default=False, description="Pause for human review before finalization."
    )
    max_critic_iterations: int = Field(
        default=3, ge=1, le=10, description="Maximum critic rejection loops."
    )
    enable_tools: bool = Field(
        default=True, description="Enable code executor and tools."
    )
    enable_memory: bool = Field(
        default=True, description="Enable long-term ChromaDB memory recall."
    )


class WorkflowStartResponse(BaseModel):
    thread_id: str
    status: str
    next_step: Optional[str] = None
    message: str


class WorkflowStatusResponse(BaseModel):
    thread_id: str
    status: str
    next_step: Optional[str] = None
    task: str
    code: Optional[str] = None
    critique: Optional[str] = None
    execution_result: Optional[str] = None
    iterations: int = 0


class WorkflowApprovalRequest(BaseModel):
    approved: bool = Field(description="Approval decision from the human operator.")
    feedback: Optional[str] = Field(
        default=None, description="Optional revision instructions or comments."
    )


class WorkflowApprovalResponse(BaseModel):
    thread_id: str
    status: str
    message: str
    final_code: Optional[str] = None


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


class MemorySearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
