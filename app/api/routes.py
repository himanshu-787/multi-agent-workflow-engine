from fastapi import APIRouter, HTTPException, Query
from app.api.models import (
    MemorySearchResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    WorkflowApprovalRequest,
    WorkflowApprovalResponse,
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
)
from app.api.service import default_workflow_service
from app.memory.store import default_memory_store
from app.tools.registry import default_registry

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowStartResponse)
async def start_workflow(req: WorkflowStartRequest):
    """Start an autonomous multi-agent workflow."""
    try:
        result = default_workflow_service.start_workflow(
            task=req.task,
            require_human_approval=req.require_human_approval,
            max_iterations=req.max_critic_iterations,
            enable_tools=req.enable_tools,
            enable_memory=req.enable_memory,
        )
        return WorkflowStartResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(thread_id: str):
    """Retrieve status, snapshot, and output of a workflow by thread ID."""
    status = default_workflow_service.get_workflow_status(thread_id)
    if not status:
        raise HTTPException(
            status_code=404, detail=f"Workflow thread '{thread_id}' not found."
        )
    return WorkflowStatusResponse(**status)


@router.post("/{thread_id}/approve", response_model=WorkflowApprovalResponse)
async def approve_workflow(thread_id: str, req: WorkflowApprovalRequest):
    """Submit human review decision (approve or reject) and resume execution."""
    try:
        result = default_workflow_service.approve_workflow(
            thread_id=thread_id,
            approved=req.approved,
            feedback=req.feedback,
        )
        return WorkflowApprovalResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}/history")
async def get_workflow_history(thread_id: str):
    """Retrieve checkpoint history and state transitions for a workflow."""
    history = default_workflow_service.get_workflow_history(thread_id)
    return {"thread_id": thread_id, "checkpoints": history}


# Additional Utility Routes
memory_router = APIRouter(prefix="/memory", tags=["Memory"])


@memory_router.get("/search", response_model=MemorySearchResponse)
async def search_memory(q: str = Query(..., description="Query text to search for"), limit: int = 3):
    """Query long-term memory for similar tasks and past code solutions."""
    results = default_memory_store.search(q, n_results=limit)
    return MemorySearchResponse(query=q, results=results)


tools_router = APIRouter(prefix="/tools", tags=["Tools"])


@tools_router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(req: ToolExecutionRequest):
    """Execute a registered tool directly with strict Pydantic validation."""
    result = default_registry.execute(req.tool_name, **req.arguments)
    return ToolExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
    )
