from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Instagram Automation API"
    DEBUG: bool = False
    SECRET_KEY: str
    API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"
    JOB_QUEUE_NAME: str = "instagram_jobs"
    SESSION_DIR: str = "/app/storage/sessions"
    DATA_DIR: str = "/app/storage/data"
    LOG_DIR: str = "/app/storage/logs"
    DEFAULT_REQUEST_DELAY: float = 3.0
    MAX_DAILY_ACTIONS: int = 150

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
