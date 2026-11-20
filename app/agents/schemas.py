from pydantic import BaseModel, Field


class CriticVerdict(BaseModel):
    """Structured verdict returned by the Critic agent."""

    approved: bool = Field(
        description="True only if the code fully solves the task correctly."
    )
    feedback: str = Field(
        description="Concise, actionable feedback for the coder."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific problems found. Empty list if approved.",
    )
