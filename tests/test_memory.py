from app.graph.builder import build_graph
from app.memory.embedding import DeterministicFastEmbedding
from app.memory.store import LongTermMemoryStore
from tests.fakes import FakeLLM, approve


def test_deterministic_embedding():
    ef = DeterministicFastEmbedding(dimension=64)
    embeddings = ef(["hello world", "fastapi multi-agent"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 64
    assert len(embeddings[1]) == 64


def test_memory_store_save_and_search():
    store = LongTermMemoryStore(in_memory=True)

    # Empty store search returns empty list
    assert store.search("random query") == []

    # Save a run
    doc_id = store.save_run(
        task="write a binary search function in Python",
        code="def binary_search(arr, x): ...",
        critique="Good O(log n) implementation.",
        metadata={"category": "algorithms"},
    )
    assert doc_id is not None

    # Search for similar task
    results = store.search("binary search", n_results=1)
    assert len(results) == 1
    assert "binary search" in results[0]["document"].lower()

    # Context formatting
    context = store.format_context(results)
    assert "Prior Experience #1" in context
    assert "binary_search" in context


def test_graph_with_memory_recall():
    store = LongTermMemoryStore(in_memory=True)
    # Seed prior memory
    store.save_run(
        task="sort an array using merge sort",
        code="def merge_sort(arr): return sorted(arr)",
        critique="Correct merge sort",
    )

    llm = FakeLLM([approve()])
    graph = build_graph(
        llm=llm,
        enable_memory=True,
        memory_store=store,
        enable_tools=False,
    )

    result = graph.invoke({"task": "sort an array"})
    assert result["final_status"] == "approved"
    assert "memory_context" in result
    assert "merge sort" in result["memory_context"]
