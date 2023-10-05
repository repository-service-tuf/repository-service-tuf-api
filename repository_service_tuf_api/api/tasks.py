# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Depends

from repository_service_tuf_api import tasks

router = APIRouter(
    prefix="/task",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary="Get task state.",
    description=(
        "Get Repository Metadata task state. "
        "The state is according with Celery tasks: "
        "`PENDING` the task still not processed or unknown/inexistent task. "
        "`RECEIVED` task is reveived by the broker server. "
        "`PRE_RUN` the task will start by repository-service-tuf-worker. "
        "`RUNNING` the task is in execution. "
        "`FAILURE` the task failed to executed. "
        "`SUCCESS` the task execution is finished. "
    ),
    response_model=tasks.Response,
    response_model_exclude_none=True,
)
def get(params: tasks.GetParameters = Depends()):
    return tasks.get(params.task_id)
