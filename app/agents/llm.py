from langchain_openai import ChatOpenAI
from app.config import settings


def get_llm(model: str | None = None, temperature: float = 0):
    """Factory to create an LLM client using configured credentials and settings."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    kwargs = {
        "model": model or settings.model_name,
        "api_key": settings.openai_api_key,
        "temperature": temperature,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    return ChatOpenAI(**kwargs)
