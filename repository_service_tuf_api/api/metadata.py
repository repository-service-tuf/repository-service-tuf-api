# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import metadata

router = APIRouter(
    prefix="/metadata",
    tags=["Metadata"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Rotate role metadata.",
    description="Rotate a role metadata that requires offline signing.",
    response_model=metadata.MetadataPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(payload: metadata.MetadataPostPayload):
    return metadata.post_metadata(payload)


@router.get(
    "/sign",
    summary="Get all metadata roles pending signatures.",
    description=(
        "Get all metadata roles that need more signatures before they can be "
        "used."
    ),
    response_model=metadata.MetadataSignGetResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def get_sign():
    return metadata.get_metadata_sign()


@router.post(
    "/sign",
    summary="Add a signature for a metadata role.",
    description="Add a signature for a metadata role.",
    response_model=metadata.MetadataPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_sign(payload: metadata.MetadataSignPostPayload):
    return metadata.post_metadata_sign(payload)


@router.post(
    "/sign/delete",
    summary="Delete role metadata in signing process.",
    description="Delete role metadata in signing process",
    response_model=metadata.MetadataSignDeleteResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_delete_sign(payload: metadata.MetadataSignDeletePayload):
    return metadata.delete_metadata_sign(payload)
