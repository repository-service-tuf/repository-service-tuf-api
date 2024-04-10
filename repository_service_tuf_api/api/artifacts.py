# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import artifacts

router = APIRouter(
    prefix="/artifacts",
    tags=["Artifacts"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Post a task to add artifacts to Metadata.",
    description=(
        "Submit an asynchronous task to add artifacts to Metadata. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=artifacts.ResponsePostAdd,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(payload: artifacts.AddPayload) -> artifacts.ResponsePostAdd:
    response = artifacts.post(payload)

    return response


@router.post(
    "/delete",
    summary="Post a task to remove artifacts from Metadata.",
    description=(
        "Submit an asynchronous task to remove artifacts from "
        "Metadata. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=artifacts.ResponsePostDelete,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_delete(
    payload: artifacts.DeletePayload,
) -> artifacts.ResponsePostDelete:
    response = artifacts.delete(payload)

    return response


@router.post(
    "/publish/",
    summary="Post a task to publish artifacts.",
    description=(
        "Submit an asynchronous task to publish artifacts not yet published "
        "from the RSTUF Database. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=artifacts.ResponsePostPublish,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_publish_artifacts() -> artifacts.ResponsePostPublish:
    response = artifacts.post_publish_artifacts()

    return response
