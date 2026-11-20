import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Multi-Agent Workflow Orchestrator"
    environment: str = "dev"
    openai_api_key: str = ""
    openai_base_url: str | None = None
    model_name: str = "gpt-4o-mini"
    chroma_path: str = "./data/chroma"
    checkpoint_db: str = "./data/checkpoints.sqlite"
    max_critic_iterations: int = 3

    def model_post_init(self, __context) -> None:
        # Check fallback environment variables if openai_api_key was not set in .env
        if not self.openai_api_key:
            fallback_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY") or ""
            if fallback_key:
                self.openai_api_key = fallback_key

        # Detect Groq keys (start with gsk_) and set base_url & model if not explicitly configured
        if self.openai_api_key.startswith("gsk_"):
            if not self.openai_base_url:
                self.openai_base_url = "https://api.groq.com/openai/v1"
            if self.model_name == "gpt-4o-mini":
                self.model_name = os.getenv("XAI_MODEL", "llama-3.1-8b-instant")


settings = Settings()
