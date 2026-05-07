from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: str

    # generic LLM config – adapt to your stack
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    llm_base_url: str | None = None  # for self-hosted

    class Config:
        env_prefix = ""  # GITLAB_URL, GITLAB_TOKEN, LLM_API_KEY, etc.
        env_file = ".env"
        env_file_encoding = "utf-8"


class GitLabConfig(BaseModel):
    base_url: str
    token: str


def get_settings() -> Settings:
    return Settings()
