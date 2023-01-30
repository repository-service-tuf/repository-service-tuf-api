# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security, status

from repository_service_tuf_api import SCOPES_NAMES, targets
from repository_service_tuf_api.token import validate_token

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
    _user=Security(validate_token, scopes=[SCOPES_NAMES.write_targets.value]),
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
    _user=Security(validate_token, scopes=[SCOPES_NAMES.delete_targets.value]),
):
    return targets.delete(payload)
