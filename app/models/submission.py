from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, ForeignKey, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SubmissionOutcome(str, enum.Enum):
    applied = "applied"
    no_response = "no_response"
    rejected = "rejected"
    not_qualified = "not_qualified"
    duplicate = "duplicate"
    no_longer_accepting = "no_longer_accepting"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    ra_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outcome: Mapped[SubmissionOutcome] = mapped_column(SAEnum(SubmissionOutcome), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job: Mapped[JobPosting] = relationship(back_populates="submission")  # type: ignore[name-defined]
    ra: Mapped[User] = relationship()  # type: ignore[name-defined]
