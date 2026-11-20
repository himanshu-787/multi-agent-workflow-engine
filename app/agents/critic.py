from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import CRITIC_SYSTEM
from app.agents.schemas import CriticVerdict
from app.graph.state import WorkflowState


def make_critic(llm):
    structured_llm = llm.with_structured_output(CriticVerdict)

    def critic(state: WorkflowState) -> dict:
        prompt = (
            f"Task:\n{state['task']}\n\n"
            f"Code to review:\n```python\n{state.get('code', '')}\n```"
        )
        if state.get("execution_result"):
            prompt += (
                f"\n\nTool execution stdout/stderr/test result:\n"
                f"{state['execution_result']}"
            )

        verdict: CriticVerdict = structured_llm.invoke(
            [
                SystemMessage(content=CRITIC_SYSTEM),
                HumanMessage(content=prompt),
            ]
        )
        critique = verdict.feedback
        if verdict.issues:
            critique += "\nIssues:\n" + "\n".join(f"- {i}" for i in verdict.issues)

        return {
            "approved": verdict.approved,
            "critique": critique,
            "iterations": state.get("iterations", 0) + 1,
        }

    return critic
