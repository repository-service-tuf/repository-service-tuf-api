# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
)


class ResponseData(BaseModel):
    artifacts: List[str]
    task_id: str
    last_update: datetime


class ResponsePostAdd(BaseModel):
    """
    Artifacts post new artifacts response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "artifacts": ["file1.tar.gz", "file2.tar.gz"],
                    "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "New Artifact(s) successfully submitted.",
            }
        }
    )

    data: ResponseData | None = None
    message: str | None = None


class ResponsePostDelete(BaseModel):
    """
    Artifacts post remove artifacts response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "artifacts": ["file1.tar.gz", "file2.tar.gz"],
                    "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Remove Artifact(s) successfully submitted.",
            }
        }
    )

    data: ResponseData | None = None
    message: str | None = None


class ResponsePostPublish(BaseModel):
    """
    Artifacts post publish artifacts response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "artifacts": [],
                    "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Publish artifacts successfully submitted.",
            }
        }
    )

    data: ResponseData | None = None
    message: str | None = None


class ArtifactInfo(BaseModel):
    length: int
    hashes: Dict[str, str] = Field(
        description=(
            "The key(s) must be compatible with the algorithm(s) supported by "
            "a TUF client"
        )
    )
    custom: Dict[str, Any] | None = None


class Artifact(BaseModel):
    info: ArtifactInfo
    path: str


with open("tests/data_examples/artifacts/add_payload.json") as f:
    content = f.read()
add_payload = json.loads(content)


class AddPayload(BaseModel):
    """
    POST method required Payload.
    """

    model_config = ConfigDict(json_schema_extra={"example": add_payload})
    artifacts: List[Artifact]
    add_task_id_to_custom: bool = Field(
        default=False,
        description="Whether to add the id of the task in custom",
    )
    publish_artifacts: bool = Field(
        default=True, description="Whether to publish the artifacts"
    )


class DeletePayload(BaseModel):
    """
    DELETE method required Payload.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "artifacts": [
                    "v3.4.1/file-3.4.1.tar.gz",
                    "config-3.4.1.yaml",
                    "file1.tar.gz",
                ]
            }
        }
    )
    artifacts: List[str]
    publish_artifacts: bool = Field(
        default=True, description="Whether to publish the artifacts changes"
    )


def post(payload: AddPayload) -> ResponsePostAdd:
    """
    Post new artifact(s)s.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"It requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()
    if payload.add_task_id_to_custom is True:
        new_artifacts: List[Artifact] = []
        for artifact in payload.artifacts:
            if artifact.info.custom:
                artifact.info.custom = {
                    "added_by_task_id": task_id,
                    **artifact.info.custom,
                }
            else:
                artifact.info.custom = {"added_by_task_id": task_id}

            new_artifacts.append(artifact)

        payload.artifacts = new_artifacts

    repository_metadata.apply_async(
        kwargs={
            "action": "add_artifacts",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "New Artifact(s) successfully submitted."
    if payload.publish_artifacts is False:
        message += " Publishing will be skipped."

    data = {
        "artifacts": [artifact.path for artifact in payload.artifacts],
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }
    return ResponsePostAdd(data=data, message=message)


def delete(payload: DeletePayload) -> ResponsePostDelete:
    """
    Delete new artifacts.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
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
            "action": "remove_artifacts",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    data = {
        "artifacts": payload.artifacts,
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    message = "Remove Artifact(s) successfully submitted."
    if payload.publish_artifacts is False:
        message += " Publishing will be skipped."
    return ResponsePostDelete(data=data, message=message)


def post_publish_artifacts() -> ResponsePostPublish:
    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "publish_artifacts",
            "payload": None,
        },
        task_id=task_id,
        queue="rstuf_internals",
        acks_late=True,
    )

    data = {
        "artifacts": [],
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return ResponsePostPublish(
        data=data, message="Publish artifacts successfully submitted."
    )
