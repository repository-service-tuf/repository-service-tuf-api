import logging
import os
from enum import Enum

from celery import Celery
from dynaconf import Dynaconf
from dynaconf.loaders import redis_loader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repository_service_tuf_api.users import crud, schemas
from repository_service_tuf_api.users.models import Base

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


class SCOPES_NAMES(Enum):
    read_bootstrap = "read:bootstrap"
    read_settings = "read:settings"
    read_targets = "read:targets"
    read_tasks = "read:tasks"
    read_token = "read:token"
    write_bootstrap = "write:bootstrap"
    write_targets = "write:targets"
    write_token = "write:token"
    delete_targets = "delete:targets"


SCOPES = {
    SCOPES_NAMES.read_targets.value: "Read (GET) targets",
    SCOPES_NAMES.read_bootstrap.value: "Read (GET) bootstrap",
    SCOPES_NAMES.read_settings.value: "Read (GET) settings",
    SCOPES_NAMES.read_tasks.value: "Read (GET) tasks",
    SCOPES_NAMES.read_token.value: "Read (GET) tokens",
    SCOPES_NAMES.write_targets.value: "Write (POST) targets",
    SCOPES_NAMES.write_token.value: "Write (POST) token",
    SCOPES_NAMES.write_bootstrap.value: "Write (POST) bootstrap",
    SCOPES_NAMES.delete_targets.value: "Delete (DELETE) targets",
}

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
        "port": settings.get("RSTUF_REDIS_SERVER_PORT", 6379),
        "db": settings.get("RSTUF_REDIS_SERVER_DB_REPO_SETTINGS", 1),
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
        logging.warn("No data found in redis, synchronizing")
        redis_loader.write(settings_repository, settings_repository.to_dict())


# Tokens
if secrets_settings.TOKEN_KEY.startswith("/run/secrets/"):
    try:
        with open(secrets_settings.TOKEN_KEY) as f:
            SECRET_KEY = f.read().rstrip("\n")
    except OSError as err:
        logging.error(str(err))

else:
    SECRET_KEY = secrets_settings.TOKEN_KEY

if secrets_settings.ADMIN_PASSWORD.startswith("/run/secrets/"):
    try:
        with open(secrets_settings.ADMIN_PASSWORD) as f:
            ADMIN_PASSWORD = f.read().rstrip("\n")
    except OSError as err:
        logging.error(str(err))

else:
    ADMIN_PASSWORD = secrets_settings.ADMIN_PASSWORD

# User database setup
DATABASE_URL = settings.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'users.sqlite')}"
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)
db = SessionLocal()

for scope in SCOPES:
    scope_entry = crud.get_scope_by_name(db, name=scope)
    if not scope_entry:
        add_scope = schemas.ScopeCreate(name=scope, description=SCOPES[scope])
        crud.create_user_scope(db, add_scope)

user = crud.get_user_by_username(db, username="admin")
if not user:
    user_in = schemas.UserCreate(
        username="admin",
        password=ADMIN_PASSWORD,
    )
    user = crud.create_user(db, user_in)
    crud.user_add_scopes(db, user, [scope for scope in crud.get_scopes(db)])

else:
    user_scopes = [user_scope.name for user_scope in user.scopes]
    for scope in SCOPES:
        if scope not in user_scopes:
            crud.user_append_scope(db, user, scope)
            logging.info(f"Scope '{scope}' added to admin.")

# Celery setup
celery = Celery(__name__)
celery.conf.broker_url = settings.BROKER_SERVER
celery.conf.result_backend = settings.REDIS_SERVER
celery.conf.accept_content = ["json", "application/json"]
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.task_track_started = True
celery.conf.broker_heartbeat = 0
celery.conf.result_persistent = True
celery.conf.task_acks_late = True
celery.conf.broker_pool_limit = None
# celery.conf.broker_use_ssl
# https://github.com/kaprien/repository-service-tuf-api/issues/91
