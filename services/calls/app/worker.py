import asyncio

from celery import Celery

from salesvoice_common.logging import setup_logging

from app.config import settings
from app.errors import TransientError

setup_logging("calls-worker", settings.log_level)

celery_app = Celery("calls", broker=settings.redis_url)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
)

MAX_RETRIES = 4


@celery_app.task(bind=True, name="calls.analyze", max_retries=MAX_RETRIES)
def analyze_call(self, call_id: str) -> None:
    from app.pipeline import mark_failed, process_call

    try:
        asyncio.run(process_call(call_id))
    except TransientError as e:
        if self.request.retries >= MAX_RETRIES:
            asyncio.run(mark_failed(call_id, f"Gave up after {MAX_RETRIES} retries: {e}"))
            return
        wait = 10 * 2 ** self.request.retries
        raise self.retry(exc=e, countdown=wait)
    except Exception as e:
        asyncio.run(mark_failed(call_id, f"{type(e).__name__}: {e}"))
