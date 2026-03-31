from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/resume_audit"

    @property
    def async_database_url(self) -> str:
        """Ensure the URL uses the asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8-hour shifts

    theirstack_api_key: str = ""
    resume_pdf_dir: str = "./resumes"

    ingestion_job_titles: list[str] = ["registered nurse", "RN", "nurse"]
    ingestion_location_pattern: str = (
        "Dallas.*TX|Fort Worth.*TX|Plano.*TX|Frisco.*TX|Arlington.*TX"
        "|McKinney.*TX|Irving.*TX|Denton.*TX|Garland.*TX|Richardson.*TX"
    )
    ingestion_max_age_days: int = 7
    ingestion_limit: int = 100


settings = Settings()
