from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "sqlite:///./sales_agent.db"
    model_name: str = "llama-3.3-70b-versatile"
    openai_base_url: str = "https://api.groq.com/openai/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"
        protected_namespaces = ("settings_",)


def get_settings() -> Settings:
    return Settings()
