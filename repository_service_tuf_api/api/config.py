# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import config

router = APIRouter(
    prefix="/config",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.put(
    "/",
    summary="Update settings.",
    description=(
        "Submit an asynchronous task to update configuration settings. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=config.PutResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def put(payload: config.PutPayload):
    return config.put(payload)


@router.get(
    "/",
    summary="List settings.",
    description="Returns the configuration settings",
    response_model=config.Response,
    response_model_exclude_none=True,
)
def get():
    return config.get()
