# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import enum
from datetime import datetime
from typing import Any, Dict

from celery import states
from pydantic import BaseModel, ConfigDict, Field

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
    # custom state used when a task is started before celery task is started
    PRE_RUN = "PRE_RUN"
    RUNNING = "RUNNING"  # custom state used when a task is RUNNING in RSTUF


class TaskName(str, enum.Enum):
    ADD_ARTIFACTS = "add_artifacts"
    REMOVE_ARTIFACTS = "remove_artifacts"
    BOOTSTRAP = "bootstrap"
    UPDATE_SETTINGS = "update_settings"
    PUBLISH_ARTIFACTS = "publish_artifacts"
    METADATA_UPDATE = "metadata_update"
    METADATA_DELEGATION = "metadata_delegation"
    SIGN_METADATA = "sign_metadata"
    DELETE_SIGN_METADATA = "delete_sign_metadata"


class GetParameters(BaseModel):
    task_id: str


class TaskResult(BaseModel):
    message: str | None = Field(
        description="Result detail description", default=None
    )
    error: str | None = Field(description="Error message", default=None)
    status: None | bool = Field(
        description="Task result status. `True` Success | `False` Failure",
        default=None,
    )
    task: TaskName | None = Field(
        description="Task name by worker", default=None
    )
    last_update: datetime | None = Field(
        description="Last time task was updated", default=None
    )
    details: Dict[str, Any] | None = Field(
        description="Relevant result details",
        default=None,
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
    result: TaskResult | None = Field(
        description=("Task result if available."),
        default=None,
    )


class Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "33e66671dcc84cdfa2535a1eb030104c",
                    "state": TaskState.SUCCESS,
                    "result": {
                        "task": TaskName.ADD_ARTIFACTS,
                        "status": True,
                        "last_update": "2023-11-17T09:54:15.762882",
                        "message": "Artifact(s) Added",
                        "details": {
                            "added_artifacts": ["file1.tar.gz"],
                            "invalid_paths": ["invalid_file.tar.gz"],
                            "target_roles": ["bins-3"],
                        },
                    },
                },
                "message": "Task state.",
            }
        }
    )
    data: TasksData
    message: str | None = None


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

    # If the task state is SUCCESS and the task.result.status is False we
    # considere it an errored task.
    if task_state == TaskState.SUCCESS and not task_result.get(
        "status", False
    ):
        task_state = TaskState.ERRORED

    return Response(
        data=TasksData(task_id=task_id, state=task_state, result=task_result),
        message="Task state.",
    )
