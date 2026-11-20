import sqlite3
from app.graph.builder import build_graph
from app.persistence.checkpointer import get_memory_checkpointer
from tests.fakes import FakeLLM, approve, reject


def test_checkpointing_saves_state():
    checkpointer = get_memory_checkpointer()
    llm = FakeLLM([approve()])
    graph = build_graph(
        llm=llm,
        checkpointer=checkpointer,
        enable_tools=False,
    )

    config = {"configurable": {"thread_id": "test-thread-checkpoint"}}
    result = graph.invoke({"task": "build an API"}, config=config)

    assert result["final_status"] == "approved"
    snapshot = graph.get_state(config)
    assert snapshot.values["final_status"] == "approved"
    assert "def add" in snapshot.values["code"]


def test_hitl_interrupts_before_human_review():
    checkpointer = get_memory_checkpointer()
    llm = FakeLLM([approve()])
    graph = build_graph(
        llm=llm,
        checkpointer=checkpointer,
        require_human_approval=True,
        enable_tools=False,
    )

    config = {"configurable": {"thread_id": "test-thread-hitl-pause"}}
    # Initial run: Critic approves, graph pauses before 'human_review'
    graph.invoke({"task": "create a database script"}, config=config)

    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)
    assert snapshot.values["approved"] is True
    assert "code" in snapshot.values


def test_hitl_resume_on_approval():
    checkpointer = get_memory_checkpointer()
    llm = FakeLLM([approve()])
    graph = build_graph(
        llm=llm,
        checkpointer=checkpointer,
        require_human_approval=True,
        enable_tools=False,
    )

    config = {"configurable": {"thread_id": "test-thread-hitl-resume"}}
    graph.invoke({"task": "create a queue worker"}, config=config)

    # Verify paused
    assert graph.get_state(config).next == ("human_review",)

    # Simulate Human approval
    graph.update_state(
        config,
        {"approved": True, "human_feedback": "Code looks production-ready."},
        as_node="human_review",
    )

    # Resume graph execution
    final = graph.invoke(None, config=config)
    assert final["approved"] is True
    assert final["final_status"] == "approved"
    assert graph.get_state(config).next == ()


def test_hitl_resume_on_rejection_loops_to_coder():
    checkpointer = get_memory_checkpointer()
    # First critic approves, human rejects, second critic approves
    llm = FakeLLM([approve(), approve()])
    graph = build_graph(
        llm=llm,
        checkpointer=checkpointer,
        require_human_approval=True,
        enable_tools=False,
        max_iterations=3,
    )

    config = {"configurable": {"thread_id": "test-thread-hitl-reject"}}
    graph.invoke({"task": "create a rate limiter"}, config=config)

    # Paused before human review
    assert graph.get_state(config).next == ("human_review",)

    # Human rejects and asks for retry
    graph.update_state(
        config,
        {"approved": False, "human_feedback": "Please add docstrings and type annotations."},
        as_node="human_review",
    )

    # Resume graph execution: loops to coder -> critic -> human_review
    resumed = graph.invoke(None, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.values["iterations"] >= 1
