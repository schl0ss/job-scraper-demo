from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.dependencies import get_db, require_lead_ra
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
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


@router.post("/bootstrap")
async def bootstrap_lead_ra(db: AsyncSession = Depends(get_db)):
    """One-time endpoint to create the initial Lead RA account.
    Returns 409 if a lead_ra user already exists."""
    result = await db.execute(select(User).where(User.role == UserRole.lead_ra))
    if result.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Lead RA already exists")
    user = User(
        email="lead@resumeaudit.study",
        hashed_password=hash_password("ChangeMe123!"),
        role=UserRole.lead_ra,
    )
    db.add(user)
    await db.commit()
    return {"message": "Lead RA created", "email": user.email}


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
