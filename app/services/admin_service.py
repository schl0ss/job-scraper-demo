from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.job_posting import JobPosting, JobStatus
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.admin import DashboardStats, RAStats, CSVExportRow
from app.schemas.auth import UserOut

STALE_THRESHOLD = timedelta(hours=24)


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    # Job counts by status
    counts = {}
    for status in JobStatus:
        result = await db.execute(
            select(func.count()).where(JobPosting.status == status)
        )
        counts[status] = result.scalar_one()

    total = sum(counts.values())

    # Stale claims
    cutoff = datetime.now(timezone.utc) - STALE_THRESHOLD
    stale_result = await db.execute(
        select(func.count()).where(
            and_(
                Assignment.released_at.is_(None),
                Assignment.claimed_at < cutoff,
                Assignment.is_stale.is_(False),
            )
        )
    )
    stale_count = stale_result.scalar_one()

    # Per-RA stats
    ra_result = await db.execute(
        select(User).where(User.role == UserRole.ra)
    )
    ras = ra_result.scalars().all()

    per_ra = []
    for ra in ras:
        claimed = await db.execute(
            select(func.count()).where(
                and_(Assignment.ra_user_id == ra.id, Assignment.released_at.is_(None))
            )
        )
        submitted = await db.execute(
            select(func.count()).where(Submission.ra_user_id == ra.id)
        )
        stale = await db.execute(
            select(func.count()).where(
                and_(
                    Assignment.ra_user_id == ra.id,
                    Assignment.released_at.is_(None),
                    Assignment.claimed_at < cutoff,
                )
            )
        )
        per_ra.append(RAStats(
            ra=UserOut.model_validate(ra),
            claimed=claimed.scalar_one(),
            submitted=submitted.scalar_one(),
            stale=stale.scalar_one(),
        ))

    return DashboardStats(
        total_jobs=total,
        available=counts.get(JobStatus.available, 0),
        claimed=counts.get(JobStatus.claimed, 0),
        submitted=counts.get(JobStatus.submitted, 0),
        excluded=counts.get(JobStatus.excluded, 0),
        stale_claims=stale_count,
        per_ra=per_ra,
    )


async def mark_stale_claims(db: AsyncSession) -> int:
    """Mark claims older than 24h as stale. Returns count marked."""
    cutoff = datetime.now(timezone.utc) - STALE_THRESHOLD
    result = await db.execute(
        select(Assignment).where(
            and_(
                Assignment.released_at.is_(None),
                Assignment.claimed_at < cutoff,
                Assignment.is_stale.is_(False),
            )
        )
    )
    stale = result.scalars().all()
    for a in stale:
        a.is_stale = True
    await db.commit()
    return len(stale)


async def reassign_claim(
    db: AsyncSession, assignment_id: int, new_ra_user_id: int
) -> Assignment:
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.ra_user_id = new_ra_user_id
    assignment.is_stale = False
    assignment.claimed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_submissions(db: AsyncSession) -> list[dict]:
    """Return submission records with joined job + RA data."""
    result = await db.execute(
        select(Submission)
        .options(
            selectinload(Submission.job).selectinload(JobPosting.employer),
            selectinload(Submission.ra),
        )
        .order_by(Submission.submitted_at.desc())
    )
    submissions = result.scalars().all()
    return [
        {
            "job_code": s.job.job_code,
            "job_title": s.job.title,
            "employer": s.job.employer.canonical_name,
            "location": s.job.location,
            "ra_email": s.ra.email,
            "outcome": s.outcome.value,
            "notes": s.notes or "",
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in submissions
    ]


async def export_submissions_csv(db: AsyncSession) -> str:
    result = await db.execute(
        select(Submission)
        .options(
            selectinload(Submission.job).selectinload(JobPosting.employer),
            selectinload(Submission.ra),
        )
        .order_by(Submission.submitted_at.desc())
    )
    submissions = result.scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "submission_id", "job_id", "theirstack_id", "job_title",
        "employer_canonical", "metro", "location", "education_level",
        "salary", "source_url", "ra_email", "outcome", "submitted_at", "notes",
    ])

    for s in submissions:
        writer.writerow([
            s.id, s.job_id, s.job.theirstack_id, s.job.title,
            s.job.employer.canonical_name, s.job.employer.metro, s.job.location,
            s.job.education_level, s.job.salary, s.job.source_url,
            s.ra.email, s.outcome, s.submitted_at.isoformat(), s.notes or "",
        ])

    return buf.getvalue()
