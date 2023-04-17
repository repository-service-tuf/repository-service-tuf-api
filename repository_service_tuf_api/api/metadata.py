# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security, status

from repository_service_tuf_api import SCOPES_NAMES, metadata
from repository_service_tuf_api.api import get_auth

router = APIRouter(
    prefix="/metadata",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

auth = get_auth()


@router.post(
    "/",
    summary=(
        f"Rotate role metadata. Scope: {SCOPES_NAMES.write_metadata.value}"
    ),
    description=("Rotate a role metadata which requires offline signing."),
    response_model=metadata.MetadataPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: metadata.MetadataPostPayload,
    _user=Security(auth, scopes=[SCOPES_NAMES.write_metadata.value]),
):
    return metadata.post_metadata(payload)
