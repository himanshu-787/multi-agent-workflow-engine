from langgraph.graph import END, START, StateGraph

from app.agents.coder import make_coder
from app.agents.critic import make_critic
from app.agents.executor import make_executor
from app.agents.llm import get_llm
from app.agents.researcher import make_researcher
from app.config import settings
from app.graph.state import WorkflowState
from app.hitl.approval import human_review_node


def finalize(state: WorkflowState) -> dict:
    if state.get("final_status") in ("approved", "rejected_by_human"):
        return {}
    status = "approved" if state.get("approved") else "max_iterations_reached"
    return {"final_status": status}


def make_router(max_iterations: int, require_human_approval: bool = False):
    def route_after_critic(state: WorkflowState) -> str:
        if state.get("approved"):
            return "human_review" if require_human_approval else "finalize"
        if state.get("iterations", 0) >= max_iterations:
            return "finalize"  # safety valve: iteration limit reached
        return "coder"  # cyclic loop

    return route_after_critic


def make_human_router(max_iterations: int):
    def route_after_human(state: WorkflowState) -> str:
        if state.get("approved"):
            return "finalize"
        # If human rejected with feedback and iteration limit not reached, loop back
        if state.get("iterations", 0) < max_iterations:
            return "coder"
        return "finalize"

    return route_after_human


def build_graph(
    llm=None,
    max_iterations: int | None = None,
    checkpointer=None,
    interrupt_before: list[str] | None = None,
    enable_tools: bool = True,
    tool_registry=None,
    require_human_approval: bool = False,
):
    llm = llm or get_llm()
    if max_iterations is None:
        max_iterations = settings.max_critic_iterations

    graph = StateGraph(WorkflowState)
    graph.add_node("researcher", make_researcher(llm))
    graph.add_node("coder", make_coder(llm))
    graph.add_node("critic", make_critic(llm))
    graph.add_node("finalize", finalize)

    if require_human_approval:
        graph.add_node("human_review", human_review_node)

    graph.add_edge(START, "researcher")

    if enable_tools:
        graph.add_node("executor", make_executor(tool_registry))
        graph.add_edge("researcher", "coder")
        graph.add_edge("coder", "executor")
        graph.add_edge("executor", "critic")
    else:
        graph.add_edge("researcher", "coder")
        graph.add_edge("coder", "critic")

    # Routing destinations after critic
    critic_destinations = {"coder": "coder", "finalize": "finalize"}
    if require_human_approval:
        critic_destinations["human_review"] = "human_review"

    graph.add_conditional_edges(
        "critic",
        make_router(max_iterations, require_human_approval=require_human_approval),
        critic_destinations,
    )

    if require_human_approval:
        graph.add_conditional_edges(
            "human_review",
            make_human_router(max_iterations),
            {"coder": "coder", "finalize": "finalize"},
        )

    graph.add_edge("finalize", END)

    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if interrupt_before is not None:
        compile_kwargs["interrupt_before"] = interrupt_before
    elif require_human_approval and checkpointer is not None:
        compile_kwargs["interrupt_before"] = ["human_review"]

    return graph.compile(**compile_kwargs)
