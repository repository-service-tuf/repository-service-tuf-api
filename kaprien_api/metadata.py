import logging
from uuid import uuid4

from kaprien_api import celery


def get_task_id():
    return uuid4().hex


@celery.task(name="app.kaprien_repo_worker")
def repository_metadata(action, settings, payload):
    logging.debug(f"New tasks action submitted {action}")
    return True
