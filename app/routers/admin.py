from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_lead_ra
from app.models.job_posting import JobPosting
from app.models.user import User
from app.schemas.admin import (
    DashboardStats, IngestionRequest, IngestionResult,
    StaleReassignRequest,
)
from app.services.admin_service import (
    export_submissions_csv, get_dashboard_stats,
    mark_stale_claims, reassign_claim,
)
from app.services.ingestion_service import get_pending_review, run_ingestion

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    return await get_dashboard_stats(db)


@router.post("/ingest", response_model=IngestionResult)
async def trigger_ingestion(
    body: IngestionRequest = IngestionRequest(),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    return await run_ingestion(db, body)


@router.post("/stale/mark", response_model=dict)
async def mark_stale(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    count = await mark_stale_claims(db)
    return {"marked_stale": count}


@router.post("/stale/reassign", response_model=dict)
async def reassign(
    body: StaleReassignRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    assignment = await reassign_claim(db, body.assignment_id, body.new_ra_user_id)
    return {"assignment_id": assignment.id, "new_ra_user_id": assignment.ra_user_id}


@router.get("/dedup/review", response_model=list[dict])
async def dedup_review_queue(
    _admin: User = Depends(require_lead_ra),
):
    return get_pending_review()


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status.value != "available":
        raise HTTPException(status_code=409, detail="Can only delete available jobs")
    await db.delete(job)
    await db.commit()
    return {"deleted": job_id}


@router.get("/export/csv")
async def export_csv(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    csv_data = await export_submissions_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=submissions.csv"},
    )
