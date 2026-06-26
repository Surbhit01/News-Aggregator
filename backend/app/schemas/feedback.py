from pydantic import BaseModel
from typing import Literal


class FeedbackCreate(BaseModel):
    article_id: str
    feedback_type: Literal["show_more", "show_less", "irrelevant"]


class FeedbackResponse(BaseModel):
    id: str
    article_id: str
    feedback_type: str
    message: str = "Feedback recorded"