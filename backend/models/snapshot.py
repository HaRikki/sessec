"""Stored API responses captured from the original site's public JSON endpoints."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ApiSnapshot(Base):
    __tablename__ = "api_snapshots"
    __table_args__ = (UniqueConstraint("path", "query", name="uq_api_snapshots_path_query"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False, default="application/json")
    body: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )
