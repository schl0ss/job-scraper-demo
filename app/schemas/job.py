from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel
from app.models.job_posting import JobStatus, EducationLevelDB


class JobFilter(BaseModel):
    status: JobStatus | None = None
    education_level: EducationLevelDB | None = None
    job_code: str | None = None
    metro: str | None = None
    limit: int = 50
    offset: int = 0


class EmployerOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    canonical_name: str
    metro: str


class JobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    job_code: str | None
    title: str
    employer: EmployerOut
    location: str
    education_level: EducationLevelDB
    salary: str | None
    source_url: str | None
    date_posted: date | None
    status: JobStatus
    created_at: datetime


class JobDetailOut(JobOut):
    description: str
