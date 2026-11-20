from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import CODER_SYSTEM
from app.agents.utils import strip_code_fences
from app.graph.state import WorkflowState


def make_coder(llm):
    def coder(state: WorkflowState) -> dict:
        prompt = (
            f"Task:\n{state['task']}\n\n"
            f"Research notes:\n{state.get('research_notes', '(none)')}\n"
        )
        if state.get("code") and state.get("critique"):
            prompt += (
                f"\nYour previous attempt:\n```python\n{state['code']}\n```\n"
                f"\nReviewer critique to address:\n{state['critique']}\n"
            )
        if state.get("execution_result"):
            prompt += (
                f"\nExecution stdout / stderr / errors from previous attempt:\n"
                f"{state['execution_result']}\n"
            )
        if state.get("human_feedback"):
            prompt += (
                f"\nHuman reviewer feedback to incorporate:\n"
                f"{state['human_feedback']}\n"
            )

        response = llm.invoke(
            [SystemMessage(content=CODER_SYSTEM), HumanMessage(content=prompt)]
        )
        return {"code": strip_code_fences(response.content)}

    return coder
