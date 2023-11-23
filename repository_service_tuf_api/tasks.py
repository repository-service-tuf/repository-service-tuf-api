# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import enum
from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from repository_service_tuf_api import repository_metadata


class TaskState(str, enum.Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"
    RETRY = "RETRY"
    IGNORED = "IGNORED"


class TaskName(str, enum.Enum):
    ADD_TARGETS = "add_targets"
    REMOVE_TARGETS = "remove_targets"
    BOOTSTRAP = "bootstrap"
    UPDATE_SETTINGS = "update_settings"
    PUBLISH_TARGETS = "publish_targets"
    METADATA_UPDATE = "metadata_update"
    SIGN_METADATA = "sign_metadata"
    DELETE_SIGN_METADATA = "delete_sign_metadata"


class GetParameters(BaseModel):
    task_id: str


class TaskDetails(BaseModel):
    message: str = Field(description="Result detail description")
    error: Optional[str] = Field(
        description=(
            "If the task status result is `False` shows an error message"
        )
    )
    any: Any = Field(description="Any releavant information from task")


class TaskResult(BaseModel):
    status: bool = Field(
        description="Task result status. `True` Success | `False` Failure"
    )
    task: TaskName = Field(description="Task name by worker")
    last_update: datetime = Field(description="Last time task was updated")
    details: TaskDetails = Field(description="Relevant result details")


class TasksData(BaseModel):
    task_id: str = Field(description="Task ID")
    state: TaskState = Field(
        description=(
            "The Celery task state. Note: It isn't the task result status.\n\n"
            "`PENDING`: Task state is unknown (assumed pending since you know "
            "the id).\n\n"
            "`RECEIVED`: Task received by a worker (only used in events).\n\n"
            "`STARTED`: Task started by a worker.\n\n"
            "`RUNNING`: Task is running.\n\n"
            "`SUCCESS`: Task succeeded.\n\n"
            "`FAILURE`: Task failed.\n\n"
            "`REVOKED`: Task revoked.\n\n"
            "`REJECTED`: Task was rejected (only used in events).\n\n"
        )
    )
    result: Optional[Union[Any, TaskResult]] = Field(
        description=(
            "Task result details (state `SUCCESS` uses schema `TaskResult)"
        )
    )


class Response(BaseModel):
    data: TasksData
    message: Optional[str]

    class Config:
        data_example = {
            "data": {
                "task_id": "33e66671dcc84cdfa2535a1eb030104c",
                "state": TaskState.SUCCESS,
                "result": {
                    "status": True,
                    "task": TaskName.ADD_TARGETS,
                    "last_update": "2023-11-17T09:54:15.762882",
                    "details": {"message": "Target(s) Added"},
                },
            },
            "message": "Task state.",
        }

        schema_extra = {"example": data_example}


def get(task_id: str) -> Response:
    """
    Get the task details from Result Backend Server.

    Uses the Celery implementation in
    ``repository_service_tuf_api.metadata.metadata_repository.AsyncResult`` to
    fetch from Result Backend the task state.

    Args:
        task_id: Task ID

    Returns:
        ``Response`` as BaseModel from pydantic
    """
    task = repository_metadata.AsyncResult(task_id)
    if isinstance(task.result, Exception):
        task_result = str(task.result)
    else:
        task_result = task.result

    return Response(
        data=TasksData(task_id=task_id, state=task.state, result=task_result),
        message="Task state.",
    )
