import importlib
import os

from celery import Celery
from dynaconf import Dynaconf

from kaprien_api import services  # noqa
from kaprien_api.tuf import MetadataRepository
from kaprien_api.tuf.interfaces import IKeyVault, IStorage

SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.ini")
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

storage_backends = [
    storage.__name__.upper() for storage in IStorage.__subclasses__()
]

if settings.STORAGE_BACKEND.upper() not in storage_backends:
    raise ValueError(
        f"Invalid Storage Backend {settings.STORAGE_BACKEND}. Supported "
        f"Storage Backends {', '.join(storage_backends)}"
    )
else:
    settings.STORAGE_BACKEND = getattr(
        importlib.import_module("kaprien_api.services"),
        settings.STORAGE_BACKEND,
    )

    if missing := [
        s.name
        for s in settings.STORAGE_BACKEND.settings()
        if s.required and s.name not in settings
    ]:
        raise AttributeError(
            f"'Settings' object has not attribute(s) {', '.join(missing)}"
        )

    settings.STORAGE_BACKEND.configure(settings)
    storage_kwargs = {
        s.argument: settings.store[s.name]
        for s in settings.STORAGE_BACKEND.settings()
    }

keyvault_backends = [
    keyvault.__name__.upper() for keyvault in IKeyVault.__subclasses__()
]
if settings.KEYVAULT_BACKEND.upper() not in keyvault_backends:
    raise ValueError(
        f"Invalid Key Vault Backend {settings.KEYVAULT_BACKEND}. Supported "
        f"Key Vault Backends: {', '.join(keyvault_backends)}"
    )
else:
    settings.KEYVAULT_BACKEND = getattr(
        importlib.import_module("kaprien_api.services"),
        settings.KEYVAULT_BACKEND,
    )

    if missing := [
        s.name
        for s in settings.KEYVAULT_BACKEND.settings()
        if s.required and s.name not in settings
    ]:
        raise AttributeError(
            f"'Settings' object has not attribute(s) {', '.join(missing)}"
        )

    settings.KEYVAULT_BACKEND.configure(settings)
    keyvault_kwargs = {
        s.argument: settings.store[s.name]
        for s in settings.KEYVAULT_BACKEND.settings()
    }


storage = settings.STORAGE_BACKEND(**storage_kwargs)
keyvault = settings.KEYVAULT_BACKEND(**keyvault_kwargs)

tuf_repository = MetadataRepository(
    storage_backend=storage, key_backend=keyvault, settings=settings
)

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


@celery.task(name="app.metadata_repository")
def repository_metadata(action, settings, payload):
    return True
