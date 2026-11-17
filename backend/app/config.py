from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./taskpilot.db"
    jwt_secret: str = "supersecretjwtkey"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    frontend_url: str = "https://taskpilot-taskpilot2.vercel.app"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
