from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CategorySelection(BaseModel):
    categories: List[str]


class KeywordTopic(BaseModel):
    keywords: List[str]


class SourceSelection(BaseModel):
    preferred_sources: List[str]
    blocked_sources: List[str]


class TrackedEntity(BaseModel):
    type: str  # "stock", "industry", "city", etc.
    name: str


class UserPreferenceUpdate(BaseModel):
    categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    preferred_sources: Optional[List[str]] = None
    blocked_sources: Optional[List[str]] = None
    tracked_entities: Optional[List[TrackedEntity]] = None


class UserPreferenceResponse(BaseModel):
    id: str
    user_id: str
    categories: List[str]
    keywords: List[str]
    preferred_sources: List[str]
    blocked_sources: List[str]
    tracked_entities: List[Dict[str, Any]]
    implicit_preferences: Dict[str, float]

    model_config = {"from_attributes": True}


class PreferenceStats(BaseModel):
    total_categories: int
    total_keywords: int
    total_preferred_sources: int
    total_blocked_sources: int
    total_tracked_entities: int