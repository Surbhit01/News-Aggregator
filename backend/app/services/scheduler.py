"""
Scheduler service: manages recurring tasks for digest generation.
Uses APScheduler for in-process scheduling (MVP).
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.services.digest_service import _generate_and_cache

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def morning_briefing_job():
    """Generate morning briefings for all active users."""
    logger.info("Scheduled: generating morning briefings")

    # In MVP, iterate over all users.
    # In production, query active users from DB.
    from app.db.session import SessionLocal
    from app.db.models import User

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        for user in users:
            try:
                logger.info(f"Generating briefing for user {user.id}")
                await _generate_and_cache(user.id, digest_type="morning_briefing")
            except Exception as e:
                logger.error(f"Failed to generate briefing for user {user.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    if scheduler.running:
        return

    # Parse morning briefing time
    try:
        hour, minute = settings.MORNING_BRIEFING_TIME.split(":")
        scheduler.add_job(
            morning_briefing_job,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id="morning_briefing",
            replace_existing=True,
        )
        logger.info(f"Scheduled morning briefing at {settings.MORNING_BRIEFING_TIME} daily")
    except Exception as e:
        logger.warning(f"Could not schedule morning briefing: {e}")

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")