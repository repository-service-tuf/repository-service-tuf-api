# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from repository_service_tuf_api.metadata import (
    get_task_id,
    is_bootstrap_done,
    repository_metadata,
)


class ResponseData(BaseModel):
    targets: Optional[List[str]]
    task_id: str
    last_update: datetime


class Response(BaseModel):
    """
    Targets Response
    """

    data: Optional[ResponseData]
    message: Optional[str]

    class Config:
        data_example = {
            "data": {
                "targets": ["file1.tar.gz", "file2.tar.gz"],
                "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                "last_update": "2022-12-01T12:10:00.578086",
            },
            "message": "New Target(s) successfully submitted.",
        }
        schema_extra = {"example": data_example}


class PayloadTargetsHashes(BaseModel):
    blake2b_256: str

    class Config:
        fields = {"blake2b_256": "blake2b-256"}


class TargetsInfo(BaseModel):
    length: int
    hashes: PayloadTargetsHashes
    custom: Optional[Dict[str, Any]]


class Targets(BaseModel):
    info: TargetsInfo
    path: str


class AddPayload(BaseModel):
    """
    POST method required Payload.
    """

    targets: List[Targets]
    add_task_id_to_custom: Optional[bool]

    class Config:
        with open("tests/data_examples/targets/payload.json") as f:
            content = f.read()
        payload = json.loads(content)
        schema_extra = {"example": payload}


class DeletePayload(BaseModel):
    """
    DELETE method required Payload.
    """

    targets: List[str]

    class Config:
        payload = {
            "targets": [
                "v3.4.1/file-3.4.1.tar.gz",
                "config-3.4.1.yaml",
                "file1.tar.gz",
            ]
        }
        schema_extra = {"example": payload}


def post(payload: AddPayload) -> Response:
    """
    Post new targets.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    if is_bootstrap_done() is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={"error": "System has not a Repository Metadata"},
        )

    task_id = get_task_id()
    if payload.add_task_id_to_custom is True:
        new_targets: List[Targets] = []
        for target in payload.targets:
            if target.info.custom:
                target.info.custom = {
                    "added_by_task_id": task_id,
                    **target.info.custom,
                }
            else:
                target.info.custom = {"added_by_task_id": task_id}

            new_targets.append(target)

        payload.targets = new_targets

    repository_metadata.apply_async(
        kwargs={
            "action": "add_targets",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    data = {
        "targets": [target.path for target in payload.targets],
        "task_id": task_id,
        "last_update": datetime.now(),
    }
    return Response(data=data, message="Target(s) successfully submitted.")


def delete(payload: DeletePayload) -> Response:
    """
    Delete new targets.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    if is_bootstrap_done() is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={"error": "System has not a Repository Metadata"},
        )

    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "remove_targets",
            "payload": payload.dict(by_alias=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    data = {
        "targets": payload.targets,
        "task_id": task_id,
        "last_update": datetime.now(),
    }
    return Response(
        data=data, message="Remove Target(s) successfully submitted."
    )


def post_publish_targets() -> Response:
    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "publish_targets",
            "payload": None,
        },
        task_id=task_id,
        queue="rstuf_internals",
        acks_late=True,
    )

    data = {
        "targets": None,
        "task_id": task_id,
        "last_update": datetime.now(),
    }

    return Response(
        data=data, message="Publish targets successfully submitted."
    )
