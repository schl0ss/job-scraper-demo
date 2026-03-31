from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.job_posting import JobStatus, EducationLevelDB
from app.models.user import User
from app.schemas.job import JobOut, JobDetailOut, JobFilter
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.services.job_service import (
    claim_job, get_job, get_resume_path, list_jobs, log_submission, release_claim
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
async def list_job_queue(
    status: JobStatus | None = Query(None),
    education_level: EducationLevelDB | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = JobFilter(
        status=status,
        education_level=education_level,
        limit=limit,
        offset=offset,
    )
    jobs = await list_jobs(db, filters)
    return [JobOut.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobDetailOut)
async def get_job_detail(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await get_job(db, job_id)
    return JobDetailOut.model_validate(job)


@router.post("/{job_id}/claim", response_model=dict, status_code=201)
async def claim(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = await claim_job(db, job_id, current_user.id)
    return {"assignment_id": assignment.id, "claimed_at": assignment.claimed_at}


@router.delete("/{job_id}/claim", response_model=dict)
async def release(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await release_claim(db, job_id, current_user.id)
    return {"status": "released"}


@router.post("/{job_id}/submission", response_model=SubmissionOut, status_code=201)
async def submit(
    job_id: int,
    body: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = await log_submission(db, job_id, current_user.id, body)
    return SubmissionOut.model_validate(submission)


@router.get("/{job_id}/resume")
async def download_resume(
    job_id: int,
    current_user: User = Depends(get_current_user),
):
    path = await get_resume_path(job_id)
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"resume_job_{job_id}.pdf",
    )
