import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from tuf_repository_service_api.metadata import (
    get_task_id,
    is_bootstrap_done,
    repository_metadata,
)


class ResponseData(BaseModel):
    targets: List[str]
    task_id: str


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
    repository_metadata.apply_async(
        kwargs={
            "action": "add_targets",
            "payload": payload.dict(by_alias=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    data = {
        "targets": [target.path for target in payload.targets],
        "task_id": task_id,
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
    }
    return Response(
        data=data, message="Remove Target(s) successfully submitted."
    )
