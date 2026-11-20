import re

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def strip_code_fences(text: str) -> str:
    """Return the contents of the first fenced code block, or the text unchanged."""
    match = _FENCE.search(text)
    return (match.group(1) if match else text).strip()
