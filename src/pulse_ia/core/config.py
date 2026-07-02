import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Pulse IA"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "pulse_ia")
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}")

    ANONYMITY_THRESHOLD_DEFAULT: int = 5
    ARTIFACTS_DIR: str = os.getenv("ARTIFACTS_DIR", "./artifacts")

    @property
    def get_secret_key(self) -> str:
        if not self.SECRET_KEY:
            if os.getenv("ENV") == "production":
                raise ValueError("SECRET_KEY must be set in production")
            return "local_dev_secret_key_fixed_v1"
        return self.SECRET_KEY

settings = Settings()
