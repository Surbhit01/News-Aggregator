from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.crud import create_feedback
from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit user feedback on an article (show_more, show_less, irrelevant)."""
    fb = create_feedback(db, user.id, feedback.article_id, feedback.feedback_type)
    return FeedbackResponse(
        id=fb.id,
        article_id=fb.article_id,
        feedback_type=fb.feedback_type,
    )