# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import logging
import os

from celery import Celery
from dynaconf import Dynaconf
from dynaconf.loaders import redis_loader

from repository_service_tuf_api.rstuf_auth.enums import ScopeName
from repository_service_tuf_api.rstuf_auth.services.auth import (
    CustomSQLAuthenticationService,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.yaml")
REPOSITORY_SETTINGS_FILE = os.path.join(DATA_DIR, "repository_settings.yaml")

settings = Dynaconf(
    envvar_prefix="RSTUF",
    settings_files=[SETTINGS_FILE],
)

settings_repository = Dynaconf(
    settings_files=[REPOSITORY_SETTINGS_FILE],
    redis_enabled=True,
    redis={
        "host": settings.REDIS_SERVER.split("redis://")[1],
        "port": settings.get("REDIS_SERVER_PORT", 6379),
        "db": settings.get("REDIS_SERVER_DB_REPO_SETTINGS", 1),
        "decode_responses": True,
    },
)
secrets_settings = Dynaconf(
    envvar_prefix="SECRETS_RSTUF",
    environments=True,
)


def sync_redis():
    """
    If there is a local configuration with bootstrap in the local file settings
    and it is not available in the Redis Server, restore it.

    Note: The Redis Server should have its persistent data setup and recovery
    mechanism. It is not a requirement from Rest API.
    """
    bootstrap_id = settings_repository.get("BOOTSTRAP")
    redis_dynaconf = redis_loader.StrictRedis(
        **settings_repository.get("REDIS_FOR_DYNACONF")
    )

    redis_dynaconf_data = redis_dynaconf.hgetall("DYNACONF_MAIN")
    if redis_dynaconf_data == {} and bootstrap_id:
        logging.warning("No data found in redis, synchronizing")
        redis_loader.write(settings_repository, settings_repository.to_dict())


# Initiate authentication service
# TODO: change the service based on a configuration (e.g., environment)
if settings.get("BUILT_IN_AUTH", False) is False:
    auth_service = None

else:
    auth_service = CustomSQLAuthenticationService(
        settings=settings, secrets_settings=secrets_settings, base_dir=DATA_DIR
    )

# TODO: remove this later. We didn't want to touch all the files that import it
#   at the moment of the rstuf_auth change
SCOPES_NAMES = ScopeName


# Celery setup
celery = Celery(__name__)
celery.conf.broker_url = settings.BROKER_SERVER
celery.conf.result_backend = (
    f"{settings.REDIS_SERVER}"
    f":{settings.get('REDIS_SERVER_PORT', 6379)}"
    f"/{settings.get('REDIS_SERVER_DB_REPO_SETTINGS', 0)}"
)
celery.conf.accept_content = ["json", "application/json"]
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.task_track_started = True
celery.conf.broker_heartbeat = 0
celery.conf.result_persistent = True
celery.conf.task_acks_late = True
celery.conf.broker_pool_limit = None
# celery.conf.broker_use_ssl
# https://github.com/vmware/repository-service-tuf-api/issues/91
