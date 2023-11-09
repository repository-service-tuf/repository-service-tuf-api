# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import bootstrap

router = APIRouter(
    prefix="/bootstrap",
    tags=["Bootstrap"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary="Check the bootstrap status.",
    description=("Check if the bootstrap of the system is done or not."),
    response_model=bootstrap.BootstrapGetResponse,
    response_model_exclude_none=True,
)
def get():
    return bootstrap.get_bootstrap()


@router.post(
    "/",
    summary="Post a task to bootstrap the system with initial signed "
    "Metadata.",
    description=(
        "Submit an asynchronous task to initialize the TUF Repository with "
        "initial signed Metadata and Settings. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=bootstrap.BootstrapPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: bootstrap.BootstrapPayload,
):
    return bootstrap.post_bootstrap(payload)
