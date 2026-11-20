from app.agents.utils import strip_code_fences
from app.graph.builder import build_graph
from tests.fakes import FakeLLM, approve, reject


def test_approved_on_first_try():
    llm = FakeLLM([approve()])
    result = build_graph(llm=llm, max_iterations=3).invoke({"task": "add two numbers"})

    assert result["approved"] is True
    assert result["iterations"] == 1
    assert result["final_status"] == "approved"
    assert "def add" in result["code"]
    assert llm.plain_calls == 2  # researcher + coder


def test_critic_rejection_loops_back_to_coder():
    llm = FakeLLM([reject(), approve()])
    result = build_graph(llm=llm, max_iterations=3).invoke({"task": "add two numbers"})

    assert result["iterations"] == 2
    assert result["final_status"] == "approved"
    assert llm.plain_calls == 3  # researcher + coder + coder (retry)


def test_loop_stops_at_max_iterations():
    llm = FakeLLM([reject()] * 10)
    result = build_graph(llm=llm, max_iterations=2).invoke({"task": "add two numbers"})

    assert result["approved"] is False
    assert result["iterations"] == 2
    assert result["final_status"] == "max_iterations_reached"


def test_strip_code_fences():
    assert strip_code_fences("```python\nx = 1\n```") == "x = 1"
    assert strip_code_fences("x = 1") == "x = 1"
