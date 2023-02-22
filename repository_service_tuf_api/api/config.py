# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security

from repository_service_tuf_api import SCOPES_NAMES, config
from repository_service_tuf_api.api.utils import authorize_user

router = APIRouter(
    prefix="/config",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary=("List settings. " f"Scope: {SCOPES_NAMES.read_settings.value}"),
    description="Returns the configuration settings",
    response_model=config.Response,
    response_model_exclude_none=True,
)
def get(
    _user=Security(authorize_user, scopes=[SCOPES_NAMES.read_settings.value])
):
    return config.get()
