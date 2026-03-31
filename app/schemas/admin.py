from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import UserOut
from app.models.job_posting import EducationLevelDB
from app.models.submission import SubmissionOutcome


class RAStats(BaseModel):
    ra: UserOut
    claimed: int
    submitted: int
    stale: int


class DashboardStats(BaseModel):
    total_jobs: int
    available: int
    claimed: int
    submitted: int
    excluded: int
    stale_claims: int
    per_ra: list[RAStats]


class StaleReassignRequest(BaseModel):
    assignment_id: int
    new_ra_user_id: int


class DedupReviewItem(BaseModel):
    raw_name: str
    raw_metro: str
    suggested_canonical_id: int
    suggested_canonical_name: str
    match_score: float
    job_posting_id: int


class DedupDecision(BaseModel):
    job_posting_id: int
    accept_merge: bool
    target_employer_id: int


class IngestionRequest(BaseModel):
    job_titles: list[str] | None = None
    location_pattern: str | None = None
    max_age_days: int = 7
    limit: int = 100


class IngestionResult(BaseModel):
    fetched: int
    inserted: int
    skipped_duplicates: int
    review_queue_additions: int


class CSVExportRow(BaseModel):
    submission_id: int
    job_id: int
    theirstack_id: int | None
    job_title: str
    employer_canonical: str
    metro: str
    location: str
    education_level: str
    salary: str | None
    source_url: str | None
    ra_email: str
    outcome: str
    submitted_at: datetime
    notes: str | None
