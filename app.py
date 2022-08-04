import json

from fastapi import APIRouter, FastAPI

from kaprien_api.api.bootstrap import router as bootstrap_v1
from kaprien_api.api.metadata import router as metadata_v1
from kaprien_api.api.repository_settings import router as settings_v1
from kaprien_api.api.targets import router as targets_v1

kaprien_app = FastAPI(
    docs_url="/",
)

api_v1 = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

api_v1.include_router(bootstrap_v1)
api_v1.include_router(metadata_v1)
api_v1.include_router(settings_v1)
api_v1.include_router(targets_v1)

kaprien_app.include_router(api_v1)


def export_swagger_json(filepath):
    with open(filepath, "w") as f:
        swagger_json = json.dumps(kaprien_app.openapi(), indent=4)
        f.write(swagger_json)
