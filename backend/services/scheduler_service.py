import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.memory_service import memory_service
from backend.services.model.spontaneous_service import generate_spontaneous_message
from backend.types import Role, User
from backend.utils.logger_utils import logger
from backend.utils.time_utils import to_iso_utc

CLEANUP_HOUR = 3
CLEANUP_MINUTE = 0


def cleanup_all_chats_job():
    logger.info("Cleanup job: starting full cleanup cycle")

    try:
        chat_ids = memory_service.get_all_chat_ids()
        logger.info("Cleanup job: found %s chats to process", len(chat_ids))

        for chat_id in chat_ids:
            memory_service.enforce_limits(chat_id)

        logger.info("Cleanup job: completed successfully")

    except Exception as e:
        logger.error("Cleanup job: failed during execution: %s", e)


def spontaneous_post_job():
    if not settings.spontaneous_enabled:
        logger.info("Spontaneous post: disabled")
        return

    logger.info("Spontaneous post: getting active chats")
    chat_ids = memory_service.get_active_chat_ids(settings.active_chat_days)
    if not chat_ids:
        logger.info("Spontaneous post: no active chats found")
        return

    logger.info("Spontaneous post: selecting chats")
    selected = random.sample(chat_ids, k=min(settings.spontaneous_max_chats, len(chat_ids)))

    logger.info("Spontaneous post: selected %s chats", len(selected))
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=settings.no_posts_days)
    cutoff_iso = to_iso_utc(cutoff_dt)

    for chat_id in selected:
        logger.info("Spontaneous post: checking recent messages for %s", chat_id)
        recent = memory_service.get_messages_since(chat_id, cutoff_iso)

        if recent:
            logger.info("Spontaneous post: skipping %s, %s messages in last %s days", chat_id, len(recent), settings.no_posts_days)
            continue

        logger.info("Spontaneous post: generating a post for %s", chat_id)
        post = generate_spontaneous_message(chat_id)

        logger.info("Spontaneous post: storing a post for %s", chat_id)
        memory_service.add_message(chat_id, User.RICK.value, Role.RICK, post)


def setup_jobs():
    interval_hours = random.randint(
        settings.spontaneous_min_interval_hours,
        settings.spontaneous_max_interval_hours,
    )

    if settings.is_dev:
        scheduler.add_job(spontaneous_post_job, "interval", minutes=5)
    else:
        scheduler.add_job(spontaneous_post_job, "interval", hours=interval_hours)

    scheduler.add_job(cleanup_all_chats_job, "cron", hour=CLEANUP_HOUR, minute=CLEANUP_MINUTE)
    logger.info("Scheduler is set up with jobs: %s", [job.name for job in scheduler.get_jobs()])


scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.timezone))
