from __future__ import annotations

import asyncio
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.employer import Employer, EmployerAlias
from app.models.job_posting import JobPosting, EducationLevelDB
from app.schemas.admin import IngestionRequest, IngestionResult

# Import the existing pipeline modules
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from employer_dedup import EmployerRegistry, normalize
from education_extractor import extract_education, EducationLevel
from theirstack_client import fetch_jobs as ts_fetch_jobs

# In-memory review queue for dedup ambiguous cases (flushed to DB on ingestion)
_pending_review: list[dict] = []


async def run_ingestion(db: AsyncSession, req: IngestionRequest) -> IngestionResult:
    """
    Fetch jobs from TheirStack, resolve employers, extract education levels,
    and insert new postings into the database.
    """
    global _pending_review
    _pending_review = []

    job_titles = req.job_titles or settings.ingestion_job_titles
    location_pattern = req.location_pattern or settings.ingestion_location_pattern

    # TheirStack client is sync — run in thread pool
    raw_jobs = await asyncio.to_thread(
        ts_fetch_jobs,
        job_titles=job_titles,
        location_pattern=location_pattern,
        max_age_days=req.max_age_days,
        limit=req.limit,
        api_key=settings.theirstack_api_key,
    )

    # Post-fetch filter: drop jobs outside the target state.
    # TheirStack's location_pattern is a regex on city names, which can match
    # cities in other states (e.g., "Arlington" matches VA and TX).
    _TX = re.compile(r"\bTX\b|Texas", re.IGNORECASE)
    raw_jobs = [j for j in raw_jobs if _TX.search(j.location)]

    inserted = 0
    skipped = 0
    review_additions = 0

    # Build an in-memory registry seeded from the DB for this run
    registry = await _load_registry(db)

    for raw in raw_jobs:
        # Skip if already ingested
        if raw.theirstack_id:
            existing = await db.execute(
                select(JobPosting).where(JobPosting.theirstack_id == raw.theirstack_id)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

        # Resolve employer (dedup)
        match = registry.resolve(raw.company, "Dallas-Fort Worth")
        emp_id = await _sync_employer(db, match, raw.company)

        if match.tier == "review":
            review_additions += 1
            _pending_review.append({
                "raw_name": raw.company,
                "raw_metro": "Dallas-Fort Worth",
                "suggested_canonical_id": match.matched_employer.canonical_id,
                "suggested_canonical_name": match.matched_employer.canonical_name,
                "match_score": match.score or 0.0,
            })

        # Extract education requirement
        edu_result = extract_education(raw.description)
        edu_level = _map_education(edu_result.level)

        # Parse date
        posted_date = None
        if raw.date_posted:
            try:
                posted_date = date.fromisoformat(raw.date_posted)
            except ValueError:
                pass

        job = JobPosting(
            theirstack_id=raw.theirstack_id,
            title=raw.title,
            employer_id=emp_id,
            location=raw.location,
            description=raw.description,
            education_level=edu_level,
            salary=raw.salary,
            source_url=raw.source_url,
            date_posted=posted_date,
        )
        db.add(job)
        inserted += 1

    await db.commit()

    return IngestionResult(
        fetched=len(raw_jobs),
        inserted=inserted,
        skipped_duplicates=skipped,
        review_queue_additions=review_additions,
    )


async def _load_registry(db: AsyncSession) -> EmployerRegistry:
    """Seed the in-memory EmployerRegistry from existing DB employers."""
    from employer_dedup import Employer as MemEmployer

    registry = EmployerRegistry()
    from sqlalchemy.orm import selectinload as sil
    result = await db.execute(
        select(Employer).options(sil(Employer.aliases))
    )
    employers = result.scalars().all()

    for emp in employers:
        # Rebuild canonical employers in memory
        mem_emp = MemEmployer(
            canonical_id=emp.id,
            canonical_name=emp.canonical_name,
            metro=emp.metro,
            aliases=[a.raw_name for a in emp.aliases],
        )
        registry._employers[emp.id] = mem_emp
        registry._norm_index[normalize(emp.canonical_name)] = emp.id
        for alias in emp.aliases:
            norm = normalize(alias.raw_name)
            if norm not in registry._norm_index:
                registry._norm_index[norm] = emp.id
        if emp.id >= registry._next_id:
            registry._next_id = emp.id + 1

    return registry


async def _sync_employer(db: AsyncSession, match, raw_name: str) -> int:
    """Persist a new employer or alias to the database, return employer DB id."""
    if match.tier == "new":
        emp = Employer(
            canonical_name=match.matched_employer.canonical_name,
            metro=match.matched_employer.metro,
        )
        db.add(emp)
        await db.flush()  # Get the ID
        alias = EmployerAlias(employer_id=emp.id, raw_name=raw_name)
        db.add(alias)
        return emp.id
    else:
        # Existing employer — just ensure alias is recorded
        existing = await db.execute(
            select(Employer).where(Employer.id == match.matched_employer.canonical_id)
        )
        emp = existing.scalar_one_or_none()
        if emp:
            # Add alias if not already there
            alias_check = await db.execute(
                select(EmployerAlias).where(
                    EmployerAlias.employer_id == emp.id,
                    EmployerAlias.raw_name == raw_name,
                )
            )
            if not alias_check.scalar_one_or_none():
                db.add(EmployerAlias(employer_id=emp.id, raw_name=raw_name))
            return emp.id
        # Fallback: create new
        new_emp = Employer(canonical_name=raw_name, metro="Dallas-Fort Worth")
        db.add(new_emp)
        await db.flush()
        return new_emp.id


def _map_education(level: EducationLevel) -> EducationLevelDB:
    if level == EducationLevel.ASSOCIATES:
        return EducationLevelDB.AA
    if level == EducationLevel.BACHELORS:
        return EducationLevelDB.BA
    return EducationLevelDB.unspecified


def get_pending_review() -> list[dict]:
    return list(_pending_review)
