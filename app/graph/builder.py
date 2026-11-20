from langgraph.graph import END, START, StateGraph

from app.agents.coder import make_coder
from app.agents.critic import make_critic
from app.agents.executor import make_executor
from app.agents.llm import get_llm
from app.agents.researcher import make_researcher
from app.config import settings
from app.graph.state import WorkflowState
from app.hitl.approval import human_review_node
from app.memory.store import default_memory_store


def make_finalize(memory_store=None):
    def finalize(state: WorkflowState) -> dict:
        if state.get("final_status") in ("approved", "rejected_by_human"):
            status = state["final_status"]
        else:
            status = "approved" if state.get("approved") else "max_iterations_reached"

        # If approved and memory store available, save to long-term memory
        if status == "approved" and memory_store is not None:
            try:
                memory_store.save_run(
                    task=state.get("task", ""),
                    code=state.get("code", ""),
                    critique=state.get("critique", ""),
                )
            except Exception:
                pass

        return {"final_status": status}

    return finalize


def make_memory_retriever(memory_store):
    def memory_retriever(state: WorkflowState) -> dict:
        task = state.get("task", "")
        if not task or not memory_store:
            return {}
        try:
            matches = memory_store.search(task, n_results=2)
            context = memory_store.format_context(matches)
            return {"memory_context": context}
        except Exception:
            return {"memory_context": ""}

    return memory_retriever


def make_router(max_iterations: int, default_require_human_approval: bool = False):
    def route_after_critic(state: WorkflowState) -> str:
        needs_human = state.get("require_human_approval", default_require_human_approval)
        if state.get("approved"):
            if needs_human:
                return "human_review"
            return "finalize"
        if state.get("iterations", 0) >= max_iterations:
            return "finalize"
        return "coder"

    return route_after_critic


def make_human_router(max_iterations: int):
    def route_after_human(state: WorkflowState) -> str:
        if state.get("approved"):
            return "finalize"
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
    enable_memory: bool = False,
    memory_store=None,
):
    llm = llm or get_llm()
    if max_iterations is None:
        max_iterations = settings.max_critic_iterations

    active_memory = memory_store if (enable_memory and memory_store is not None) else (default_memory_store if enable_memory else None)

    graph = StateGraph(WorkflowState)
    graph.add_node("researcher", make_researcher(llm))
    graph.add_node("coder", make_coder(llm))
    graph.add_node("critic", make_critic(llm))
    graph.add_node("human_review", human_review_node)
    graph.add_node("finalize", make_finalize(active_memory))

    if enable_memory and active_memory is not None:
        graph.add_node("memory_retriever", make_memory_retriever(active_memory))
        graph.add_edge(START, "memory_retriever")
        graph.add_edge("memory_retriever", "researcher")
    else:
        graph.add_edge(START, "researcher")

    if enable_tools:
        graph.add_node("executor", make_executor(tool_registry))
        graph.add_edge("researcher", "coder")
        graph.add_edge("coder", "executor")
        graph.add_edge("executor", "critic")
    else:
        graph.add_edge("researcher", "coder")
        graph.add_edge("coder", "critic")

    graph.add_conditional_edges(
        "critic",
        make_router(max_iterations, default_require_human_approval=require_human_approval),
        {"coder": "coder", "human_review": "human_review", "finalize": "finalize"},
    )

    graph.add_conditional_edges(
        "human_review",
        make_human_router(max_iterations),
        {"coder": "coder", "finalize": "finalize"},
    )

    graph.add_edge("finalize", END)

    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
        # Always interrupt before human_review when checkpointer is present
        compile_kwargs["interrupt_before"] = interrupt_before or ["human_review"]
    elif interrupt_before is not None:
        compile_kwargs["interrupt_before"] = interrupt_before

    return graph.compile(**compile_kwargs)
