from __future__ import annotations

import enum
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Enum as SAEnum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class JobStatus(str, enum.Enum):
    available = "available"
    claimed = "claimed"
    submitted = "submitted"
    excluded = "excluded"
    expired = "expired"


class EducationLevelDB(str, enum.Enum):
    AA = "AA"
    BA = "BA"
    unspecified = "unspecified"


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    theirstack_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    employer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    education_level: Mapped[EducationLevelDB] = mapped_column(
        SAEnum(EducationLevelDB), nullable=False, default=EducationLevelDB.unspecified
    )
    salary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    date_posted: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), nullable=False, default=JobStatus.available, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    employer: Mapped[Employer] = relationship(back_populates="job_postings")  # type: ignore[name-defined]
    assignments: Mapped[list[Assignment]] = relationship(back_populates="job")  # type: ignore[name-defined]
    submission: Mapped[Submission | None] = relationship(back_populates="job", uselist=False)  # type: ignore[name-defined]
