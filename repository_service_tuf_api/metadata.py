# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

import logging
from uuid import uuid4

from repository_service_tuf_api import celery, settings_repository, sync_redis


def is_bootstrap_done():
    """
    Check if the boot is done.
    """

    sync_redis()
    if settings_repository.get_fresh("BOOTSTRAP", False):
        return True
    else:
        return False


def get_task_id():
    return uuid4().hex


@celery.task(name="app.repository_service_tuf_worker")
def repository_metadata(action, payload):
    logging.debug(f"New tasks action submitted {action}")
    return True
