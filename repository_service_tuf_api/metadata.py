# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
)
from repository_service_tuf_api.common_models import Roles, TUFMetadata


class MetadataPostPayload(BaseModel):
    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]

    class Config:
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class PostData(BaseModel):
    task_id: Optional[str]


class MetadataPostResponse(BaseModel):
    data: Optional[PostData]
    message: str

    class Config:
        example = {
            "data": {
                "task_id": "7a634b556f784ae88785d36425f9a218",
            },
            "message": "Bootstrap accepted.",
        }

        schema_extra = {"example": example}


def post_metadata(payload: MetadataPostPayload) -> MetadataPostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"It requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "metadata_rotation",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    return MetadataPostResponse(
        data={"task_id": task_id}, message="Metadata update accepted."
    )
