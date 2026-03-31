from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from app.models.submission import SubmissionOutcome


class SubmissionCreate(BaseModel):
    outcome: SubmissionOutcome
    notes: str | None = None


class SubmissionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    job_id: int
    ra_user_id: int
    outcome: SubmissionOutcome
    submitted_at: datetime
    notes: str | None
