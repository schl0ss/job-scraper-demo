from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.assignment import Assignment
from app.models.job_posting import JobPosting, JobStatus
from app.models.submission import Submission
from app.schemas.job import JobFilter
from app.schemas.submission import SubmissionCreate

CLAIM_DURATION = timedelta(hours=24)


async def list_jobs(db: AsyncSession, filters: JobFilter) -> list[JobPosting]:
    stmt = (
        select(JobPosting)
        .options(selectinload(JobPosting.employer))
        .offset(filters.offset)
        .limit(filters.limit)
        .order_by(JobPosting.date_posted.desc().nullslast(), JobPosting.id.desc())
    )
    if filters.status:
        stmt = stmt.where(JobPosting.status == filters.status)
    if filters.education_level:
        stmt = stmt.where(JobPosting.education_level == filters.education_level)
    if filters.job_code:
        try:
            full_code = f"JOB-{int(filters.job_code):06d}"
        except ValueError:
            full_code = filters.job_code
        stmt = stmt.where(JobPosting.job_code == full_code)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: int) -> JobPosting:
    result = await db.execute(
        select(JobPosting)
        .options(selectinload(JobPosting.employer))
        .where(JobPosting.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


async def claim_job(db: AsyncSession, job_id: int, ra_user_id: int) -> Assignment:
    job = await get_job(db, job_id)

    if job.status != JobStatus.available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is not available (status: {job.status})",
        )

    assignment = Assignment(job_id=job_id, ra_user_id=ra_user_id)
    job.status = JobStatus.claimed
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def release_claim(db: AsyncSession, job_id: int, ra_user_id: int) -> JobPosting:
    job = await get_job(db, job_id)

    result = await db.execute(
        select(Assignment).where(
            and_(
                Assignment.job_id == job_id,
                Assignment.ra_user_id == ra_user_id,
                Assignment.released_at.is_(None),
            )
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active claim not found")

    assignment.released_at = datetime.now(timezone.utc)
    job.status = JobStatus.available
    await db.commit()
    return job


async def log_submission(
    db: AsyncSession, job_id: int, ra_user_id: int, data: SubmissionCreate
) -> Submission:
    job = await get_job(db, job_id)

    if job.status != JobStatus.claimed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job must be claimed before logging a submission",
        )

    # Close out the active assignment
    result = await db.execute(
        select(Assignment).where(
            and_(
                Assignment.job_id == job_id,
                Assignment.ra_user_id == ra_user_id,
                Assignment.released_at.is_(None),
            )
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment:
        assignment.released_at = datetime.now(timezone.utc)

    submission = Submission(
        job_id=job_id,
        ra_user_id=ra_user_id,
        outcome=data.outcome,
        notes=data.notes,
    )
    job.status = JobStatus.submitted
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_resume_path(job_id: int) -> Path:
    """Return path to the generated resume PDF for this job."""
    pdf_dir = Path(settings.resume_pdf_dir)
    path = pdf_dir / f"job_{job_id}.pdf"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume PDF not yet generated for this job",
        )
    return path
