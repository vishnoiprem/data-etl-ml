"""
SQLAlchemy 2.x models for the Kanban board.

One class per table. Use the 2.x `DeclarativeBase` style — NOT the legacy
`declarative_base()` factory. The legacy form still works in 2.x but emits
warnings in newer versions, and every tutorial old enough to use it is also
old enough to have outdated patterns elsewhere.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base. New models inherit from this."""


class Card(Base):
    """A single Kanban card.

    Columns intentionally use snake_case; FastAPI's Pydantic layer does the
    camelCase conversion at the response boundary.
    """

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    column: Mapped[str] = mapped_column(
        String(32), nullable=False, default="backlog"
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
