from langgraph.graph import StateGraph, START, END
from app.graph.state import WorkflowState


def researcher(state: WorkflowState) -> dict:
    return {"research_notes": f"[stub] research for: {state['task']}"}


def coder(state: WorkflowState) -> dict:
    return {"code": "print('hello world')"}


def critic(state: WorkflowState) -> dict:
    return {
        "approved": True,
        "critique": "[stub] looks fine",
        "iterations": state.get("iterations", 0) + 1,
    }


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("researcher", researcher)
    graph.add_node("coder", coder)
    graph.add_node("critic", critic)

    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "coder")
    graph.add_edge("coder", "critic")
    graph.add_edge("critic", END)
    return graph.compile()
