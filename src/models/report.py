from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

import sqlalchemy as sa
from sqlmodel import Column, Field, Relationship, SQLModel

from src.models.enums import TriageCategory, pg_enum

if TYPE_CHECKING:
    from src.models.confession import Confession
    from src.models.user import User


class Report(SQLModel, table=True):
    __tablename__ = "reports"
    __table_args__ = (
        sa.Index(
            "idx_reports_unresolved",
            "confession_id",
            postgresql_where=sa.text("resolved = false"),
        ),
    )

    confession_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            sa.ForeignKey("confessions.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    reporter_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    reason: TriageCategory = Field(
        sa_column=Column(
            pg_enum(TriageCategory, "triage_category"),
            nullable=False,
        ),
    )
    resolved: bool = Field(
        default=False,
        sa_column=Column(
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Relationships
    confession: Optional["Confession"] = Relationship(
        back_populates="reports",
    )
    reporter: Optional["User"] = Relationship(
        back_populates="reports",
    )
