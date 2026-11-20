from app.graph.builder import build_graph


def test_skeleton_graph_runs():
    graph = build_graph()
    result = graph.invoke({"task": "write a hello world script"})
    assert result["approved"] is True
    assert result["iterations"] == 1
    assert "hello" in result["code"]
