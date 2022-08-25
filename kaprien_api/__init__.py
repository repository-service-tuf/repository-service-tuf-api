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

SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.ini")
SECRET_SETTINGS_FILE = os.getenv("SECRET_SETTINGS_FILE", ".secrets.ini")

settings = Dynaconf(
    envvar_prefix="KAPRIEN",
    settings_files=[SETTINGS_FILE],
    environments=True,
)
simple_settings = Dynaconf(
    envvar_prefix="KAPRIEN",
    settings_files=[SETTINGS_FILE],
    environments=True,
)
secrets_settings = Dynaconf(
    envvar_prefix="SECRETS_KAPRIEN",
    settings_files=[SECRET_SETTINGS_FILE],
    environments=True,
)

# Tokens
SECRET_KEY = secrets_settings.TOKEN_KEY

# User database
DATABASE_URL = (
    f"sqlite:///{settings.get('DATABASE_DATA', './database/users.sqlite')}"
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
        password=secrets_settings.ADMIN_PASSWORD,
    )
    user = crud.create_user(db, user_in)
    crud.user_add_scopes(db, user, [scope for scope in crud.get_scopes(db)])

# # Services
# storage_backends = [
#     storage.__name__.upper() for storage in IStorage.__subclasses__()
# ]

# if settings.STORAGE_BACKEND.upper() not in storage_backends:
#     raise ValueError(
#         f"Invalid Storage Backend {settings.STORAGE_BACKEND}. Supported "
#         f"Storage Backends {', '.join(storage_backends)}"
#     )
# else:
#     settings.STORAGE_BACKEND = getattr(
#         importlib.import_module("kaprien_api.tuf.services"),
#         settings.STORAGE_BACKEND,
#     )

#     if missing := [
#         s.name
#         for s in settings.STORAGE_BACKEND.settings()
#         if s.required and s.name not in settings
#     ]:
#         raise AttributeError(
#             f"'Settings' object has not attribute(s) {', '.join(missing)}"
#         )

#     settings.STORAGE_BACKEND.configure(settings)
#     storage_kwargs = {
#         s.argument: settings.store[s.name]
#         for s in settings.STORAGE_BACKEND.settings()
#     }

# keyvault_backends = [
#     keyvault.__name__.upper() for keyvault in IKeyVault.__subclasses__()
# ]
# if settings.KEYVAULT_BACKEND.upper() not in keyvault_backends:
#     raise ValueError(
#         f"Invalid Key Vault Backend {settings.KEYVAULT_BACKEND}. Supported "
#         f"Key Vault Backends: {', '.join(keyvault_backends)}"
#     )
# else:
#     settings.KEYVAULT_BACKEND = getattr(
#         importlib.import_module("kaprien_api.tuf.services"),
#         settings.KEYVAULT_BACKEND,
#     )

#     if missing := [
#         s.name
#         for s in settings.KEYVAULT_BACKEND.settings()
#         if s.required and s.name not in settings
#     ]:
#         raise AttributeError(
#             f"'Settings' object has not attribute(s) {', '.join(missing)}"
#         )

#     settings.KEYVAULT_BACKEND.configure(settings)
#     keyvault_kwargs = {
#         s.argument: settings.store[s.name]
#         for s in settings.KEYVAULT_BACKEND.settings()
#     }


# storage = settings.STORAGE_BACKEND(**storage_kwargs)
# keyvault = settings.KEYVAULT_BACKEND(**keyvault_kwargs)


celery = Celery(__name__)
celery.conf.broker_url = f"amqp://{settings.RABBITMQ_SERVER}"
celery.conf.result_backend = "rpc://"
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
    return True
