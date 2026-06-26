"""
Source bias routes: manage configurable bias ratings for news sources.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel

from app.db.session import get_db
from app.db.crud import get_all_source_biases, upsert_source_bias, delete_source_bias
from app.api.deps import get_current_user
from app.db.models import User


class SourceBiasCreate(BaseModel):
    domain: str
    bias_rating: str  # "liberal", "conservative", "neutral", "unknown"
    confidence: float = 0.7
    notes: str | None = None


class SourceBiasResponse(BaseModel):
    domain: str
    bias_rating: str
    confidence: float
    notes: str | None = None

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/biases", tags=["biases"])


@router.get("", response_model=Dict[str, str])
async def list_biases(db: Session = Depends(get_db)):
    """List all configured source biases (domain → bias_rating)."""
    return get_all_source_biases(db)


@router.post("", response_model=SourceBiasResponse, status_code=201)
async def create_bias(
    data: SourceBiasCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add or update a source bias rating."""
    valid_ratings = {"liberal", "conservative", "neutral", "unknown"}
    if data.bias_rating not in valid_ratings:
        raise HTTPException(
            status_code=422,
            detail=f"bias_rating must be one of: {', '.join(sorted(valid_ratings))}",
        )
    bias = upsert_source_bias(db, data.domain, data.bias_rating, data.confidence, data.notes)
    return bias


@router.delete("/{domain}")
async def remove_bias(
    domain: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a source bias rating."""
    deleted = delete_source_bias(db, domain)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source bias not found")
    return {"status": "deleted", "domain": domain}