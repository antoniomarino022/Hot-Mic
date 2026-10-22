from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

import sqlalchemy as sa
from sqlmodel import Column, Field, Relationship, SQLModel

from src.models.enums import ReactionType, pg_enum

if TYPE_CHECKING:
    from src.models.confession import Confession
    from src.models.user import User


class Reaction(SQLModel, table=True):
    __tablename__ = "reactions"

    confession_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            sa.ForeignKey("confessions.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    type: ReactionType = Field(
        sa_column=Column(
            pg_enum(ReactionType, "reaction_type"),
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
        back_populates="reactions",
    )
    user: Optional["User"] = Relationship(
        back_populates="reactions",
    )
