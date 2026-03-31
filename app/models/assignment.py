from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ra_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    job: Mapped[JobPosting] = relationship(back_populates="assignments")  # type: ignore[name-defined]
    ra: Mapped[User] = relationship()  # type: ignore[name-defined]
