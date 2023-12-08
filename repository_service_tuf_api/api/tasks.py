# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Depends

from repository_service_tuf_api import tasks

router = APIRouter(
    prefix="/task",
    tags=["Task"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary="Get task state.",
    description="Get RSTUF tasks information.",
    response_model=tasks.Response,
    response_model_exclude_none=True,
)
def get(params: tasks.GetParameters = Depends()):
    return tasks.get(params.task_id)
