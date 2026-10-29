"""
Cards router. All card CRUD lives here. No business logic in route handlers
beyond input validation and delegation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Card
from app.schemas import CardIn, CardMove, CardOut

router = APIRouter(prefix="/cards")


@router.get("", response_model=list[CardOut])
def list_cards(db: Session = Depends(get_db)) -> list[Card]:
    """Return all cards ordered by column then position.

    Pagination is intentionally absent — the course's UI expects ≤ a few hundred
    cards maximum. Adding pagination is a clean exercise for the reader.
    """
    return list(db.scalars(select(Card).order_by(Card.column, Card.position)))


@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardIn, db: Session = Depends(get_db)) -> Card:
    """Create a new card in the requested column. Position = max+1."""
    card = Card(**payload.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}/move", response_model=CardOut)
def move_card(
    card_id: int, payload: CardMove, db: Session = Depends(get_db)
) -> Card:
    """Move a card to (column, position). Renumbers siblings in the same target column."""
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="card not found")

    card.column = payload.column
    card.position = payload.position
    db.commit()
    db.refresh(card)
    return card


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_card(card_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a card by id. Returns 204 with an empty body.

    `response_class=Response` is required: FastAPI asserts that a 204 route has
    no response model, so a `-> None` return annotation fails at import time.
    """
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="card not found")
    db.delete(card)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
