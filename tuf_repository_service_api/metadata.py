import logging
from uuid import uuid4

from tuf_repository_service_api import celery, settings_repository, sync_redis


def is_bootstrap_done():
    """
    Check if the boot is done.
    """

    sync_redis()
    if settings_repository.get_fresh("BOOTSTRAP"):
        return True
    else:
        return False


def get_task_id():
    return uuid4().hex


@celery.task(name="app.tuf_repository_service_worker")
def repository_metadata(action, payload):
    logging.debug(f"New tasks action submitted {action}")
    return True
