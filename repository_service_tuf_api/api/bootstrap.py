# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security, status

from repository_service_tuf_api import SCOPES_NAMES, bootstrap
from repository_service_tuf_api.api import get_auth

router = APIRouter(
    prefix="/bootstrap",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

auth = get_auth()


@router.get(
    "/",
    summary=(
        "Check the bootstrap status. "
        f"Scope: {SCOPES_NAMES.read_bootstrap.value}"
    ),
    description=("Check if the bootstrap of the system is done or not."),
    response_model=bootstrap.BootstrapGetResponse,
    response_model_exclude_none=True,
)
def get(_user=Security(auth, scopes=[SCOPES_NAMES.read_bootstrap.value])):
    return bootstrap.get_bootstrap()


@router.post(
    "/",
    summary=(
        "Bootstrap the system with initial signed Metadata. "
        f"Scope: {SCOPES_NAMES.write_bootstrap.value}"
    ),
    description=(
        "Initialize the TUF Repository with initial signed Metadata and "
        "Settings."
    ),
    response_model=bootstrap.BootstrapPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: bootstrap.BootstrapPayload,
    _user=Security(auth, scopes=[SCOPES_NAMES.write_bootstrap.value]),
):
    return bootstrap.post_bootstrap(payload)
