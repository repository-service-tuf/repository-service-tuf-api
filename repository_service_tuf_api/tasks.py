# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

from pydantic import BaseModel, Field

from repository_service_tuf_api import repository_metadata


class GetParameters(BaseModel):
    task_id: str


class TasksData(BaseModel):
    task_id: str = Field(description="Task ID")
    state: str = Field(
        description="State according with Celery Tasks",
    )
    result: Optional[Any] = Field(
        description="Details about the task execution.",
    )


class Response(BaseModel):
    data: TasksData
    message: Optional[str]

    class Config:
        data_example = {
            "data": {
                "task_id": "91353735ef7d48099df86d8bfa30316e",
                "state": "SUCCESS",
                "result": {
                    "status": "Task finished.",
                    "details": {"key": "value"},
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
