# SPDX-FileCopyrightText: 2024 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import delegations

router = APIRouter(
    prefix="/delegations",
    tags=["Delegations"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Post a task to create a new delegation.",
    description=(
        "Submit an asynchronous task to create a new delegation. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=delegations.DelegationsResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_delegation(payload: delegations.MetadataDelegationsPayload):
    return delegations.metadata_delegation(payload, action="add")


@router.put(
    "/",
    summary="Put a task to update delegation(s).",
    description=(
        "Submit an asynchronous task to update delegation(s). "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=delegations.DelegationsResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def put_delegation(payload: delegations.MetadataDelegationsPayload):
    return delegations.metadata_delegation(payload, action="update")


@router.post(
    "/delete",
    summary="Post a task to create a delete delegation.",
    description=(
        "Submit an asynchronous task to delete delegation. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=delegations.DelegationsResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def delete_delegation(payload: delegations.MetadataDelegationDeletePayload):
    return delegations.metadata_delegation(payload, action="delete")
