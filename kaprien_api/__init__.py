import logging
import os
from enum import Enum

from celery import Celery
from dynaconf import Dynaconf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kaprien_api.users import crud, schemas
from kaprien_api.users.models import Base


class SCOPES_NAMES(Enum):
    read_bootstrap = "read:bootstrap"
    read_settings = "read:settings"
    read_targets = "read:targets"
    read_token = "read:token"
    write_bootstrap = "write:bootstrap"
    write_targets = "write:targets"
    write_token = "write:token"


SCOPES = {
    SCOPES_NAMES.read_targets.value: "Read (GET) targets",
    SCOPES_NAMES.read_bootstrap.value: "Read (GET) bootstrap",
    SCOPES_NAMES.read_settings.value: "Read (GET) settings",
    SCOPES_NAMES.read_token.value: "Read (GET) tokens",
    SCOPES_NAMES.write_targets.value: "Write (POST) targets",
    SCOPES_NAMES.write_token.value: "Write (POST) token",
    SCOPES_NAMES.write_bootstrap.value: "Write (POST) bootstrap",
}

DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.ini")
REPOSITORY_SETTINGS_FILE = os.path.join(DATA_DIR, "repository_settings.ini")

settings = Dynaconf(
    envvar_prefix="KAPRIEN",
    settings_files=[SETTINGS_FILE],
    environments=True,
)
settings_repository = Dynaconf(
    settings_files=[REPOSITORY_SETTINGS_FILE],
    environments=True,
)
secrets_settings = Dynaconf(
    envvar_prefix="SECRETS_KAPRIEN",
    environments=True,
)

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

# User database
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

celery = Celery(__name__)
celery.conf.broker_url = f"amqp://{settings.RABBITMQ_SERVER}"
celery.conf.result_backend = "redis://redis"
celery.conf.accept_content = ["json", "application/json"]
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.task_track_started = True
celery.conf.broker_heartbeat = 0
celery.conf.result_persistent = True
celery.conf.task_acks_late = True
celery.conf.broker_pool_limit = None
# celery.conf.broker_use_ssl = True


@celery.task(name="app.kaprien_repo_worker")
def repository_metadata(action, settings, payload):
    logging.debug(f"New tasks action submitted {action}")
    return True
