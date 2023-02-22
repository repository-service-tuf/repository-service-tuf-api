# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security, status

from repository_service_tuf_api import SCOPES_NAMES, targets
from repository_service_tuf_api.api.utils import authorize_user

router = APIRouter(
    prefix="/targets",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary=(
        "Add targets files to Metadata. "
        f"Scope: {SCOPES_NAMES.write_targets.value}"
    ),
    description="Add targets files to Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: targets.AddPayload,
    _user=Security(authorize_user, scopes=[SCOPES_NAMES.write_targets.value]),
):
    return targets.post(payload)


@router.delete(
    "/",
    summary=(
        "Remove targets files from Metadata. "
        f"Scope: {SCOPES_NAMES.delete_targets.value}"
    ),
    description="Remove targets files from Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def delete(
    payload: targets.DeletePayload,
    _user=Security(authorize_user, scopes=[SCOPES_NAMES.delete_targets.value]),
):
    return targets.delete(payload)


@router.post(
    "/publish/",
    summary=(
        "Submit a task to publish targets."
        f"Scope: {SCOPES_NAMES.write_targets.value}"
    ),
    description=(
        "Trigger a task to publish targets not yet published from the "
        "RSTUF Database"
    ),
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_publish_targets(
    _user=Security(authorize_user, scopes=[SCOPES_NAMES.write_targets.value]),
):
    return targets.post_publish_targets()
