"""
Pydantic v2 schemas for the Kanban board.

Naming convention (kept distinct from `models.py` to avoid the most common
agent failure: importing SQLAlchemy models into the response layer and
leaking session state across processes):

  CardIn  -> request body to create a card
  CardOut -> response body for any card returned by the API
  CardMove -> request body for the "move to column" endpoint
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CardIn(BaseModel):
    """Request body for POST /api/cards."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    column: str = Field(default="backlog")


class CardMove(BaseModel):
    """Request body for PATCH /api/cards/{id}/move."""

    column: str = Field(pattern=r"^(backlog|in_progress|done)$")
    position: int = Field(ge=0)


class CardOut(BaseModel):
    """Response shape for any endpoint that returns a single card."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    column: str
    position: int
    created_at: datetime
    updated_at: datetime
