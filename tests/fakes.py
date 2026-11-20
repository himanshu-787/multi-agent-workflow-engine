from langchain_core.messages import AIMessage

from app.agents.schemas import CriticVerdict


def approve() -> CriticVerdict:
    return CriticVerdict(approved=True, feedback="Looks correct.", issues=[])


def reject(msg: str = "Handle empty input.") -> CriticVerdict:
    return CriticVerdict(approved=False, feedback=msg, issues=[msg])


class _FakeStructured:
    def __init__(self, verdicts: list):
        self._verdicts = verdicts

    def invoke(self, messages):
        return self._verdicts.pop(0)


class FakeLLM:
    """Returns canned text for plain calls and scripted verdicts for structured calls."""

    def __init__(self, verdicts: list):
        self.verdicts = list(verdicts)
        self.plain_calls = 0

    def invoke(self, messages):
        self.plain_calls += 1
        return AIMessage(content="```python\ndef add(a, b):\n    return a + b\n```")

    def with_structured_output(self, schema):
        return _FakeStructured(self.verdicts)
