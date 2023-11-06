# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import targets

deprecation_warning = (
    " Deprecation Warning: this endpoint will removed in v1.0.0, "
    "use `/api/v1/artifacts`"
)

router = APIRouter(
    prefix="/artifacts",
    tags=["Artifacts"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Add artifacts to Metadata.",
    description="Add artifacts to Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(payload: targets.AddPayload):
    response = targets.post(payload)

    return response


@router.post(
    "/delete",
    summary="Remove artifacts from Metadata. ",
    description="Remove artifacts from Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_delete(payload: targets.DeletePayload):
    response = targets.delete(payload)

    return response


@router.post(
    "/publish/",
    summary="Submit a task to publish artifacts.",
    description=(
        "Trigger a task to publish artifacts not yet published from the "
        "RSTUF Database"
    ),
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_publish_targets():
    response = targets.post_publish_targets()

    return response
