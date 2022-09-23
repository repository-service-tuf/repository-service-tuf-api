import json
import logging

from fastapi import APIRouter, FastAPI

from kaprien_api import settings, settings_repository
from kaprien_api.api.bootstrap import router as bootstrap_v1
from kaprien_api.api.config import router as config_v1
from kaprien_api.api.targets import router as targets_v1
from kaprien_api.api.tasks import router as tasks_v1
from kaprien_api.api.token import router as token_v1

kaprien_app = FastAPI(
    title="Kaprien Rest API",
    description="Kaprien Rest API service for Kaprien Server",
    docs_url="/",
)

api_v1 = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

if settings.get("BOOTSTRAP_NODE", False) is True:
    api_v1.include_router(bootstrap_v1)
logging.info(f"Bootstrap on this node enabled: {settings.BOOTSTRAP_NODE}")
logging.info(f"Bootstrap ID: {settings_repository.get_fresh('BOOTSTRAP')}")

api_v1.include_router(config_v1)
api_v1.include_router(targets_v1)
api_v1.include_router(token_v1)
api_v1.include_router(tasks_v1)

kaprien_app.include_router(api_v1)


def export_swagger_json(filepath):
    with open(filepath, "w") as f:
        swagger_json = json.dumps(kaprien_app.openapi(), indent=4)
        f.write(swagger_json)
