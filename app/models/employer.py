from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Employer(Base):
    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    metro: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    aliases: Mapped[list[EmployerAlias]] = relationship(
        back_populates="employer", cascade="all, delete-orphan"
    )
    job_postings: Mapped[list[JobPosting]] = relationship(back_populates="employer")  # type: ignore[name-defined]


class EmployerAlias(Base):
    __tablename__ = "employer_aliases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_name: Mapped[str] = mapped_column(String(500), nullable=False)

    employer: Mapped[Employer] = relationship(back_populates="aliases")
