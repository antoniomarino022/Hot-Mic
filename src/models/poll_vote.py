from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

import sqlalchemy as sa
from sqlmodel import Column, Field, Relationship, SQLModel

from src.models.enums import PollChoice, pg_enum

if TYPE_CHECKING:
    from src.models.confession import Confession
    from src.models.user import User


class PollVote(SQLModel, table=True):
    __tablename__ = "poll_votes"
    __table_args__ = (
        sa.UniqueConstraint("confession_id", "user_id", name="uq_poll_votes_confession_user"),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
    confession_id: int = Field(
        sa_column=Column(
            sa.Integer,
            sa.ForeignKey("confessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    user_id: int = Field(
        sa_column=Column(
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    choice: PollChoice = Field(
        sa_column=Column(
            pg_enum(PollChoice, "poll_choice"),
            nullable=False,
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
        back_populates="poll_votes",
    )
    user: Optional["User"] = Relationship(
        back_populates="poll_votes",
    )
