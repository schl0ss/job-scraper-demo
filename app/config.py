from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
