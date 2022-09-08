from typing import Any, Optional

from fastapi import Query
from pydantic import BaseModel, Field

from kaprien_api.metadata import repository_metadata


class GetParameters:
    def __init__(
        self,
        task_id: str = Query(description="Task id", required=True),
    ):
        self.task_id = task_id


class TasksData(BaseModel):
    task_id: str = Field(description="Task ID")
    status: str = Field(
        description="Status according with Celery Tasks",
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
                "tasks": [
                    {
                        "task_id": "91353735ef7d48099df86d8bfa30316e",
                        "status": "SUCCESS",
                        "result": True,
                    }
                ],
                "message": "Task details. ",
            }
        }
        schema_extra = {"example": data_example}


def get(task_id: str) -> Response:
    """
    Get the task details from Result Backend Server.

    Uses the Celery implementation in
    ``kaprien_api.metadata.metadata_repository.AsyncResult`` to fetch from
    Result Backend the task status.

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
        data=TasksData(
            task_id=task_id, status=task.status, result=task_result
        ),
        message="Task status.",
    )
