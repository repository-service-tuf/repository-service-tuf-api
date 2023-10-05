# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
import logging
from typing import List

from fastapi import APIRouter, FastAPI

from repository_service_tuf_api import (
    is_auth_enabled,
    settings,
    settings_repository,
)
from repository_service_tuf_api.api.bootstrap import router as bootstrap_v1
from repository_service_tuf_api.api.config import router as config_v1
from repository_service_tuf_api.api.metadata import router as metadata_v1
from repository_service_tuf_api.api.targets import router as targets_v1
from repository_service_tuf_api.api.tasks import router as tasks_v1
from repository_service_tuf_api.api.token import router as token_v1

v1_endpoints = [
    bootstrap_v1,
    config_v1,
    metadata_v1,
    targets_v1,
    tasks_v1,
    token_v1,
]

rstuf_app = FastAPI(
    title="Repository Service for TUF API",
    description="Repository Service for TUF Rest API",
    docs_url="/",
)

api_v1 = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


def load_endpoints():
    # load endpoints
    disabled_endpoints: List[str] = settings.get(
        "DISABLE_ENDPOINTS", ""
    ).split(":")
    if is_auth_enabled is False:
        disabled_endpoints.append(f"{api_v1.prefix}{token_v1.prefix}/")

    for v1_endpoint in v1_endpoints:
        endpoint_routes = v1_endpoint.routes.copy()
        for endpoint_route in endpoint_routes:
            route = (
                f"{endpoint_route.methods}{api_v1.prefix}{endpoint_route.path}"
            )
            if route in disabled_endpoints:
                logging.info(f"Disabled endpoint {route}")
                v1_endpoint.routes.remove(endpoint_route)

        if f"{api_v1.prefix}{v1_endpoint.prefix}/" in disabled_endpoints:
            logging.info(
                f"Disabled endpoint {api_v1.prefix}{v1_endpoint.prefix}/"
            )
        else:
            api_v1.include_router(v1_endpoint)

    rstuf_app.include_router(api_v1)


load_endpoints()
logging.info(f"Bootstrap ID: {settings_repository.get_fresh('BOOTSTRAP')}")


def export_swagger_json(filepath):
    with open(filepath, "w") as f:
        swagger_json = json.dumps(rstuf_app.openapi(), indent=4)
        f.write(swagger_json)
