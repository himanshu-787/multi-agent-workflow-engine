import sys

from app.graph.builder import build_graph


def main() -> None:
    task = " ".join(sys.argv[1:]) or (
        "Write a Python function is_palindrome(s) that ignores case, spaces and punctuation."
    )
    graph = build_graph()

    final: dict = {}
    for update in graph.stream({"task": task}, stream_mode="updates"):
        for node, delta in update.items():
            print(f"\n=== {node} ===")
            for key, value in delta.items():
                print(f"{key}: {str(value)[:300]}")
            final.update(delta)

    print("\n" + "=" * 40)
    print(f"Status: {final.get('final_status')}  |  Iterations: {final.get('iterations')}")
    print(f"\nFinal code:\n{final.get('code')}")


if __name__ == "__main__":
    main()
