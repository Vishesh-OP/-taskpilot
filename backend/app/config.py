from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dev.db"  # local dev/tests only; use Postgres when deployed
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_hours: int = 12
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    frontend_origins: str = "http://localhost:5173"
    llm_timeout_seconds: float = 30.0
    max_agent_steps: int = 5
    timezone: str = "Asia/Kolkata"

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.frontend_origins.split(",") if o.strip()]


settings = Settings()
