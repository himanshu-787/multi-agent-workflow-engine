from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import RESEARCHER_SYSTEM
from app.graph.state import WorkflowState


def make_researcher(llm):
    def researcher(state: WorkflowState) -> dict:
        prompt = f"Task: {state['task']}"
        if state.get("memory_context"):
            prompt += f"\n\nRelevant past solutions & context:\n{state['memory_context']}"

        response = llm.invoke(
            [
                SystemMessage(content=RESEARCHER_SYSTEM),
                HumanMessage(content=prompt),
            ]
        )
        return {"research_notes": response.content}

    return researcher
