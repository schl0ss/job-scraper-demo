import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_raw_db_url = os.environ.get("DATABASE_URL", "")
if _raw_db_url.startswith("postgresql://"):
    os.environ["DATABASE_URL"] = _raw_db_url.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/resume_audit"
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8-hour shifts

    theirstack_api_key: str = ""
    resume_pdf_dir: str = "./resumes"

    ingestion_job_titles: list[str] = ["registered nurse", "RN", "nurse"]
    ingestion_location_pattern: str = (
        "Dallas|Fort Worth|Plano|Frisco|Arlington|McKinney|Irving"
    )
    ingestion_max_age_days: int = 7
    ingestion_limit: int = 100

    @model_validator(mode="after")
    def _fix_async_driver(self) -> "Settings":
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self


settings = Settings()
