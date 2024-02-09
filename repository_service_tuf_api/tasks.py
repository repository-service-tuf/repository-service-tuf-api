# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from celery import states
from pydantic import BaseModel, Field

from repository_service_tuf_api import repository_metadata


class TaskState(str, enum.Enum):
    PENDING = states.PENDING
    RECEIVED = states.RECEIVED
    STARTED = states.STARTED
    SUCCESS = states.SUCCESS
    FAILURE = states.FAILURE
    REVOKED = states.REVOKED
    REJECTED = states.REJECTED
    RETRY = states.RETRY
    IGNORED = states.IGNORED
    ERRORED = "ERRORED"
    RUNNING = "RUNNING"  # custom state used when a task is RUNNING in RSTUF


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


class TaskResult(BaseModel):
    message: Optional[str] = Field(description="Result detail description")
    error: Optional[str] = Field(description="Error message")
    status: Optional[bool] = Field(
        description="Task result status. `True` Success | `False` Failure",
    )
    task: Optional[TaskName] = Field(description="Task name by worker")
    last_update: Optional[datetime] = Field(
        description="Last time task was updated"
    )
    details: Optional[Dict[str, Any]] = Field(
        description="Relevant result details"
    )


class TasksData(BaseModel):
    task_id: str = Field(description="Task ID")
    state: TaskState = Field(
        description=(
            "The Celery task state.\n\n"
            "`PENDING`: Task state is unknown (assumed pending since you know "
            "the id).\n\n"
            "`RECEIVED`: Task received by a RSTUF Worker (only used in "
            "events).\n\n"
            "`SUCCESS`: Task succeeded.\n\n"
            "`STARTED`: Task started by a RSTUF Worker.\n\n"
            "`RUNNING`: Task is running on RSTUF Worker.\n\n"
            "`FAILURE`: Task failed (unexpected).\n\n"
            "`REVOKED`: Task revoked.\n\n"
            "`RETRY`: Task is waiting for retry.\n\n"
            "`ERRORED`: Task errored. RSTUF identified an error while "
            "processing the task.\n\n"
            "`REJECTED`: Task was rejected (only used in events).\n\n"
            "`IGNORED`: Task was ignored."
        )
    )
    result: Optional[TaskResult] = Field(
        description=("Task result if available.")
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
                    "task": TaskName.ADD_TARGETS,
                    "last_update": "2023-11-17T09:54:15.762882",
                    "message": "Target(s) Added",
                    "details": {
                        "targets": ["file1.tar.gz"],
                        "target_roles": ["bins-3"],
                    },
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

    task_state = task.state
    task_result = task.result

    # Celery FAILURE task, we include the task result (exception) as an error
    # and default message as critical failure executing the task.
    if isinstance(task.result, Exception):
        task_result = {
            "message": str(task.result),
        }

    # If the task state is SUCCESS and the task result is False we considere
    # it an errored task.
    if task_state == TaskState.SUCCESS and not task_result.get(
        "status", False
    ):
        task_state = TaskState.ERRORED

    return Response(
        data=TasksData(task_id=task_id, state=task_state, result=task_result),
        message="Task state.",
    )
