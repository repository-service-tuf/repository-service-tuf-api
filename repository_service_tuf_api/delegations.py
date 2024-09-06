# SPDX-FileCopyrightText: 2024 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
)
from repository_service_tuf_api.common_models import TUFDelegations

with open("tests/data_examples/metadata/delegation-payload.json") as f:
    content = f.read()
delegation_payload_example = json.loads(content)


class ResponseData(BaseModel):
    task_id: str | None = None
    last_update: datetime


class DelegationsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                }
            }
        }
    )
    data: ResponseData | None = None
    message: str


#
# Metadata Delegation
#
class DelegationRolesData(BaseModel):
    # TODO: add parameters for delegation roles, for example 'purge',
    # 'force'  during removing or managing delegation roles
    name: str


class DelegationsData(BaseModel):
    roles: List[DelegationRolesData]


class MetadataDelegationsPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": delegation_payload_example}
    )

    delegations: TUFDelegations


# Metadata Delegation (Delete)
class MetadataDelegationDeletePayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "delegations": {"roles": [{"name": "dev"}, {"name": "legacy"}]}
            }
        }
    )

    delegations: DelegationsData


def metadata_delegation(
    payload: MetadataDelegationsPayload | MetadataDelegationDeletePayload,
    action: str,
):
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"Requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()
    worker_payload = payload.model_dump(by_alias=True, exclude_none=True)
    worker_payload["action"] = action

    repository_metadata.apply_async(
        kwargs={
            "action": "metadata_delegation",
            "payload": worker_payload,
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = f"Metadata delegation {action} accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return DelegationsResponse(data=data, message=message)
